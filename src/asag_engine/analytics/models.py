from sqlalchemy import (
    Column,
    String,
    Float,
    ForeignKey,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from asag_engine.db.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(String(20), primary_key=True)
    student_code = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100))
    grade_level = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("AssessmentAttempt", back_populates="student")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(20), primary_key=True)
    paper_id = Column(String(100))
    question_id = Column(String(100))
    title = Column(String(200), nullable=False)
    topic_code = Column(String(20))
    topic_name = Column(String(100))
    subtopic = Column(String(150))
    max_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("AssessmentAttempt", back_populates="assessment")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(String(30), primary_key=True)
    student_id = Column(String(20), ForeignKey("students.id"))
    assessment_id = Column(String(20), ForeignKey("assessments.id"))

    score_awarded = Column(Float, nullable=False)
    is_correct = Column(Boolean)
    feedback = Column(String)

    attempt_date = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="attempts")
    assessment = relationship("Assessment", back_populates="attempts")