from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from pydantic.config import ConfigDict

CompressionLevel = Literal["brief", "medium", "detailed"]
Differentiation = Literal["foundation", "core", "advanced"]


class FlashcardItem(BaseModel):
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)


class WorkedExample(BaseModel):
    question: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)


class RevisionItem(BaseModel):
    keyPoint: str = Field(..., min_length=1)
    quickPractice: str = Field(..., min_length=1)


class SlideBullet(BaseModel):
    text: str = Field(..., min_length=1)
    bulletPoint: str = Field(..., min_length=1)


class SlideOutline(BaseModel):
    bulletPoints: List[SlideBullet] = Field(default_factory=list)


class ContentGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    courseId: str = Field(..., min_length=1)
    sourceResourceId: Optional[str] = None

    topic: str = Field(..., min_length=2)
    compressionLevel: CompressionLevel = "medium"
    focusPoints: List[str] = Field(default_factory=list)

    includeFlashcards: bool = False
    useRag: bool = False

    grade: Optional[str] = None
    learningObjectives: List[str] = Field(default_factory=list)
    curriculumStandard: Optional[str] = None

    differentiation: Differentiation = "core"

    @model_validator(mode="after")
    def _basic_checks(self):
        if not self.topic.strip():
            raise ValueError("topic is required")
        return self


class ContentGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    courseId: str
    sourceResourceId: Optional[str] = None
    topic: str

    grade: Optional[str] = None
    curriculumStandard: Optional[str] = None
    learningObjectives: List[str] = Field(default_factory=list)

    compressionLevel: CompressionLevel
    differentiation: Differentiation

    summary: str = Field(..., min_length=1)
    lessonNotes: str = Field(..., min_length=1)

    # ✅ structured (no more stringified blobs)
    workedExamples: List[WorkedExample] = Field(default_factory=list)
    revisionSheet: List[RevisionItem] = Field(default_factory=list)
    slideOutline: SlideOutline = Field(default_factory=SlideOutline)

    includeFlashcards: bool
    flashcards: List[FlashcardItem] = Field(default_factory=list)

    ragEvidence: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)