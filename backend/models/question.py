from pydantic import BaseModel, Field
from typing import Optional, List

class QuestionBase(BaseModel):
    question_text: str = Field(...)
    question_type: str = Field(...)
    points: Optional[float] = 1

class QuestionOption(BaseModel):
    option_id: Optional[int] = None
    option_text: str
    is_correct: Optional[bool] = None

class QuestionCreate(QuestionBase):
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None

class QuestionResponse(QuestionBase):
    question_id: int
    order_index: Optional[int] = None
    options: Optional[List[QuestionOption]] = None

class AnswerKeyItem(BaseModel):
    question_id: int
    correct_option_id: Optional[int] = None
    correct_answer: Optional[str] = None

class AnswerKeyResponse(BaseModel):
    exam_id: int
    answers: List[AnswerKeyItem]
