from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    fullname: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?\d{9,15}$")

class UserCreate(UserBase):
    phone: str = Field(..., pattern=r"^\+?\d{9,15}$", description="Số điện thoại (9-15 chữ số)")
    password: str = Field(..., min_length=6, max_length=72, description="Mật khẩu (6-72 ký tự)")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    role: Optional[str] = "student"
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    password_hash: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

class PasswordRecover(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)

class UserUpdate(BaseModel):
    fullname: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?\d{9,15}$")
