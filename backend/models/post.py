from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PostBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    author: str = Field(..., max_length=100)
    date: str
    subject: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50)
    description: Optional[str] = None
    class_field: Optional[str] = Field(None, alias="class", max_length=20)
    specialized: Optional[str] = Field(None, max_length=50)
    file_url: Optional[str] = None

class PostCreate(PostBase):
    author: Optional[str] = Field(None, max_length=100)  # Make author optional for teacher posts

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    date: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    class_field: Optional[str] = Field(None, alias="class", max_length=20)
    specialized: Optional[str] = Field(None, max_length=50)
    file_url: Optional[str] = None

class PostResponse(PostBase):
    id: int
    views: int = 0
    downloads: int = 0
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True

class PostList(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[PostResponse]