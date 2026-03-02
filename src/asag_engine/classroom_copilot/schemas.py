from pydantic import BaseModel
from typing import Optional


class CopilotRequest(BaseModel):
    task_type: str
    topic: str
    grade_level: str
    instructions: str


class CopilotEditRequest(BaseModel):
    draft_id: str
    edit_instruction: str


class CopilotResponse(BaseModel):
    draft_id: str
    generated_content: str
    citations: list
    version: int