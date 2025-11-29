# routers/exams.py
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime
from backend.models import (
    ExamCreate, ExamUpdate, ExamResponse, ExamList,
    QuestionCreate, QuestionResponse, AnswerKeyResponse, AnswerKeyItem,
    ExamSubmission, ExamResultResponse, AnswerSubmission,
)
from backend.database import db
from backend.middleware import get_current_user, require_admin
from backend.utils import r2

router = APIRouter()

@router.get("/", response_model=ExamList)
async def get_exams(
    page: int = 1,
    page_size: int = 20,
    subject: Optional[str] = None,
    search: Optional[str] = None,
):
    """Get all exams with filters and pagination"""
    offset = (page - 1) * page_size
    
    # Build query with table aliases - always use aliases for consistency
    where_clauses = []
    params = []
    
    if subject:
        where_clauses.append("e.subject = ?")
        params.append(subject)
    
    if search:
        where_clauses.append("(e.title LIKE ? OR u.fullname LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Always join users for consistency (needed for u.fullname in SELECT and search)
    count_query = f"""
        SELECT COUNT(*) as total 
        FROM exams e
        LEFT JOIN users u ON u.id = e.created_by
        {where_sql}
    """
    
    count_result = await db.fetch_one(count_query, params)
    total = count_result["total"] if count_result else 0
    
    # Get exams - always join users for consistency
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
async def get_exam(exam_id: int):
    """Get single exam by ID"""
    exam = await db.fetch_one(
        """
        SELECT e.id, u.fullname, e.title, e.author, e.subject, e.file_url,
               e.answer_file_url, e.created_by, e.created_at, e.updated_at
        FROM exams e
        LEFT JOIN users u ON u.id = e.created_by
        WHERE e.id = ?
        """,
        [exam_id]
    )
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
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
    current_user: dict = Depends(get_current_user)
):
    """Create new exam"""
    exam_id = await db.insert(
        """
        INSERT INTO exams (title, author, subject, description, duration_min, file_url, answer_file_url, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            exam.title, exam.author, exam.subject, exam.description, exam.duration_min,
            exam.file_url, exam.answer_file_url, current_user["id"]
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
    current_user: dict = Depends(get_current_user)
):
    """Create exam with file upload"""
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
        INSERT INTO exams (title, author, subject, file_url, answer_file_url, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [title, author, subject, final_exam_url, final_answer, current_user["id"]]
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
async def update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update exam"""
    # Check if exam exists and user owns it
    existing_exam = await db.fetch_one(
        "SELECT created_by FROM exams WHERE id = ?",
        [exam_id]
    )
    
    if not existing_exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    if existing_exam["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this exam"
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
        return await get_exam(exam_id)
    
    params.append(exam_id)
    await db.update(
        f"UPDATE exams SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params
    )
    return await get_exam(exam_id)

@router.put("/{exam_id}/admin", response_model=ExamResponse)
async def admin_update_exam(
    exam_id: int,
    exam_update: ExamUpdate,
    admin: dict = Depends(require_admin)
):
    update_fields = []
    params = []
    data = exam_update.model_dump(exclude_unset=True)
    if "title" in data:
        update_fields.append("title = ?")
        params.append(data["title"])
    if "author" in data:
        update_fields.append("author = ?")
        params.append(data["author"])
    if "subject" in data:
        update_fields.append("subject = ?")
        params.append(data["subject"])
    if "description" in data:
        update_fields.append("description = ?")
        params.append(data["description"])
    if "duration_min" in data:
        update_fields.append("duration_min = ?")
        params.append(data["duration_min"])
    if "file_url" in data:
        update_fields.append("file_url = ?")
        params.append(data["file_url"])
    if "answer_file_url" in data:
        update_fields.append("answer_file_url = ?")
        params.append(data["answer_file_url"])
    if update_fields:
        params.append(exam_id)
        await db.update(
            f"UPDATE exams SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params
        )
    return await get_exam(exam_id)

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_exam(exam_id: int, admin: dict = Depends(require_admin)):
    await db.delete("DELETE FROM exam_questions WHERE exam_id = ?", [exam_id])
    qids = await db.fetch_all("SELECT question_id FROM questions WHERE exam_id = ?", [exam_id])
    for q in qids:
        await db.delete("DELETE FROM question_options WHERE question_id = ?", [q["question_id"]])
        await db.delete("DELETE FROM question_answers WHERE question_id = ?", [q["question_id"]])
    await db.delete("DELETE FROM questions WHERE exam_id = ?", [exam_id])
    await db.delete("DELETE FROM exams WHERE id = ?", [exam_id])
    return {}

@router.post("/{exam_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def admin_add_question(
    exam_id: int,
    payload: QuestionCreate,
    admin: dict = Depends(require_admin)
):
    qid = await db.insert(
        "INSERT INTO questions (exam_id, question_text, question_type, points) VALUES (?, ?, ?, ?)",
        [exam_id, payload.question_text, payload.question_type, payload.points]
    )
    order_row = await db.fetch_one("SELECT COALESCE(MAX(order_index), 0) AS max_order FROM exam_questions WHERE exam_id = ?", [exam_id])
    next_order = (order_row or {}).get("max_order", 0) + 1
    await db.insert("INSERT INTO exam_questions (exam_id, question_id, order_index) VALUES (?, ?, ?)", [exam_id, qid, next_order])
    if payload.question_type == "multiple_choice" and payload.options:
        for opt in payload.options:
            await db.insert(
                "INSERT INTO question_options (question_id, option_text, is_correct) VALUES (?, ?, ?)",
                [qid, opt.option_text, 1 if opt.is_correct else 0]
            )
    if payload.question_type in ("true_false","short_answer") and payload.correct_answer:
        await db.insert(
            "INSERT INTO question_answers (question_id, correct_answer) VALUES (?, ?)",
            [qid, payload.correct_answer]
        )
    row = await db.fetch_one("SELECT question_id, question_text, question_type, points FROM questions WHERE question_id = ?", [qid])
    opts = await db.fetch_all("SELECT option_id, option_text, is_correct FROM question_options WHERE question_id = ?", [qid])
    return {
        "question_id": row["question_id"],
        "question_text": row["question_text"],
        "question_type": row["question_type"],
        "points": row["points"],
        "order_index": next_order,
        "options": opts or None,
    }

@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def admin_update_question(
    question_id: int,
    payload: QuestionCreate,
    admin: dict = Depends(require_admin)
):
    await db.update(
        "UPDATE questions SET question_text = ?, question_type = ?, points = ?, updated_at = CURRENT_TIMESTAMP WHERE question_id = ?",
        [payload.question_text, payload.question_type, payload.points, question_id]
    )
    await db.delete("DELETE FROM question_options WHERE question_id = ?", [question_id])
    await db.delete("DELETE FROM question_answers WHERE question_id = ?", [question_id])
    if payload.question_type == "multiple_choice" and payload.options:
        for opt in payload.options:
            await db.insert(
                "INSERT INTO question_options (question_id, option_text, is_correct) VALUES (?, ?, ?)",
                [question_id, opt.option_text, 1 if opt.is_correct else 0]
            )
    if payload.question_type in ("true_false","short_answer") and payload.correct_answer:
        await db.insert(
            "INSERT INTO question_answers (question_id, correct_answer) VALUES (?, ?)",
            [question_id, payload.correct_answer]
        )
    row = await db.fetch_one("SELECT question_id, question_text, question_type, points FROM questions WHERE question_id = ?", [question_id])
    ord_row = await db.fetch_one("SELECT order_index FROM exam_questions WHERE question_id = ?", [question_id])
    opts = await db.fetch_all("SELECT option_id, option_text, is_correct FROM question_options WHERE question_id = ?", [question_id])
    return {
        "question_id": row["question_id"],
        "question_text": row["question_text"],
        "question_type": row["question_type"],
        "points": row["points"],
        "order_index": (ord_row or {}).get("order_index"),
        "options": opts or None,
    }

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_question(question_id: int, admin: dict = Depends(require_admin)):
    await db.delete("DELETE FROM exam_questions WHERE question_id = ?", [question_id])
    await db.delete("DELETE FROM question_options WHERE question_id = ?", [question_id])
    await db.delete("DELETE FROM question_answers WHERE question_id = ?", [question_id])
    await db.delete("DELETE FROM questions WHERE question_id = ?", [question_id])
    return {}

@router.get("/{exam_id}/answer-key", response_model=AnswerKeyResponse)
async def get_answer_key(exam_id: int):
    """Return correct answers for an exam"""
    # Get MCQ correct options
    mcq_answers = await db.fetch_all(
        """
        SELECT qo.question_id, qo.option_id AS correct_option_id
        FROM question_options qo
        JOIN questions q ON q.question_id = qo.question_id
        WHERE q.exam_id = ? AND q.question_type = 'multiple_choice' AND qo.is_correct = 1
        """,
        [exam_id]
    )

    # Get TF/Short answers
    tf_sa_answers = await db.fetch_all(
        """
        SELECT qa.question_id, qa.correct_answer
        FROM question_answers qa
        JOIN questions q ON q.question_id = qa.question_id
        WHERE q.exam_id = ? AND q.question_type IN ('true_false','short_answer')
        """,
        [exam_id]
    )

    answers: List[AnswerKeyItem] = []
    for row in mcq_answers:
        answers.append({
            "question_id": row["question_id"],
            "correct_option_id": row["correct_option_id"]
        })
    for row in tf_sa_answers:
        answers.append({
            "question_id": row["question_id"],
            "correct_answer": row["correct_answer"]
        })

    return {"exam_id": exam_id, "answers": answers}

@router.post("/{exam_id}/submit", response_model=ExamResultResponse, status_code=status.HTTP_201_CREATED)
async def submit_exam(
    exam_id: int,
    submission: ExamSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit exam answers and calculate score"""
    # Verify exam exists
    exam = await db.fetch_one(
        "SELECT id, title FROM exams WHERE id = ?",
        [exam_id]
    )
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Get answer key
    answer_key_data = await get_answer_key(exam_id)
    answer_key = {a["question_id"]: a for a in answer_key_data["answers"]}
    
    # Get questions with points
    questions = await db.fetch_all(
        """
        SELECT q.question_id, q.points, q.question_type
        FROM exam_questions eq
        JOIN questions q ON q.question_id = eq.question_id
        WHERE eq.exam_id = ?
        """,
        [exam_id]
    )
    question_points = {q["question_id"]: q["points"] for q in questions}
    question_types = {q["question_id"]: q["question_type"] for q in questions}
    
    # Calculate score
    total_points = sum(question_points.values())
    score = 0.0
    answer_details = []
    
    for answer in submission.answers:
        q_id = answer.question_id
        q_type = question_types.get(q_id)
        q_points = question_points.get(q_id, 0)
        is_correct = False
        points_earned = 0.0
        
        if q_id in answer_key:
            key = answer_key[q_id]
            if q_type == "multiple_choice":
                # Check if selected option is correct
                if answer.option_id and key.get("correct_option_id") == answer.option_id:
                    is_correct = True
                    points_earned = q_points
            elif q_type in ("true_false", "short_answer"):
                # For now, just check if answer exists (can be improved with fuzzy matching)
                if answer.answer_text and key.get("correct_answer"):
                    # Simple exact match (can be improved)
                    is_correct = answer.answer_text.strip().lower() == key["correct_answer"].strip().lower()
                    if is_correct:
                        points_earned = q_points
        
        score += points_earned
        answer_details.append({
            "question_id": q_id,
            "answer_text": answer.answer_text,
            "option_id": answer.option_id,
            "is_correct": is_correct,
            "points_earned": points_earned,
            "total_points": q_points
        })
    
    percentage = (score / total_points * 100) if total_points > 0 else 0
    
    # Save exam result
    result_id = await db.insert(
        """
        INSERT INTO exam_results (exam_id, student_id, score, total_points, percentage, time_spent_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [exam_id, current_user["id"], score, total_points, percentage, submission.time_spent_seconds]
    )
    
    # Save individual answers
    for detail in answer_details:
        await db.insert(
            """
            INSERT INTO student_answers (exam_result_id, question_id, answer_text, option_id, is_correct, points_earned)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [result_id, detail["question_id"], detail.get("answer_text"), detail.get("option_id"), 
             detail["is_correct"], detail["points_earned"]]
        )
    
    return {
        "exam_result_id": result_id,
        "exam_id": exam_id,
        "exam_title": exam["title"],
        "score": score,
        "total_points": total_points,
        "percentage": percentage,
        "time_spent_seconds": submission.time_spent_seconds,
        "submitted_at": datetime.now(),
        "answers": answer_details
    }

@router.get("/results/{result_id}", response_model=ExamResultResponse)
async def get_exam_result(
    result_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get exam result by ID"""
    result = await db.fetch_one(
        """
        SELECT er.id, er.exam_id, er.score, er.total_points, er.percentage, 
               er.time_spent_seconds, er.submitted_at, e.title
        FROM exam_results er
        JOIN exams e ON e.id = er.exam_id
        WHERE er.id = ? AND er.student_id = ?
        """,
        [result_id, current_user["id"]]
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Get answer details
    answers = await db.fetch_all(
        """
        SELECT question_id, answer_text, option_id, is_correct, points_earned
        FROM student_answers
        WHERE exam_result_id = ?
        """,
        [result_id]
    )
    
    answer_details = [
        {
            "question_id": a["question_id"],
            "answer_text": a.get("answer_text"),
            "option_id": a.get("option_id"),
            "is_correct": a["is_correct"],
            "points_earned": a["points_earned"],
            "total_points": 0  # Will be filled from question
        }
        for a in answers
    ]
    
    return {
        "exam_result_id": result["id"],
        "exam_id": result["exam_id"],
        "exam_title": result["title"],
        "score": result["score"],
        "total_points": result["total_points"],
        "percentage": result["percentage"],
        "time_spent_seconds": result["time_spent_seconds"],
        "submitted_at": result["submitted_at"],
        "answers": answer_details
    }

@router.get("/results", response_model=List[ExamResultResponse])
async def get_my_exam_results(
    current_user: dict = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20
):
    """Get all exam results for current user"""
    offset = (page - 1) * page_size
    
    results = await db.fetch_all(
        """
        SELECT er.id, er.exam_id, er.score, er.total_points, er.percentage,
               er.time_spent_seconds, er.submitted_at, e.title
        FROM exam_results er
        JOIN exams e ON e.id = er.exam_id
        WHERE er.student_id = ?
        ORDER BY er.submitted_at DESC
        LIMIT ? OFFSET ?
        """,
        [current_user["id"], page_size, offset]
    )
    
    return [
        {
            "exam_result_id": r["id"],
            "exam_id": r["exam_id"],
            "exam_title": r["title"],
            "score": r["score"],
            "total_points": r["total_points"],
            "percentage": r["percentage"],
            "time_spent_seconds": r["time_spent_seconds"],
            "submitted_at": r["submitted_at"],
            "answers": []  # Omit details for list view
        }
        for r in results
    ]
    
    
