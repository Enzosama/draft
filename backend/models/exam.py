from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExamBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    author: str = Field(..., max_length=100)
    subject: str = Field(..., max_length=50)
    description: Optional[str] = None
    duration_min: Optional[int] = None
    file_url: Optional[str] = None
    answer_file_url: Optional[str] = None

class ExamCreate(ExamBase):
    pass

class ExamUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    subject: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    duration_min: Optional[int] = None
    file_url: Optional[str] = None
    answer_file_url: Optional[str] = None

class ExamResponse(ExamBase):
    id: int
    fullname: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    questions: Optional[list] = None

    class Config:
        from_attributes = True

class ExamList(BaseModel):
    total: int
    page: int
    page_size: int
    data: list[ExamResponse]

# Exam Submission Models
class AnswerSubmission(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    option_id: Optional[int] = None

class ExamSubmission(BaseModel):
    exam_id: int
    answers: list[AnswerSubmission]
    time_spent_seconds: int = 0

class ExamResultResponse(BaseModel):
    exam_result_id: int
    exam_id: int
    exam_title: str
    score: float
    total_points: float
    percentage: float
    time_spent_seconds: int
    submitted_at: datetime
    answers: list[dict]  # List of answer details with correctness
