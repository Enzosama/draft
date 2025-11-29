from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from backend.models.post import PostList, PostCreate, PostUpdate, PostResponse
from backend.services.posts import fetch_posts
from backend.database import db
from backend.middleware.auth import require_teacher, get_current_user

router = APIRouter(prefix="/api/teacher/posts", tags=["teacher-posts"])

@router.get("/", response_model=PostList)
async def get_my_posts(
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_teacher)
):
    """Get posts created by the current teacher"""
    try:
        return await fetch_posts(page=page, page_size=page_size, subject=subject, search=search, teacher_id=current_user["id"])
    except HTTPException as e:
        raise e

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher_post(payload: PostCreate, current_user: dict = Depends(require_teacher)):
    """Create a new post as a teacher"""
    # Use teacher's name as author if not provided
    author = payload.author or current_user["fullname"]
    
    post_id = await db.insert(
        (
            "INSERT INTO posts (title, author, \"date\", subject, category, description, "
            "views, downloads, \"class\", specialized, file_url, user_id, teacher_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        [
            payload.title, author, payload.date, payload.subject, payload.category,
            payload.description, 0, 0, payload.class_field, payload.specialized, payload.file_url, 
            current_user["id"], current_user["id"]
        ]
    )
    
    if not post_id:
        raise HTTPException(status_code=500, detail="Failed to create post")
    
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

@router.put("/{post_id}", response_model=PostResponse)
async def update_my_post(post_id: int, payload: PostUpdate, current_user: dict = Depends(require_teacher)):
    """Update a post created by the current teacher"""
    # Verify post belongs to teacher
    post = await db.fetch_one("SELECT id FROM posts WHERE id = ? AND teacher_id = ?", [post_id, current_user["id"]])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or access denied")
    
    data = payload.model_dump(exclude_unset=True, by_alias=True)
    fields = []
    params = []
    
    for key in ["title","author","date","subject","category","description","class","specialized","file_url"]:
        v = data.get(key)
        if v is not None:
            fields.append(f"{key} = ?")
            params.append(v)
    
    if not fields:
        # Return existing post if no changes
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
    
    params.append(post_id)
    
    await db.update(
        f"UPDATE posts SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
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

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_post(post_id: int, current_user: dict = Depends(require_teacher)):
    """Delete a post created by the current teacher"""
    result = await db.execute("DELETE FROM posts WHERE id = ? AND teacher_id = ?", [post_id, current_user["id"]])
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Post not found or access denied")
    
    return {}

# Classroom assignment endpoints
@router.post("/{post_id}/assign/{classroom_id}", status_code=status.HTTP_201_CREATED)
async def assign_post_to_classroom(post_id: int, classroom_id: int, current_user: dict = Depends(require_teacher)):
    """Assign a post to a specific classroom"""
    # Verify post belongs to teacher
    post = await db.fetch_one("SELECT id FROM posts WHERE id = ? AND teacher_id = ?", [post_id, current_user["id"]])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or access denied")
    
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", [classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    # Check if already assigned
    existing = await db.fetch_one("SELECT * FROM classroom_posts WHERE classroom_id = ? AND post_id = ?", [classroom_id, post_id])
    if existing:
        raise HTTPException(status_code=400, detail="Post already assigned to this classroom")
    
    # Assign post to classroom
    await db.execute(
        "INSERT INTO classroom_posts (classroom_id, post_id) VALUES (?, ?)",
        [classroom_id, post_id]
    )
    
    return {"message": "Post assigned to classroom successfully"}

@router.delete("/{post_id}/assign/{classroom_id}")
async def unassign_post_from_classroom(post_id: int, classroom_id: int, current_user: dict = Depends(require_teacher)):
    """Remove a post assignment from a classroom"""
    # Verify post belongs to teacher
    post = await db.fetch_one("SELECT id FROM posts WHERE id = ? AND teacher_id = ?", [post_id, current_user["id"]])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or access denied")
    
    # Remove assignment
    result = await db.execute(
        "DELETE FROM classroom_posts WHERE classroom_id = ? AND post_id = ?",
        [classroom_id, post_id]
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Post unassigned from classroom successfully"}

@router.get("/classroom/{classroom_id}", response_model=PostList)
async def get_classroom_posts(
    classroom_id: int,
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_teacher)
):
    """Get posts assigned to a specific classroom"""
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", [classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    try:
        return await fetch_posts(page=page, page_size=page_size, subject=subject, search=search, classroom_id=classroom_id)
    except HTTPException as e:
        raise e