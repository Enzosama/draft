import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from backend.config import settings
import logging

logger = logging.getLogger("security")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using bcrypt directly"""
    try:
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        
        # Bcrypt has a 72-byte limit, truncate if necessary
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash using bcrypt directly"""
    try:
        # Convert to bytes
        password_bytes = password.encode('utf-8')
        
        # Bcrypt has a 72-byte limit, truncate if necessary
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise ValueError(f"Could not hash password: {e}")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode error: {e}")
        return None

def generate_reset_token() -> str:
    """Generate secure password reset token"""
    import secrets
    return secrets.token_urlsafe(32)

def create_password_reset_token(email: str) -> str:
    """Create short-lived token for password reset"""
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "reset"
    }
    return jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None

# Log initialization
logger.info("Security module initialized with bcrypt (direct)")
