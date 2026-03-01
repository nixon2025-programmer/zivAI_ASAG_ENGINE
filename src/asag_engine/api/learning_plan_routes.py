from flask import Blueprint, jsonify
from asag_engine.db.session import get_db
from asag_engine.learning_plans.service import LearningPlanService

bp_learning = Blueprint(
    "learning_plans",
    __name__,
    url_prefix="/api/v1/learning-plans"
)


@bp_learning.route("/student/<student_id>", methods=["POST"])
def generate_learning_plan(student_id):
    db = next(get_db())
    plan = LearningPlanService.generate_plan(db, student_id)
    return jsonify(plan.model_dump())