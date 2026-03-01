from pydantic import BaseModel
from typing import Optional


class TutorRequest(BaseModel):
    student_id: str
    question_text: str
    student_answer: Optional[str] = None
    request_type: str  # "explain", "hint", "step_by_step", "feedback"


class TutorResponse(BaseModel):
    student_id: str
    request_type: str
    response: str