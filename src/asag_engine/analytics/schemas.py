from pydantic import BaseModel
from typing import List, Optional


class TopicPerformance(BaseModel):
    topic_code: str
    topic_name: Optional[str] = None
    average_score: float
    mastery_level: str


class StudentInsight(BaseModel):
    student_id: str
    risk_level: str
    weak_topics: List[str]
    recommendations: List[str]


class ClassInsight(BaseModel):
    class_id: str
    average_score: float
    weak_topics: List[str]