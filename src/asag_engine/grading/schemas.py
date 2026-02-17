from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class MarkPointAwarded(BaseModel):
    point: str = Field(..., description="Mark point matched from scheme evidence")
    marks: float = Field(..., ge=0)
    justification: str = Field(..., description="Why marks were awarded")

class SourceItem(BaseModel):
    doc_type: Optional[str] = None
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GradeResult(BaseModel):
    score_awarded: float = Field(..., ge=0)
    max_score: float = Field(..., gt=0)
    mark_points_awarded: List[MarkPointAwarded] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    feedback_short: str
    sources: List[SourceItem] = Field(default_factory=list)
