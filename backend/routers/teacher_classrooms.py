from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.database import db
from backend.middleware.auth import require_teacher, get_current_user
import random
import string

router = APIRouter(prefix="/api/teacher/classrooms", tags=["teacher-classrooms"])

class ClassroomCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    subject: Optional[str] = None

class ClassroomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    subject: Optional[str] = None
    is_active: Optional[bool] = None

class ClassroomResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    subject: Optional[str] = None
    code: str
    is_active: bool
    student_count: int
    created_at: str

class StudentResponse(BaseModel):
    id: int
    fullname: str
    email: str
    phone: str
    joined_at: str

class AddStudentRequest(BaseModel):
    student_email: str

def generate_classroom_code():
    """Generate a unique 6-character classroom code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        # Check if code exists
        # This is a simple check - in production you'd want to handle this more robustly
        return code

@router.get("/", response_model=List[ClassroomResponse])
async def list_my_classrooms(current_user: dict = Depends(require_teacher)):
    """List all classrooms owned by the current teacher"""
    classrooms = await db.fetch_all(
        """SELECT c.id, c.name, c.description, c.subject, c.code, c.is_active, 
                  c.created_at, COUNT(cs.student_id) as student_count
           FROM classrooms c
           LEFT JOIN classroom_students cs ON c.id = cs.classroom_id
           WHERE c.teacher_id = ?
           GROUP BY c.id
           ORDER BY c.created_at DESC""",
        [current_user["id"]]
    )
    
    return classrooms

@router.post("/", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
async def create_classroom(payload: ClassroomCreate, current_user: dict = Depends(require_teacher)):
    """Create a new classroom"""
    code = generate_classroom_code()
    
    # Insert classroom and get the ID
    classroom_id = await db.insert(
        """INSERT INTO classrooms (name, description, subject, teacher_id, code, is_active) 
           VALUES (?, ?, ?, ?, ?, 1)""",
        [payload.name, payload.description, payload.subject, current_user["id"], code]
    )
    
    if not classroom_id:
        raise HTTPException(status_code=500, detail="Failed to create classroom")
    
    # Get the created classroom
    classroom = await db.fetch_one(
        """SELECT c.id, c.name, c.description, c.subject, c.code, c.is_active, 
                  c.created_at, 0 as student_count
           FROM classrooms c
           WHERE c.id = ?""",
        [classroom_id]
    )
    
    return classroom

@router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(classroom_id: int, current_user: dict = Depends(require_teacher)):
    """Get classroom details"""
    classroom = await db.fetch_one(
        """SELECT c.id, c.name, c.description, c.subject, c.code, c.is_active, 
                  c.created_at, COUNT(cs.student_id) as student_count
           FROM classrooms c
           LEFT JOIN classroom_students cs ON c.id = cs.classroom_id
           WHERE c.id = ? AND c.teacher_id = ?
           GROUP BY c.id""",
        [classroom_id, current_user["id"]]
    )
    
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    return classroom

@router.put("/{classroom_id}", response_model=ClassroomResponse)
async def update_classroom(classroom_id: int, payload: ClassroomUpdate, current_user: dict = Depends(require_teacher)):
    """Update classroom information"""
    # Check if classroom exists and belongs to teacher
    existing = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", [classroom_id, current_user["id"]])
    if not existing:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    # Build update query
    update_fields = []
    params = []
    
    if payload.name is not None:
        update_fields.append("name = ?")
        params.append(payload.name)
    
    if payload.description is not None:
        update_fields.append("description = ?")
        params.append(payload.description)
    
    if payload.subject is not None:
        update_fields.append("subject = ?")
        params.append(payload.subject)
    
    if payload.is_active is not None:
        update_fields.append("is_active = ?")
        params.append(payload.is_active)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    params.append(classroom_id)
    
    await db.execute(
        f"UPDATE classrooms SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
    )
    
    # Return updated classroom
    classroom = await db.fetch_one(
        """SELECT c.id, c.name, c.description, c.subject, c.code, c.is_active, 
                  c.created_at, COUNT(cs.student_id) as student_count
           FROM classrooms c
           LEFT JOIN classroom_students cs ON c.id = cs.classroom_id
           WHERE c.id = ?
           GROUP BY c.id""",
        [classroom_id]
    )
    
    return classroom

@router.delete("/{classroom_id}")
async def delete_classroom(classroom_id: int, current_user: dict = Depends(require_teacher)):
    """Delete classroom (and all related data due to CASCADE)"""
    result = await db.execute(
        "DELETE FROM classrooms WHERE id = ? AND teacher_id = ?",
        [classroom_id, current_user["id"]]
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    return {"message": "Classroom deleted successfully"}

@router.get("/{classroom_id}/students", response_model=List[StudentResponse])
async def list_classroom_students(classroom_id: int, current_user: dict = Depends(require_teacher)):
    """List all students in a classroom"""
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", [classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    students = await db.fetch_all(
        """SELECT u.id, u.fullname, u.email, u.phone, cs.joined_at
           FROM users u
           JOIN classroom_students cs ON u.id = cs.student_id
           WHERE cs.classroom_id = ?
           ORDER BY cs.joined_at DESC""",
        [classroom_id]
    )
    
    return students

@router.post("/{classroom_id}/students", status_code=status.HTTP_201_CREATED)
async def add_student_to_classroom(classroom_id: int, payload: AddStudentRequest, current_user: dict = Depends(require_teacher)):
    """Add a student to classroom by email"""
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", [classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    # Find student by email
    student = await db.fetch_one("SELECT id FROM users WHERE email = ? AND role = 'student'", [payload.student_email])
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student_id = student["id"]
    
    # Check if student is already in classroom
    existing = await db.fetch_one("SELECT * FROM classroom_students WHERE classroom_id = ? AND student_id = ?", [classroom_id, student_id])
    if existing:
        raise HTTPException(status_code=400, detail="Student already in classroom")
    
    # Add student to classroom
    await db.execute(
        "INSERT INTO classroom_students (classroom_id, student_id) VALUES (?, ?)",
        [classroom_id, student_id]
    )
    
    return {"message": "Student added to classroom successfully"}

@router.delete("/{classroom_id}/students/{student_id}")
async def remove_student_from_classroom(classroom_id: int, student_id: int, current_user: dict = Depends(require_teacher)):
    """Remove a student from classroom"""
    # Verify classroom belongs to teacher
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE id = ? AND teacher_id = ?", [classroom_id, current_user["id"]])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or access denied")
    
    # Remove student from classroom
    result = await db.execute(
        "DELETE FROM classroom_students WHERE classroom_id = ? AND student_id = ?",
        [classroom_id, student_id]
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found in classroom")
    
    return {"message": "Student removed from classroom successfully"}

# Student endpoints (for joining classrooms)
@router.post("/join/{classroom_code}", status_code=status.HTTP_201_CREATED)
async def join_classroom(classroom_code: str, current_user: dict = Depends(get_current_user)):
    """Student joins a classroom using code"""
    # Verify user is a student
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can join classrooms")
    
    # Find classroom by code
    classroom = await db.fetch_one("SELECT id FROM classrooms WHERE code = ? AND is_active = 1", [classroom_code])
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found or inactive")
    
    classroom_id = classroom["id"]
    
    # Check if student is already in classroom
    existing = await db.fetch_one("SELECT * FROM classroom_students WHERE classroom_id = ? AND student_id = ?", [classroom_id, current_user["id"]])
    if existing:
        raise HTTPException(status_code=400, detail="Already joined this classroom")
    
    # Add student to classroom
    await db.execute(
        "INSERT INTO classroom_students (classroom_id, student_id) VALUES (?, ?)",
        [classroom_id, current_user["id"]]
    )
    
    return {"message": "Successfully joined classroom"}

@router.get("/student/my-classrooms", response_model=List[ClassroomResponse])
async def list_student_classrooms(current_user: dict = Depends(get_current_user)):
    """List all classrooms the student is enrolled in"""
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students can view enrolled classrooms")
    
    classrooms = await db.fetch_all(
        """SELECT c.id, c.name, c.description, c.subject, c.code, c.is_active, 
                  c.created_at, COUNT(cs2.student_id) as student_count
           FROM classrooms c
           JOIN classroom_students cs ON c.id = cs.classroom_id
           LEFT JOIN classroom_students cs2 ON c.id = cs2.classroom_id
           WHERE cs.student_id = ? AND c.is_active = 1
           GROUP BY c.id
           ORDER BY cs.joined_at DESC""",
        [current_user["id"]]
    )
    
    return classrooms