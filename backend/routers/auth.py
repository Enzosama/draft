from fastapi import APIRouter, HTTPException, status, Depends
import logging
import time
from backend.models import UserCreate, UserLogin, UserResponse, Token
from backend.database import db
from backend.utils import get_password_hash, verify_password, create_access_token
from backend.middleware.auth import get_current_user

router = APIRouter()
logger = logging.getLogger("auth")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    t0 = time.perf_counter()
    logger.info(f"register_attempt email={user.email}")
    
    existing = await db.fetch_one("SELECT id FROM users WHERE email = ?", [user.email])
    if existing:
        logger.warning(f"register_conflict email={user.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được đăng ký. Vui lòng sử dụng email khác hoặc đăng nhập."
        )
    
    try:
        password_hash = get_password_hash(user.password)
    except Exception as e:
        logger.error(f"register_fail email={user.email} reason=unknown_error error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi đăng ký. Vui lòng thử lại sau."
        )
    # Attempt primary insert with phone; fallback if legacy schema requires dateofbirth
    try:
        try:
            user_id = await db.insert(
                "INSERT INTO users (fullname, email, phone, password_hash, role, is_active) VALUES (?, ?, ?, ?, 'student', 1)",
                [user.fullname, user.email, user.phone, password_hash]
            )
        except Exception as e1:
            logger.warning(f"register_insert_fallback1 email={user.email} error={str(e1)}")
            try:
                user_id = await db.insert(
                    "INSERT INTO users (fullname, email, dateofbirth, phone, password_hash, role, is_active) VALUES (?, ?, ?, ?, ?, 'student', 1)",
                    [user.fullname, user.email, "", user.phone, password_hash]
                )
            except Exception as e2:
                logger.warning(f"register_insert_fallback2 email={user.email} error={str(e2)}")
                user_id = await db.insert(
                    "INSERT INTO users (fullname, email, dateofbirth, password_hash, is_active) VALUES (?, ?, ?, ?, 1)",
                    [user.fullname, user.email, "", password_hash]
                )
    except Exception as e:
        logger.error(f"register_fail email={user.email} reason=db_insert_error error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể tạo tài khoản. Vui lòng thử lại sau."
        )
    created = await db.fetch_one(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE id = ?",
        [user_id]
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(f"register_success email={user.email} user_id={user_id} latency_ms={latency_ms}")
    return created

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    t0 = time.perf_counter()
    logger.info(f"login_attempt email={credentials.email}")
    user = await db.fetch_one(
        "SELECT id, email, password_hash, role, is_active FROM users WHERE email = ?",
        [credentials.email]
    )
    if not user or not user.get("is_active"):
        latency_ms = int((time.perf_counter() - t0) * 1000)
        logger.warning(f"login_fail email={credentials.email} reason=not_found_or_inactive latency_ms={latency_ms}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng. Vui lòng kiểm tra lại."
        )
    if not verify_password(credentials.password, user["password_hash"]):
        latency_ms = int((time.perf_counter() - t0) * 1000)
        logger.warning(f"login_fail email={credentials.email} reason=wrong_password latency_ms={latency_ms}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng. Vui lòng kiểm tra lại."
        )
    token = create_access_token({"sub": user["email"], "uid": user["id"]})
    latency_ms = int((time.perf_counter() - t0) * 1000)
    logger.info(f"login_success email={credentials.email} user_id={user['id']} latency_ms={latency_ms}")
    return {"access_token": token, "token_type": "bearer"}

from pydantic import BaseModel, EmailStr

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

from backend.utils.email import send_password_reset_email
import uuid
import datetime

@router.post("/recover")
async def recover(payload: PasswordRecoveryRequest):
    # Check if user exists
    user = await db.fetch_one("SELECT id, email FROM users WHERE email = ?", [payload.email])
    if not user:
        # For security, we don't want to reveal if email exists or not
        # So we just simulate a success response
        # Add a small delay to mimic processing time
        time.sleep(0.5)
        return {"message": "Nếu email tồn tại, liên kết đặt lại mật khẩu sẽ được gửi."}
        
    # Generate reset token
    token = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    # Save token to DB
    await db.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        [user["id"], token, expires_at]
    )
    
    # Send email
    email_sent = await send_password_reset_email(user["email"], token)
    
    if not email_sent:
        # Fallback for development: Log the link
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        logger.warning(f"⚠️ Email sending failed (likely not configured). Reset link for {user['email']}: {reset_link}")
        print(f"\n\n[DEV MODE] Password Reset Link for {user['email']}:\n{reset_link}\n\n")
    
    return {"message": "Nếu email tồn tại, liên kết đặt lại mật khẩu sẽ được gửi."}

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint - currently just returns success (token invalidation handled client-side)"""
    logger.info(f"logout_success user_id={current_user.get('id')} email={current_user.get('email')}")
    return {"message": "Đăng xuất thành công"}
