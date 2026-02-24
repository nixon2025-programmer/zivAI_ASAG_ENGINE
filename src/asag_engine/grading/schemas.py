from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class MarkPointAwarded(BaseModel):
    point: str = Field(..., min_length=1)
    marks: float = Field(..., ge=0)
    justification: str = Field(..., min_length=1)


class SourceItem(BaseModel):
    doc_type: Optional[str] = None
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GradeResult(BaseModel):
    # avoid warning for fields starting with "model_"
    model_config = ConfigDict(protected_namespaces=())

    score_awarded: float = Field(..., ge=0)
    max_score: float = Field(..., gt=0)

    # "rubric/llm mode" fields
    expected_answer: str = Field(default="")
    is_correct: bool = Field(default=False)
    model_solution: str = Field(default="")

    # evidence/marking breakdown
    mark_points_awarded: List[MarkPointAwarded] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    feedback_short: str = Field(..., min_length=1)
    sources: List[SourceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bounds(self):
        # clamp score
        if self.score_awarded > self.max_score:
            self.score_awarded = self.max_score
        if self.score_awarded < 0:
            self.score_awarded = 0.0

        # clamp points sum to max_score
        total = 0.0
        fixed = []
        for p in self.mark_points_awarded or []:
            m = float(p.marks or 0.0)
            if m < 0:
                m = 0.0
            if total + m > self.max_score:
                m = max(0.0, self.max_score - total)
            if m > 0:
                p.marks = m
                fixed.append(p)
                total += m
            if total >= self.max_score:
                break
        self.mark_points_awarded = fixed

        # force score to be consistent with points when points exist
        if self.mark_points_awarded:
            self.score_awarded = min(total, self.max_score)

        # keep feedback consistent
        if self.score_awarded >= self.max_score and self.max_score > 0:
            self.feedback_short = "Correct."
            self.is_correct = True
        elif self.score_awarded == 0:
            self.feedback_short = "Incorrect."
            self.is_correct = False
        return self
