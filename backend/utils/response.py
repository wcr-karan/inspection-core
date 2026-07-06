"""Standardized API response builders.

Every Lambda handler uses these functions to return consistent JSON responses.
This ensures the API never returns inconsistent response shapes — a common
problem in serverless projects where each handler is a separate function.

Response format:
    Success: {"success": true, "data": {...}}
    Error:   {"success": false, "message": "...", "error": "..."}
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def success_response(data: Any, status_code: int = 200) -> dict:
    """Build a standardized success response.

    Args:
        data: The response payload. Can be a dict, list, or any
              JSON-serializable value.
        status_code: HTTP status code. Defaults to 200.

    Returns:
        API Gateway-compatible response dict.
    """
    return {
        "statusCode": status_code,
        "headers": _default_headers(),
        "body": json.dumps({
            "success": True,
            "data": data,
        }),
    }


def created_response(data: Any) -> dict:
    """Build a 201 Created response.

    Used after successfully creating a new resource (e.g., POST /inspections).

    Args:
        data: The created resource.

    Returns:
        API Gateway-compatible response dict with 201 status.
    """
    return success_response(data, status_code=201)


def error_response(
    message: str,
    status_code: int = 400,
    error: Optional[str] = None,
) -> dict:
    """Build a standardized error response.

    Args:
        message: Human-readable error message for the API consumer.
        status_code: HTTP status code. Defaults to 400.
        error: Optional technical error detail (e.g., exception class name).

    Returns:
        API Gateway-compatible response dict.
    """
    body = {
        "success": False,
        "message": message,
    }

    if error:
        body["error"] = error

    return {
        "statusCode": status_code,
        "headers": _default_headers(),
        "body": json.dumps(body),
    }


def not_found_response(message: str = "Resource not found") -> dict:
    """Build a 404 Not Found response."""
    return error_response(message, status_code=404)


def internal_error_response(
    message: str = "An internal error occurred",
) -> dict:
    """Build a 500 Internal Server Error response.

    Note: Never expose internal details (stack traces, table names) in the
    message. Log them instead and return a generic message to the client.
    """
    return error_response(message, status_code=500)


def _default_headers() -> dict:
    """Default response headers applied to every response.

    Includes CORS headers for browser-based API consumers and
    Content-Type for JSON responses.
    """
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }
