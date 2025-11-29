import boto3
import logging
from botocore.exceptions import ClientError
from botocore.config import Config
from backend.config import settings
from typing import Optional, BinaryIO
import mimetypes
from datetime import datetime
import io

class R2Storage:
    def __init__(self):
        self.logger = logging.getLogger("r2")
        self.client = None
        self.bucket = settings.CLOUDFLARE_R2_BUCKET_NAME
        self.available = False
        if self._is_configured():
            self._init_client()
            self._ensure_bucket_exists()

    def _is_configured(self) -> bool:
        return settings.use_cloudflare_r2

    def _init_client(self):
        if self.client is None:
            self.client = boto3.client(
                service_name="s3",
                endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT_URL,
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
                region_name="auto",
                config=Config(
                    signature_version="s3v4",
                    s3={'addressing_style': 'path'}
                )
            )
    
    def _ensure_bucket_exists(self):
        if not self._is_configured():
            self.logger.warning("r2_skip reason=not_configured")
            self.available = False
            return
        try:
            self.client.head_bucket(Bucket=self.bucket)
            self.available = True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    self.available = True
                except Exception:
                    self.available = False
                    self.logger.error("r2_create_bucket_failed")
            else:
                self.available = False
                self.logger.error("r2_disabled")

    def _is_available(self) -> bool:
        return self._is_configured() and self.available
    
    def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        folder: str = "files",
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload file to R2 and return public URL
        
        Args:
            file_content: File bytes
            filename: Original filename
            folder: Folder/prefix in bucket
            content_type: MIME type (auto-detect if None)
        
        Returns:
            Public URL or None if failed
        """
        if not self._is_available():
            self.logger.warning("r2_upload_skip reason=not_configured")
            return None
        self._init_client()
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = filename.replace(" ", "_")
            key = f"{folder}/{timestamp}_{safe_filename}"
            
            # Detect content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Upload to R2
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type,
            )
            
            # Return public URL
            # Format: https://{endpoint}/{bucket}/{key}
            public_url = f"{settings.CLOUDFLARE_R2_ENDPOINT_URL}/{key}"
            return public_url
        
        except ClientError:
            self.logger.error("r2_upload_client_error")
            return None
        except Exception:
            self.logger.error("r2_upload_unexpected_error")
            return None
    
    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        filename: str,
        folder: str = "files",
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """Upload file-like object"""
        content = file_obj.read()
        return self.upload_file(content, filename, folder, content_type)
    
    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from R2 by URL
        
        Args:
            file_url: Full URL of the file
        
        Returns:
            True if successful
        """
        if not self._is_available():
            self.logger.warning("r2_delete_skip reason=not_configured")
            return False
        self._init_client()
        try:
            # Extract key from URL
            # URL format: https://{endpoint}/{bucket}/{key}
            # or: https://{endpoint}/{key}
            key = file_url.split(settings.CLOUDFLARE_R2_ENDPOINT_URL + "/")[-1]
            
            # Remove bucket name if present
            if key.startswith(f"{self.bucket}/"):
                key = key[len(self.bucket) + 1:]
            
            self.client.delete_object(Bucket=self.bucket, Key=key)
            self.logger.info("r2_delete_success")
            return True
        
        except ClientError:
            self.logger.error("r2_delete_client_error")
            return False
        except Exception:
            self.logger.error("r2_delete_unexpected_error")
            return False
    
    def get_file(self, key: str) -> Optional[bytes]:
        """Download file content"""
        if not self._is_available():
            self.logger.warning("r2_get_skip reason=not_configured")
            return None
        self._init_client()
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()
        except ClientError:
            self.logger.error("r2_get_client_error")
            return None
    
    def get_presigned_url(
        self, 
        key: str, 
        expires_in: int = 3600,
        method: str = "get_object"
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access
        
        Args:
            key: Object key
            expires_in: Expiration time in seconds
            method: 'get_object' or 'put_object'
        
        Returns:
            Presigned URL or None
        """
        if not self._is_available():
            self.logger.warning("r2_presign_skip reason=not_configured")
            return None
        self._init_client()
        try:
            url = self.client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError:
            self.logger.error("r2_presign_client_error")
            return None
    
    def list_files(self, prefix: str = "", max_keys: int = 100) -> list:
        """List files in bucket with optional prefix"""
        if not self._is_available():
            self.logger.warning("r2_list_skip reason=not_configured")
            return []
        self._init_client()
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            return response.get('Contents', [])
        except ClientError:
            self.logger.error("r2_list_client_error")
            return []
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists"""
        if not self._is_available():
            self.logger.warning("r2_exists_skip reason=not_configured")
            return False
        self._init_client()
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            self.logger.error("r2_exists_client_error")
            return False

# Singleton instance
r2 = R2Storage()
