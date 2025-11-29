from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
from backend.models.post import PostList, PostCreate, PostUpdate, PostResponse
from backend.services.posts import fetch_posts
from backend.database import db
from backend.middleware.auth import require_admin, require_teacher_or_admin, get_current_user

router = APIRouter()

@router.get("/", response_model=PostList)
async def get_posts(
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
):
    try:
        return await fetch_posts(page=page, page_size=page_size, subject=subject, search=search)
    except HTTPException as e:
        raise e

@router.get("", response_model=PostList)
async def get_posts_no_slash(
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
):
    try:
        return await fetch_posts(page=page, page_size=page_size, subject=subject, search=search)
    except HTTPException as e:
        raise e

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, current_user: dict = Depends(require_teacher_or_admin)):
    # For teachers, set teacher_id and use their name as author if not provided
    if current_user.get("role") == "teacher":
        author = payload.author or current_user["fullname"]
        teacher_id = current_user["id"]
        user_id = current_user["id"]
    else:  # Admin
        author = payload.author
        teacher_id = None
        user_id = current_user["id"]
    
    post_id = await db.insert(
        (
            "INSERT INTO posts (title, author, \"date\", subject, category, description, "
            "views, downloads, \"class\", specialized, file_url, user_id, teacher_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        [
            payload.title, author, payload.date, payload.subject, payload.category,
            payload.description, 0, 0, payload.class_field, payload.specialized, payload.file_url, user_id, teacher_id,
        ]
    )
    row = await db.fetch_one(
        "SELECT id, title, author, date, subject, category, description, views, downloads, class, specialized, file_url, user_id, teacher_id, created_at, updated_at FROM posts WHERE id = ?",
        [post_id]
    )
    return PostResponse(**{
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "date": row["date"],
        "subject": row["subject"],
        "category": row["category"],
        "description": row["description"],
        "class_field": row.get("class"),
        "specialized": row.get("specialized"),
        "file_url": row.get("file_url"),
        "views": row.get("views", 0),
        "downloads": row.get("downloads", 0),
        "user_id": row.get("user_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    })

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_no_slash(payload: PostCreate, current_user: dict = Depends(require_teacher_or_admin)):
    return await create_post(payload, current_user)

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, payload: PostUpdate, current_user: dict = Depends(require_teacher_or_admin)):
    # Check if user has permission to update this post
    post = await db.fetch_one("SELECT id, teacher_id, user_id FROM posts WHERE id = ?", [post_id])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Teachers can only update their own posts, admins can update any post
    if current_user.get("role") == "teacher" and post["teacher_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only update your own posts")
    
    data = payload.model_dump(exclude_unset=True, by_alias=True)
    fields = []
    params = []
    for key in ["title","author","date","subject","category","description","class","specialized","file_url"]:
        v = data.get(key)
        if v is not None:
            fields.append(f"{key} = ?")
            params.append(v)
    if not fields:
        row = await db.fetch_one(
            "SELECT id, title, author, date, subject, category, description, views, downloads, class, specialized, file_url, user_id, teacher_id, created_at, updated_at FROM posts WHERE id = ?",
            [post_id]
        )
        if not row:
            raise HTTPException(status_code=404, detail="Post not found")
        return PostResponse(**{
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "date": row["date"],
            "subject": row["subject"],
            "category": row["category"],
            "description": row["description"],
            "class_field": row.get("class"),
            "specialized": row.get("specialized"),
            "file_url": row.get("file_url"),
            "views": row.get("views", 0),
            "downloads": row.get("downloads", 0),
            "user_id": row.get("user_id"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        })
    params.append(post_id)
    await db.update(
        f"UPDATE posts SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
    )
    row = await db.fetch_one(
        "SELECT id, title, author, date, subject, category, description, views, downloads, class, specialized, file_url, user_id, teacher_id, created_at, updated_at FROM posts WHERE id = ?",
        [post_id]
    )
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(**{
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "date": row["date"],
        "subject": row["subject"],
        "category": row["category"],
        "description": row["description"],
        "class_field": row.get("class"),
        "specialized": row.get("specialized"),
        "file_url": row.get("file_url"),
        "views": row.get("views", 0),
        "downloads": row.get("downloads", 0),
        "user_id": row.get("user_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    })

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, current_user: dict = Depends(require_teacher_or_admin)):
    # Check if user has permission to delete this post
    post = await db.fetch_one("SELECT id, teacher_id FROM posts WHERE id = ?", [post_id])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Teachers can only delete their own posts, admins can delete any post
    if current_user.get("role") == "teacher" and post["teacher_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    
    await db.delete("DELETE FROM posts WHERE id = ?", [post_id])
    return {}
