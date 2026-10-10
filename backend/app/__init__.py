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

    # Security Guard: Prevent production booting with fallback or dev secrets
    if config_name == "production":
        insecure_keys = {
            "vetvision-ai-fallback-secret-key-32-chars",
            "vetvision-ai-jwt-fallback-secret-key",
            "vetvision-ai-dev-secret-key-super-secure-change-in-prod-2026",
            "vetvision-jwt-dev-secret-key-32-chars-long-secure",
            "change-this-to-a-very-secure-random-secret-key-in-production",
            "change-this-jwt-secret-key-to-a-secure-random-string",
        }
        secret_key = application.config.get("SECRET_KEY")
        jwt_key = application.config.get("JWT_SECRET_KEY")
        if not secret_key or secret_key in insecure_keys:
            raise ValueError("SECURITY CONFIGURATION ERROR: Production deployment requires a secure, non-default SECRET_KEY.")
        if not jwt_key or jwt_key in insecure_keys:
            raise ValueError("SECURITY CONFIGURATION ERROR: Production deployment requires a secure, non-default JWT_SECRET_KEY.")

    # Initialize extensions
    db.init_app(application)
    migrate.init_app(application, db)
    jwt.init_app(application)

    # Import models so Alembic and SQLAlchemy register metadata
    import app.models  # noqa: F401

    from app.config import parse_cors_origins

    # Configure CORS
    raw_cors = os.getenv("CORS_ORIGINS", application.config.get("CORS_ORIGINS", "*"))
    cors_origins = parse_cors_origins(raw_cors, env=config_name)
    application.config["CORS_ORIGINS"] = cors_origins
    cors.init_app(application, resources={r"/api/*": {"origins": cors_origins}})

    # Register CLI commands
    @application.cli.command("seed-db")
    def seed_db_command():
        """Seed symptom catalog and clinical follow-up question bank idempotently."""
        import click
        from app.models.symptom import seed_symptoms
        from app.models.question_bank import seed_follow_up_questions

        click.echo("Seeding clinical symptoms...")
        seeded_sym = seed_symptoms()
        click.echo(f"Clinical symptoms seeded: {seeded_sym}")

        click.echo("Seeding clinical follow-up questions...")
        seeded_q = seed_follow_up_questions()
        click.echo(f"Follow-up questions seeded: {seeded_q}")
        click.echo("Database seeding completed successfully.")

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
