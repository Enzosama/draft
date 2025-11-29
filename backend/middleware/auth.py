from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.database import db
from backend.utils import decode_token
from backend.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.fetch_one(
        "SELECT * FROM users WHERE email = ? AND is_active = 1",
        [email]
    )
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """Get current user if token provided, otherwise None"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    # First check if user has admin role
    print(f"DEBUG: require_admin user={current_user.get('email')} role={current_user.get('role')}")
    if current_user.get("role") == "admin":
        return current_user
    
    # Then check environment-based admin configuration
    emails = [e.strip().lower() for e in (settings.ADMIN_EMAILS or "").split(",") if e.strip()]
    ids = [int(x) for x in (settings.ADMIN_USER_IDS or "").split(",") if x.strip().isdigit()]
    if (current_user.get("email", "").lower() in emails) or (current_user.get("id") in ids):
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")

async def require_teacher(current_user: dict = Depends(get_current_user)) -> dict:
    """Require user to be either teacher or admin"""
    if current_user.get("role") in ["teacher", "admin"]:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher required")

async def require_teacher_or_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require user to be either teacher or admin"""
    if current_user.get("role") in ["teacher", "admin"]:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher or admin required")
