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


class CurriculumAlignmentLite(BaseModel):
    subject: str
    topic: str
    subtopic: str
    competency: str
    confidence: float = Field(..., ge=0, le=1)


class CurriculumTag(BaseModel):
    topic_code: str = Field(..., min_length=2)
    topic_name: str = Field(..., min_length=2)
    competency: str = Field(..., min_length=3)
    cognitive_level: Optional[str] = None


class CoverageGap(BaseModel):
    topic: Optional[str] = None
    coverage_percent: Optional[float] = None
    recommendation: Optional[str] = None

    topic_code: Optional[str] = None
    topic_name: Optional[str] = None
    reason: Optional[str] = None


class CurriculumAlignment(BaseModel):
    syllabus_name: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None

    aligned_topics: List[CurriculumTag] = Field(default_factory=list)
    coverage_gaps: List[CoverageGap] = Field(default_factory=list)
    suggested_next_topics: List[str] = Field(default_factory=list)
    best_match: Optional[CurriculumAlignmentLite] = None


class GradeResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    score_awarded: float = Field(..., ge=0)
    max_score: float = Field(..., gt=0)

    expected_answer: str = Field(default="")
    is_correct: bool = Field(default=False)
    model_solution: str = Field(default="")

    mark_points_awarded: List[MarkPointAwarded] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    feedback_short: str = Field(..., min_length=1)

    sources: List[SourceItem] = Field(default_factory=list)

    curriculum_alignment: Optional[CurriculumAlignment] = None
    coverage_analysis: List[CoverageGap] = Field(default_factory=list)

    performance_insight: Optional[StudentPerformanceInsight] = None


    @model_validator(mode="after")
    def validate_bounds(self):
        if self.score_awarded > self.max_score:
            self.score_awarded = self.max_score
        if self.score_awarded < 0:
            self.score_awarded = 0.0

        total = 0.0
        fixed: List[MarkPointAwarded] = []

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

        if self.mark_points_awarded:
            self.score_awarded = min(total, self.max_score)

        if self.score_awarded >= self.max_score and self.max_score > 0:
            self.feedback_short = "Correct."
            self.is_correct = True
        elif self.score_awarded == 0:
            self.feedback_short = "Incorrect."
            self.is_correct = False

        return self

class Misconception(BaseModel):
        topic_code: Optional[str] = None
        description: str
        frequency: Optional[int] = None
        severity: Optional[str] = None  # low / medium / high

class MasteryLevel(BaseModel):
        topic_code: Optional[str] = None
        topic_name: Optional[str] = None
        mastery_percent: float = Field(..., ge=0, le=100)
        risk_level: Optional[str] = None  # low / medium / high

class InterventionRecommendation(BaseModel):
        topic_code: Optional[str] = None
        recommendation: str
        priority: Optional[str] = None  # low / medium / high

class StudentPerformanceInsight(BaseModel):
        student_id: Optional[str] = None
        class_id: Optional[str] = None

        overall_average: float = Field(..., ge=0, le=100)

        mastery_by_topic: List[MasteryLevel] = Field(default_factory=list)
        detected_misconceptions: List[Misconception] = Field(default_factory=list)
        recommended_interventions: List[InterventionRecommendation] = Field(default_factory=list)