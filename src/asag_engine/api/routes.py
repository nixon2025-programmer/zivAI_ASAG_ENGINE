from flask import Blueprint, request, jsonify
from pydantic import BaseModel, Field, ValidationError
from asag_engine.grading.grader import ASAGGrader

bp = Blueprint("routes", __name__)
grader = ASAGGrader()

class GradeRequest(BaseModel):
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
        result = grader.grade(req.question_text, req.student_answer, req.max_marks)
        return jsonify(result.model_dump())
    except Exception as e:
        return jsonify({"error": "grading_failed", "details": str(e)}), 500
