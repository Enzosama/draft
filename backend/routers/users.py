from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel, Field
from backend.database import db
from backend.middleware import get_current_user
from backend.models.user import UserResponse

router = APIRouter()

class UserUpdate(BaseModel):
    fullname: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^\+?\d{9,15}$")

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.fetch_one(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE id = ?",
        [current_user["id"]]
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.put("/me", response_model=UserResponse)
async def update_me(update: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_data = update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    fields = []
    params = []
    for key, value in update_data.items():
        fields.append(f"{key} = ?")
        params.append(value)
    params.append(current_user["id"])

    await db.update(
        f"UPDATE users SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
    )

    user = await db.fetch_one(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE id = ?",
        [current_user["id"]]
    )
    return user
