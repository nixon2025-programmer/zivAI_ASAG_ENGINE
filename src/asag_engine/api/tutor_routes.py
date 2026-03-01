from flask import Blueprint, request, jsonify
from asag_engine.db.session import get_db
from asag_engine.tutor.service import TutorService
from asag_engine.tutor.schemas import TutorRequest, TutorResponse

bp_tutor = Blueprint(
    "tutor",
    __name__,
    url_prefix="/api/v1/tutor",
)


@bp_tutor.route("/student/<student_id>", methods=["POST"])
def tutor_agent(student_id):
    db = next(get_db())
    data = request.json

    req = TutorRequest(
        student_id=student_id,
        question_text=data["question_text"],
        student_answer=data.get("student_answer"),
        request_type=data["request_type"],
    )

    result = TutorService.generate_response(
        db=db,
        student_id=req.student_id,
        question_text=req.question_text,
        request_type=req.request_type,
        student_answer=req.student_answer,
    )

    response = TutorResponse(
        student_id=req.student_id,
        request_type=req.request_type,
        response=result,
    )

    return jsonify(response.dict())