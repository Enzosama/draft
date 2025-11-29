from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from backend.database import db
from backend.middleware.auth import require_admin, get_current_user

router = APIRouter(prefix="/api/admin/teachers", tags=["admin-teachers"])

class TeacherCreate(BaseModel):
    email: EmailStr
    fullname: str
    phone: str
    password: str

class TeacherUpdate(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class TeacherResponse(BaseModel):
    id: int
    fullname: str
    email: str
    phone: str
    role: str
    is_active: bool
    created_at: str

@router.get("/", response_model=List[TeacherResponse])
async def list_teachers(admin: dict = Depends(require_admin)):
    """List all teachers"""
    teachers = await db.fetch_all(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE role = 'teacher' ORDER BY created_at DESC"
    )
    return teachers

@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(payload: TeacherCreate, admin: dict = Depends(require_admin)):
    """Create a new teacher account"""
    # Check if email already exists
    existing = await db.fetch_one("SELECT id FROM users WHERE email = ?", [payload.email])
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with teacher role
    from backend.utils import get_password_hash
    password_hash = get_password_hash(payload.password)
    
    result = await db.execute(
        """INSERT INTO users (fullname, email, phone, password_hash, role, is_active) 
           VALUES (?, ?, ?, ?, 'teacher', 1)""",
        [payload.fullname, payload.email, payload.phone, password_hash]
    )
    
    # Get the created teacher (get the ID from the result)
    teacher_id = result.get("lastrowid") if isinstance(result, dict) else result.lastrowid if hasattr(result, 'lastrowid') else None
    
    teacher = await db.fetch_one(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE id = ?",
        [teacher_id]
    )
    
    return teacher

@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(teacher_id: int, admin: dict = Depends(require_admin)):
    """Get teacher details"""
    teacher = await db.fetch_one(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE id = ? AND role = 'teacher'",
        [teacher_id]
    )
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return teacher

@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(teacher_id: int, payload: TeacherUpdate, admin: dict = Depends(require_admin)):
    """Update teacher information"""
    # Check if teacher exists
    existing = await db.fetch_one("SELECT id FROM users WHERE id = ? AND role = 'teacher'", [teacher_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Build update query
    update_fields = []
    params = []
    
    if payload.fullname is not None:
        update_fields.append("fullname = ?")
        params.append(payload.fullname)
    
    if payload.phone is not None:
        update_fields.append("phone = ?")
        params.append(payload.phone)
    
    if payload.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(payload.is_active)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    params.append(teacher_id)
    
    await db.execute(
        f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
    )
    
    # Return updated teacher
    teacher = await db.fetch_one(
        "SELECT id, fullname, email, phone, role, is_active, created_at FROM users WHERE id = ?",
        [teacher_id]
    )
    
    return teacher

@router.delete("/{teacher_id}")
async def delete_teacher(teacher_id: int, admin: dict = Depends(require_admin)):
    """Delete teacher (soft delete by setting is_active = 0)"""
    result = await db.execute(
        "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND role = 'teacher'",
        [teacher_id]
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {"message": "Teacher deactivated successfully"}

@router.post("/{teacher_id}/activate")
async def activate_teacher(teacher_id: int, admin: dict = Depends(require_admin)):
    """Activate a teacher account"""
    result = await db.execute(
        "UPDATE users SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND role = 'teacher'",
        [teacher_id]
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {"message": "Teacher activated successfully"}

@router.get("/{teacher_id}/classrooms")
async def get_teacher_classrooms(teacher_id: int, admin: dict = Depends(require_admin)):
    """Get all classrooms managed by a teacher"""
    classrooms = await db.fetch_all(
        """SELECT c.id, c.name, c.description, c.subject, c.code, c.is_active, 
                  c.created_at, COUNT(cs.student_id) as student_count
           FROM classrooms c
           LEFT JOIN classroom_students cs ON c.id = cs.classroom_id
           WHERE c.teacher_id = ?
           GROUP BY c.id
           ORDER BY c.created_at DESC""",
        [teacher_id]
    )
    
    return classrooms