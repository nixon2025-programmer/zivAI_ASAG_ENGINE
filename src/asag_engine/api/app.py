from flask import Flask

from asag_engine.config import settings
from asag_engine.logging_setup import setup_logging
from asag_engine.api.routes import bp as grading_bp
from asag_engine.api.zivai_teacher_routes import bp_teacher

from asag_engine.api.zivai_content_routes import bp_zivai_content
from asag_engine.api.analytics_routes import bp as analytics_bp
from asag_engine.api.learning_plan_routes import bp_learning


def create_app() -> Flask:
    setup_logging()
    app = Flask(__name__)

    # Existing ASAG grading API
    app.register_blueprint(grading_bp)

    # New teacher assessments API
    app.register_blueprint(bp_teacher)

    # New content generation API
    app.register_blueprint(bp_zivai_content)

    app.register_blueprint(analytics_bp)

    app.register_blueprint(bp_learning)

    return app


def main():
    app = create_app()
    app.run(host=settings.host, port=settings.port, debug=(settings.env == "dev"))


if __name__ == "__main__":
    main()

