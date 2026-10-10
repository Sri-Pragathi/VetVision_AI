"""Configuration management for VetVision AI Backend."""
import os
from datetime import timedelta
from pathlib import Path
from typing import Union, List, Any, Optional
from dotenv import load_dotenv

# Load .env file from backend root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def parse_cors_origins(raw_origins: Any, env: str = "development") -> Union[List[str], str]:
    """Parse comma-separated CORS_ORIGINS into a clean list of allowed origins.

    - In development/testing: falls back to '*' if unset, empty, or whitespace.
    - In production: strictly enforces explicit non-wildcard origins, raising
      ValueError on missing, empty, or wildcard configurations.
    """
    if raw_origins is None:
        if env == "production":
            raise ValueError(
                "SECURITY CONFIGURATION ERROR: Production deployment requires explicit, non-empty CORS_ORIGINS."
            )
        return "*"

    if isinstance(raw_origins, (list, tuple, set)):
        origins = [str(o).strip() for o in raw_origins if str(o).strip()]
    elif isinstance(raw_origins, str):
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    else:
        origins = []

    if not origins:
        if env == "production":
            raise ValueError(
                "SECURITY CONFIGURATION ERROR: Production deployment requires non-empty CORS_ORIGINS."
            )
        return "*"

    if "*" in origins:
        if env == "production":
            raise ValueError(
                "SECURITY CONFIGURATION ERROR: Wildcard '*' CORS origin is not permitted in production."
            )
        return "*"

    return origins


def get_database_url() -> str:
    """Retrieve database URL from environment with fallback and fix legacy prefixes."""
    url = os.getenv("DATABASE_URL")
    if not url:
        # Fallback to local SQLite file in backend directory for instant dev
        db_path = BASE_DIR / "vetvision_dev.db"
        return f"sqlite:///{db_path}"
    # Compatibility fix for older postgres:// URI schemas used by some providers
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class BaseConfig:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "vetvision-ai-fallback-secret-key-32-chars")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True

    # JWT Settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "vetvision-ai-jwt-fallback-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "60"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )
    JWT_ERROR_MESSAGE_KEY = "message"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Media / Image Upload Configuration
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))  # 10 MB limit
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_IMAGE_MIMETYPES = {"image/jpeg", "image/png", "image/webp"}


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    ENV = "development"
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = get_database_url()


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    ENV = "testing"
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key-minimum-32-chars-secure-vetvision"
    SECRET_KEY = "test-app-secret-key-minimum-32-chars-secure-vetvision"
    # Shorter expiry for fast testing if needed
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
    UPLOAD_FOLDER = str(BASE_DIR / "test_uploads")


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    ENV = "production"
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = get_database_url()


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
