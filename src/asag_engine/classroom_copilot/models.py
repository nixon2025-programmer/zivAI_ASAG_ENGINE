from sqlalchemy import Column, String, Text, Integer, DateTime, func
from sqlalchemy.orm import relationship
from asag_engine.db.base import Base
import uuid


class CopilotDraft(Base):
    __tablename__ = "copilot_drafts"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)

    task_type = Column(String(50), nullable=False)
    topic = Column(String(255), nullable=False)
    grade_level = Column(String(50), nullable=False)

    content = Column(Text, nullable=False)

    version = Column(Integer, default=1)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())