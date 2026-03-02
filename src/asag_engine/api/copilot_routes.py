from flask import Blueprint, request, jsonify
from asag_engine.db.session import get_db
from asag_engine.classroom_copilot.service import ClassroomCopilotService
from asag_engine.classroom_copilot.schemas import CopilotRequest

bp_copilot = Blueprint("copilot", __name__, url_prefix="/api/v1/copilot")

service = ClassroomCopilotService()

@bp_copilot.post("/generate")
def generate_content():
    db = next(get_db())
    payload = request.get_json()

    req = CopilotRequest(**payload)
    result = service.generate(db, req)

    return jsonify(result.dict())