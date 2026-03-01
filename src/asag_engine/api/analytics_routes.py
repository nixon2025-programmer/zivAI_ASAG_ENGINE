from flask import Blueprint, jsonify
from asag_engine.db.session import get_db
from asag_engine.analytics.service import AnalyticsService

bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


@bp.route("/student/<student_id>", methods=["GET"])
def student_insights(student_id: str):
    db = next(get_db())
    insights = AnalyticsService.student_insights(db, student_id)
    return jsonify(insights.model_dump())