from pydantic import BaseModel
from typing import Optional, List

class CopilotRequest(BaseModel):
    task_type: str  # "assessment" | "worksheet" | "lesson_plan"
    topic: str
    grade_level: str
    instructions: Optional[str] = None
    use_school_materials: bool = True
    top_k_context: int = 5

class CopilotResponse(BaseModel):
    generated_content: str
    citations: Optional[List[dict]] = None