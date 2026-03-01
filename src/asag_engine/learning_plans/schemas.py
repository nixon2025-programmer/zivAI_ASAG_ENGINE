from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class LearningPlanItem(BaseModel):
    item_id: str
    type: str
    week_number: int
    title: str
    content: Optional[str] = None
    estimated_minutes: int
    due_at: datetime


class LearningPlanMeta(BaseModel):
    status: str
    start_date: str
    end_date: str
    mastery_now: float
    mastery_target: float


class LearningPlanResponse(BaseModel):
    success: bool
    plan_id: str
    student_id: str
    plan_meta: LearningPlanMeta
    weak_topics: List[str]
    recommendations: List[str]