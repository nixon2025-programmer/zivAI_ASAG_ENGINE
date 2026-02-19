from typing import Optional
from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field, ValidationError
from asag_engine.grading.grader import ASAGGrader

bp = Blueprint("routes", __name__)
grader = ASAGGrader()


class GradeRequest(BaseModel):
    paper_id: Optional[str] = Field(default=None, description="Optional paper id")
    question_id: Optional[str] = Field(default=None, description="Optional question id")
    question_text: str = Field(..., min_length=3)
    student_answer: str = Field(..., min_length=1)
    max_marks: float = Field(..., gt=0)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/api/v1/grade")
def grade():
    try:
        payload = request.get_json(force=True)
        req = GradeRequest.model_validate(payload)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "bad_request", "details": str(e)}), 400

    try:
        result = grader.grade(
            paper_id=req.paper_id,
            question_id=req.question_id,
            question_text=req.question_text,
            student_answer=req.student_answer,
            max_marks=req.max_marks,
        )
        return jsonify(result.model_dump())
    except Exception as e:
        return jsonify({"error": "grading_failed", "details": str(e)}), 500
