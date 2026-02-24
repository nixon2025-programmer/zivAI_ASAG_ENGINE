from typing import List, Optional, Literal, Any, Dict
from pydantic import BaseModel, Field, model_validator
from pydantic.config import ConfigDict


QuestionType = Literal["short_answer", "multiple_choice", "structured", "essay", "true_false"]
AssessmentType = Literal["Test", "Quiz", "Homework", "Assignment", "Exam", "Project"]
Difficulty = Literal["easy", "medium", "hard"]
FormatType = Literal["pdf", "json", "docx", "online"]


class OptionItem(BaseModel):
    text: str = Field(..., min_length=1)
    isCorrect: bool = False


class AssessmentQuestion(BaseModel):
    questionText: str = Field(..., min_length=3)
    questionType: QuestionType
    points: float = Field(..., gt=0)

    correctAnswer: Optional[str] = ""
    options: List[OptionItem] = Field(default_factory=list)
    attributes: List[str] = Field(default_factory=list)

    markScheme: Optional[str] = ""
    rubric: Optional[str] = ""
    modelAnswer: Optional[str] = ""


class RegenerateInstruction(BaseModel):
    questionIndex: int = Field(..., ge=0)
    teacherFeedback: str = Field(..., min_length=3)


class AssessmentGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., min_length=2)
    description: str = Field(default="")
    type: AssessmentType
    maxScore: float = Field(..., gt=0)
    weight: float = Field(default=0, ge=0)
    dueDate: Optional[str] = None
    courseId: str = Field(..., min_length=1)
    isAIEnhanced: bool = True
    status: str = Field(default="draft")

    subject: Optional[str] = None
    grade: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    format: Optional[FormatType] = "json"
    numQuestions: Optional[int] = Field(default=None, ge=1, le=100)

    questions: List[AssessmentQuestion] = Field(default_factory=list)
    regenerate: List[RegenerateInstruction] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_generation_intent(self):
        if not self.questions:
            if not (self.subject and self.grade and self.topic and self.difficulty and self.numQuestions):
                if self.type != "Project":
                    raise ValueError(
                        "If questions[] is empty, you must provide subject, grade, topic, difficulty, and numQuestions."
                    )
        return self


class AssessmentGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    description: str
    type: AssessmentType
    maxScore: float
    weight: float
    dueDate: Optional[str] = None
    courseId: str
    isAIEnhanced: bool
    status: str

    questions: List[AssessmentQuestion]
    answerKey: Optional[str] = ""
    expectedTotal: float = 0.0
    notes: Optional[str] = ""
    sources: List[Dict[str, Any]] = Field(default_factory=list)