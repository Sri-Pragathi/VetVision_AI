"""Tests for CORS parsing and cross-origin security enforcement."""
import pytest
from app import create_app
from app.config import parse_cors_origins


def test_parse_cors_origins_single_and_multiple():
    """Verify parsing single and multiple comma-separated origins with whitespace."""
    # Single origin
    res1 = parse_cors_origins("http://localhost:3000", env="development")
    assert res1 == ["http://localhost:3000"]

    # Multiple origins with varying whitespace
    res2 = parse_cors_origins("http://localhost:3000,  https://vetvision.app  , http://127.0.0.1:3000 ", env="development")
    assert res2 == ["http://localhost:3000", "https://vetvision.app", "http://127.0.0.1:3000"]

    # List input
    res3 = parse_cors_origins(["http://localhost:3000", " https://vetvision.app "], env="development")
    assert res3 == ["http://localhost:3000", "https://vetvision.app"]


def test_parse_cors_origins_empty_and_fallback():
    """Verify development falls back safely to wildcard, whereas production rejects empty/missing."""
    # Development fallbacks
    assert parse_cors_origins(None, env="development") == "*"
    assert parse_cors_origins("", env="development") == "*"
    assert parse_cors_origins("   ", env="development") == "*"
    assert parse_cors_origins("*", env="development") == "*"

    # Production rejects missing, empty, or whitespace-only
    with pytest.raises(ValueError, match="SECURITY CONFIGURATION ERROR"):
        parse_cors_origins(None, env="production")

    with pytest.raises(ValueError, match="SECURITY CONFIGURATION ERROR"):
        parse_cors_origins("", env="production")

    with pytest.raises(ValueError, match="SECURITY CONFIGURATION ERROR"):
        parse_cors_origins("   ", env="production")

    # Production rejects wildcard
    with pytest.raises(ValueError, match=r"Wildcard '\*' CORS origin is not permitted in production"):
        parse_cors_origins("*", env="production")

    with pytest.raises(ValueError, match=r"Wildcard '\*' CORS origin is not permitted in production"):
        parse_cors_origins("https://app.vetvision.com, *", env="production")


def test_cors_headers_with_allowed_and_unpermitted_origins(monkeypatch):
    """Verify Flask-Cors headers are properly applied to allowed origins and rejected on unpermitted origins."""
    app = create_app("testing")

    with app.test_client() as client:
        # Default testing allows wildcard * (Flask-Cors echoes back the Origin or *)
        res = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
        assert res.status_code == 200
        assert res.headers.get("Access-Control-Allow-Origin") in ["*", "http://localhost:3000"]

    # Test with explicit restricted origins list
    monkeypatch.setenv("CORS_ORIGINS", "https://authorized.vetvision.app, https://partner.vetvision.app")
    app_restricted = create_app("testing")

    with app_restricted.test_client() as client:
        # 1. First authorized origin
        res1 = client.get("/api/v1/health", headers={"Origin": "https://authorized.vetvision.app"})
        assert res1.status_code == 200
        assert res1.headers.get("Access-Control-Allow-Origin") == "https://authorized.vetvision.app"

        # 2. Second authorized origin
        res2 = client.get("/api/v1/health", headers={"Origin": "https://partner.vetvision.app"})
        assert res2.status_code == 200
        assert res2.headers.get("Access-Control-Allow-Origin") == "https://partner.vetvision.app"

        # 3. Unpermitted origin: Access-Control-Allow-Origin must NOT be present
        res_evil = client.get("/api/v1/health", headers={"Origin": "https://malicious-site.com"})
        assert res_evil.status_code == 200
        assert res_evil.headers.get("Access-Control-Allow-Origin") is None
