"""Application factory for VetVision AI backend."""
import os
from typing import Optional
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors
from app.routes import register_routes
from app.utils.error_handlers import register_error_handlers


def create_app(config_name: Optional[str] = None) -> Flask:
    """Construct and configure the Flask application instance."""
    application = Flask(__name__)

    # Determine configuration mode
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    config_class = config_by_name.get(config_name, config_by_name["development"])
    application.config.from_object(config_class)

    # Initialize extensions
    db.init_app(application)
    migrate.init_app(application, db)
    jwt.init_app(application)

    # Import models so Alembic and SQLAlchemy register metadata
    import app.models  # noqa: F401

    # Configure CORS
    cors_origins = application.config.get("CORS_ORIGINS", "*")
    cors.init_app(application, resources={r"/api/*": {"origins": cors_origins}})

    # JWT Token blocklist callback for logout checking
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
        from app.models.token_blocklist import TokenBlocklist
        jti = jwt_payload.get("jti")
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None

    # Register centralized error handlers
    register_error_handlers(application)

    # Register all API v1 routes
    register_routes(application)

    return application
