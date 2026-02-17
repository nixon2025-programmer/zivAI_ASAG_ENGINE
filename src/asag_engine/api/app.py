from flask import Flask
from asag_engine.config import settings
from asag_engine.logging_setup import setup_logging
from asag_engine.api.routes import bp

def create_app() -> Flask:
    setup_logging()
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app

def main():
    app = create_app()
    app.run(host=settings.host, port=settings.port, debug=(settings.env == "dev"))

if __name__ == "__main__":
    main()
