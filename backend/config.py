"""Root config alias for VetVision AI backend."""
from app.config import (
    BaseConfig,
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
    config_by_name,
)

__all__ = [
    "BaseConfig",
    "DevelopmentConfig",
    "TestingConfig",
    "ProductionConfig",
    "config_by_name",
]
