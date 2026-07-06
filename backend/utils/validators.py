"""Reusable request validation utilities.

Centralizes input validation logic so handlers stay thin.
Every validation function raises ValidationError on failure,
which handlers catch and convert to a 400 response.
"""

import json
import logging
from typing import Any, Optional

from backend.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


def parse_request_body(event: dict) -> dict:
    """Parse and validate the JSON body from an API Gateway event.

    Args:
        event: The Lambda event from API Gateway.

    Returns:
        Parsed body as a dictionary.

    Raises:
        ValidationError: If body is missing or not valid JSON.
    """
    body = event.get("body")

    if not body:
        raise ValidationError("Request body is required")

    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid JSON in request body: %s", exc)
        raise ValidationError("Request body must be valid JSON")

    if not isinstance(parsed, dict):
        raise ValidationError("Request body must be a JSON object")

    return parsed


def get_path_parameter(event: dict, param_name: str) -> str:
    """Extract and validate a path parameter from an API Gateway event.

    Args:
        event: The Lambda event from API Gateway.
        param_name: The name of the path parameter (e.g., 'warehouseId').

    Returns:
        The parameter value as a string.

    Raises:
        ValidationError: If the parameter is missing or empty.
    """
    params = event.get("pathParameters") or {}
    value = params.get(param_name, "").strip()

    if not value:
        raise ValidationError(f"Path parameter '{param_name}' is required")

    return value


def validate_required_fields(data: dict, required_fields: list[str]) -> None:
    """Validate that all required fields are present and non-empty.

    Args:
        data: The parsed request body.
        required_fields: List of field names that must be present.

    Raises:
        ValidationError: If any required field is missing or empty.
    """
    missing = []

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)

    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )


def validate_allowed_values(
    value: Any,
    field_name: str,
    allowed_values: list,
) -> None:
    """Validate that a value is one of the allowed options.

    Args:
        value: The value to check.
        field_name: The field name (for error messages).
        allowed_values: List of acceptable values.

    Raises:
        ValidationError: If value is not in allowed_values.
    """
    if value not in allowed_values:
        raise ValidationError(
            f"Invalid value for '{field_name}': '{value}'. "
            f"Allowed values: {', '.join(str(v) for v in allowed_values)}"
        )


def get_query_parameter(
    event: dict,
    param_name: str,
    default: Optional[str] = None,
) -> Optional[str]:
    """Extract an optional query string parameter.

    Args:
        event: The Lambda event from API Gateway.
        param_name: The query parameter name.
        default: Default value if parameter is not present.

    Returns:
        The parameter value or the default.
    """
    params = event.get("queryStringParameters") or {}
    return params.get(param_name, default)
