from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from asag_engine.agents.content_agent.agent import ContentAgent
from asag_engine.agents.content_agent.schemas import ContentGenerateRequest


bp_zivai_content = Blueprint("zivai_content_routes", __name__)
content_agent = ContentAgent()


@bp_zivai_content.post("/api/v1/zivai/teacher/content")
def teacher_content():
    try:
        payload = request.get_json(force=True)
        req = ContentGenerateRequest.model_validate(payload)
    except ValidationError as e:
        return jsonify({"error": "validation_error", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": "bad_request", "details": str(e)}), 400

    try:
        out = content_agent.generate(req)
        return jsonify(out.model_dump())
    except Exception as e:
        return jsonify({"error": "generation_failed", "details": str(e)}), 500