from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Education API"
    DEBUG: bool = False
    
    # JWT / Authentication
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = "sqlite:///./db.sqlite"
    ENABLE_CLOUDFLARE: bool = False
    
    # Cloudflare D1
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    CLOUDFLARE_DATABASE_ID: Optional[str] = None
    CLOUDFLARE_API_TOKEN: Optional[str] = None
    
    # Cloudflare R2
    CLOUDFLARE_R2_ACCESS_KEY_ID: Optional[str] = None
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: Optional[str] = None
    CLOUDFLARE_R2_ENDPOINT_URL: Optional[str] = None
    CLOUDFLARE_R2_BUCKET_NAME: str = "education-storage"
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@yourdomain.com"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # External API
    EXTERNAL_API_BASE_URL: Optional[str] = None
    EXTERNAL_API_TOKEN: Optional[str] = None

    GEMINI_API_KEY: Optional[str] = None
    ADMIN_EMAILS: Optional[str] = None
    ADMIN_USER_IDS: Optional[str] = None
    
    class Config:
        # Load .env from parent directory (project root)
        import os
        _current_file = os.path.abspath(__file__)
        _backend_dir = os.path.dirname(_current_file)
        _project_root = os.path.dirname(_backend_dir)
        _env_path = os.path.join(_project_root, ".env")
        
        env_file = _env_path
        case_sensitive = True
        extra = "allow"
    
    @property
    def use_cloudflare_d1(self) -> bool:
        return self.ENABLE_CLOUDFLARE and all([
            self.CLOUDFLARE_ACCOUNT_ID,
            self.CLOUDFLARE_DATABASE_ID,
            self.CLOUDFLARE_API_TOKEN
        ])

    @property
    def use_cloudflare_r2(self) -> bool:
        return self.ENABLE_CLOUDFLARE and all([
            self.CLOUDFLARE_R2_ENDPOINT_URL,
            self.CLOUDFLARE_R2_ACCESS_KEY_ID,
            self.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
        ])

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
