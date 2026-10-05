"""Standardized JSON API response helpers for VetVision AI."""
from typing import Any, Optional, Dict
from flask import jsonify, Response


def success_response(
    data: Optional[Any] = None,
    message: str = "Success",
    status_code: int = 200,
) -> tuple[Response, int]:
    """Generate a consistent JSON success response.
    
    Format:
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    """
    payload: Dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data

    return jsonify(payload), status_code


def error_response(
    message: str = "An error occurred",
    errors: Optional[Any] = None,
    status_code: int = 400,
) -> tuple[Response, int]:
    """Generate a consistent JSON error response.
    
    Format:
    {
        "success": false,
        "message": "...",
        "errors": { ... }
    }
    """
    payload: Dict[str, Any] = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        payload["errors"] = errors

    return jsonify(payload), status_code
