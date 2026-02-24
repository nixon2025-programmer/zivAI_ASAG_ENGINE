# src/asag_engine/api/zivai_teacher_routes.py
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from asag_engine.agents.assessment_agent.agent import AssessmentAgent
from asag_engine.agents.assessment_agent.schemas import AssessmentGenerateRequest, AssessmentGenerateResponse

bp_teacher = Blueprint("zivai_teacher", __name__)
agent = AssessmentAgent()


@bp_teacher.post("/api/v1/zivai/teacher/assessments")
def create_assessment():
    try:
        payload = request.get_json(force=True)
        if payload is None:
            return jsonify({"error": "bad_request", "details": "Invalid or missing JSON body."}), 400
        req = AssessmentGenerateRequest.model_validate(payload)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "bad_request", "details": str(e)}), 400

    try:
        result: AssessmentGenerateResponse = agent.generate(req)
        return jsonify(result.model_dump())
    except Exception as e:
        return jsonify({"error": "generation_failed", "details": str(e)}), 500