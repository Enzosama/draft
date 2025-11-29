from fastapi import APIRouter
from backend.database import db

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

@router.get("/")
async def list_subjects():
    rows = await db.fetch_all("SELECT id, name, description, parent_id FROM subjects ORDER BY name ASC")
    return rows
