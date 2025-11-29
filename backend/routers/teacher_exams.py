from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, List
from backend.models import ExamCreate, ExamUpdate, ExamResponse, ExamList
from backend.database import db
from backend.middleware.auth import require_teacher, get_current_user
from backend.utils import r2

router = APIRouter(prefix="/api/teacher/exams", tags=["teacher-exams"])

@router.get("/", response_model=ExamList)
async def get_my_exams(
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_teacher)
):
    """Get all exams created by the current teacher"""
    offset = (page - 1) * page_size
    
    where_clauses = ["e.created_by = ?"]
    params = [current_user["id"]]
    
    if subject:
        where_clauses.append("e.subject = ?")
        params.append(subject)
    
    if search:
        where_clauses.append("(e.title LIKE ? OR e.author LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_sql = "WHERE " + " AND ".join(where_clauses)
    
    # Count total
    count_result = await db.fetch_one(
        f"""
        SELECT COUNT(*) as total 
        FROM exams e
        {where_sql}
        """,
        params
    )
    total = count_result["total"] if count_result else 0
    
    # Get exams
    exams = await db.fetch_all(
        f"""
        SELECT e.id, u.fullname, e.title, e.author, e.subject, e.file_url,
               e.answer_file_url, e.created_by, e.created_at, e.updated_at
        FROM exams e
        LEFT JOIN users u ON u.id = e.created_by
        {where_sql}
        ORDER BY e.created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset]
    )
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": exams
    }

@router.get("/{exam_id}", response_model=ExamResponse)
async def get_my_exam(exam_id: int, current_user: dict = Depends(require_teacher)):
    """Get a specific exam created by the current teacher"""
    exam = await db.fetch_one(
        """
        SELECT e.id, u.fullname, e.title, e.author, e.subject, e.file_url,
               e.answer_file_url, e.created_by, e.created_at, e.updated_at
        FROM exams e
        LEFT JOIN users u ON u.id = e.created_by
        WHERE e.id = ? AND e.created_by = ?
        """,
        [exam_id, current_user["id"]]
    )
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or access denied"
        )
    
    # Load questions with ordering
    questions_rows = await db.fetch_all(
        """
        SELECT q.question_id, q.question_text, q.question_type, q.points, eq.order_index
        FROM exam_questions eq
        JOIN questions q ON q.question_id = eq.question_id
        WHERE eq.exam_id = ?
        ORDER BY eq.order_index ASC
        """,
        [exam_id]
    )
    
    from backend.models import QuestionResponse
    questions: List[QuestionResponse] = []
    for row in questions_rows:
        q = {
            "question_id": row["question_id"],
            "question_text": row["question_text"],
            "question_type": row["question_type"],
            "points": row["points"],
            "order_index": row["order_index"],
        }
        if row["question_type"] == "multiple_choice":
            options = await db.fetch_all(
                "SELECT option_id, option_text FROM question_options WHERE question_id = ?",
                [row["question_id"]]
            )
            q["options"] = options or []
        else:
            q["options"] = []
        questions.append(q)
    
    exam["questions"] = questions
    return exam

@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam: ExamCreate,
    current_user: dict = Depends(require_teacher)
):
    """Create a new exam as a teacher"""
    exam_id = await db.insert(
        """
        INSERT INTO exams (title, author, subject, description, duration_min, file_url, answer_file_url, created_by, teacher_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            exam.title, exam.author, exam.subject, exam.description, exam.duration_min,
            exam.file_url, exam.answer_file_url, current_user["id"], current_user["id"]
        ]
    )
    
    new_exam = await db.fetch_one(
        """
        SELECT e.id, u.fullname, e.title, e.author, e.subject, e.file_url,
               e.answer_file_url, e.created_by, e.created_at, e.updated_at
        FROM exams e
        LEFT JOIN users u ON u.id = e.created_by
        WHERE e.id = ?
        """,
        [exam_id]
    )
    
    return new_exam

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def create_exam_with_files(
    title: str = Form(...),
    author: str = Form(...),
    subject: str = Form(...),
    file_url_text: Optional[str] = Form(None),
    answer_file_url_text: Optional[str] = Form(None),
    exam_file: Optional[UploadFile] = File(None),
    answer_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_teacher)
):
    """Create exam with file upload as a teacher"""
    exam_url = None
    if exam_file:
        exam_content = await exam_file.read()
        exam_url = r2.upload_file(exam_content, exam_file.filename, folder="exams")
    
    answer_url = None
    if answer_file:
        answer_content = await answer_file.read()
        answer_url = r2.upload_file(answer_content, answer_file.filename, folder="answers")
    
    final_answer = answer_url if answer_url else answer_file_url_text
    final_exam_url = exam_url if exam_url else file_url_text
    
    # Create exam
    exam_id = await db.insert(
        """
        INSERT INTO exams (title, author, subject, file_url, answer_file_url, created_by, teacher_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [title, author, subject, final_exam_url, final_answer, current_user["id"], current_user["id"]]
    )
    
    new_exam = await db.fetch_one(
        """
        SELECT e.id, u.fullname, e.title, e.author, e.subject, e.file_url,
               e.answer_file_url, e.created_by, e.created_at, e.updated_at
        FROM exams e
        LEFT JOIN users u ON u.id = e.created_by
        WHERE e.id = ?
        """,
        [exam_id]
    )
    
    return new_exam

@router.put("/{exam_id}", response_model=ExamResponse)
async def update_my_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    current_user: dict = Depends(require_teacher)
):
    """Update an exam created by the current teacher"""
    # Check if exam exists and belongs to teacher
    existing_exam = await db.fetch_one(
        "SELECT created_by FROM exams WHERE id = ? AND created_by = ?",
        [exam_id, current_user["id"]]
    )
    
    if not existing_exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or access denied"
        )
    
    # Build update query
    update_fields = []
    params = []
    
    update_data = exam_update.model_dump(exclude_unset=True)
    
    if "title" in update_data:
        update_fields.append("title = ?")
        params.append(update_data["title"])
    if "author" in update_data:
        update_fields.append("author = ?")
        params.append(update_data["author"])
    if "subject" in update_data:
        update_fields.append("subject = ?")
        params.append(update_data["subject"])
    if "description" in update_data:
        update_fields.append("description = ?")
        params.append(update_data["description"])
    if "duration_min" in update_data:
        update_fields.append("duration_min = ?")
        params.append(update_data["duration_min"])
    if "file_url" in update_data:
        update_fields.append("file_url = ?")
        params.append(update_data["file_url"])
    if "answer_file_url" in update_data:
        update_fields.append("answer_file_url = ?")
        params.append(update_data["answer_file_url"])
    
    if not update_fields:
        return await get_my_exam(exam_id, current_user)
    
    params.append(exam_id)
    await db.update(
        f"UPDATE exams SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
    )
    return await get_my_exam(exam_id, current_user)

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_exam(exam_id: int, current_user: dict = Depends(require_teacher)):
    """Delete an exam created by the current teacher"""
    result = await db.execute(
        "DELETE FROM exams WHERE id = ? AND created_by = ?",
        [exam_id, current_user["id"]]
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or access denied"
        )
    
    return {}


