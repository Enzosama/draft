from typing import Optional, List, Dict, Any
from backend.models.post import PostResponse, PostList
from backend.config import settings
from fastapi import HTTPException, status
from backend.database import db

def _map_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "author": item.get("author"),
        "date": item.get("date"),
        "subject": item.get("subject"),
        "category": item.get("category"),
        "description": item.get("description"),
        "class_field": item.get("class"),
        "specialized": item.get("specialized"),
        "file_url": item.get("fileUrl") or item.get("file_url"),
        "views": item.get("views", 0),
        "downloads": item.get("downloads", 0),
        "user_id": item.get("user_id"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }

async def fetch_posts(
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
    teacher_id: Optional[int] = None,
    classroom_id: Optional[int] = None,
) -> PostList:
    offset = max(0, (page - 1) * page_size)

    where_clauses: List[str] = []
    params: List[Any] = []

    if subject:
        where_clauses.append("subject = ?")
        params.append(subject)
    if search:
        where_clauses.append("(title LIKE ? OR description LIKE ? OR author LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])
    if teacher_id:
        where_clauses.append("teacher_id = ?")
        params.append(teacher_id)
    if classroom_id:
        # For classroom-specific posts, we need to join with classroom_posts
        where_clauses.append("p.id IN (SELECT post_id FROM classroom_posts WHERE classroom_id = ?)")
        params.append(classroom_id)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    count_row = await db.fetch_one(f"SELECT COUNT(*) AS total FROM posts p {where_sql}", params)
    total = (count_row or {}).get("total", 0)

    query_sql = (
        "SELECT p.id, p.title, p.author, p.date, p.subject, p.category, p.description, "
        "p.views, p.downloads, p.class, p.specialized, p.file_url, p.user_id, p.teacher_id, p.created_at, p.updated_at "
        f"FROM posts p {where_sql} ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
    )

    items = await db.fetch_all(query_sql, params + [page_size, offset])
    mapped = [_map_item(x) for x in items]
    posts: List[PostResponse] = [PostResponse(**item) for item in mapped]
    return PostList(total=total, page=page, page_size=page_size, data=posts)
