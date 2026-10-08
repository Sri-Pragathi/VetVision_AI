"""Routes blueprint registration."""
from flask import Flask, Blueprint
from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.pet_routes import pet_bp
from app.routes.symptom_routes import symptom_bp
from app.routes.assessment_routes import assessment_bp
# Step 3: Dynamic Question Engine
from app.routes.question_routes import question_bp
from app.routes.answer_routes import answer_bp


def register_routes(app: Flask) -> None:
    """Register all API v1 endpoints with the application."""
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    # Register sub-blueprints
    api_v1.register_blueprint(health_bp)
    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(user_bp)
    api_v1.register_blueprint(pet_bp)
    api_v1.register_blueprint(symptom_bp)
    api_v1.register_blueprint(assessment_bp)
    # Step 3
    api_v1.register_blueprint(question_bp)
    api_v1.register_blueprint(answer_bp)

    # Register root v1 blueprint with main app
    app.register_blueprint(api_v1)
