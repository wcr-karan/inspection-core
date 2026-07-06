"""Lambda handler for POST /inspections.

Creates a new drone inspection. This handler demonstrates the
standard pattern all handlers follow:

1. Parse the request body
2. Validate required fields
3. Call the service layer
4. Return a standardized response
5. Catch known exceptions → proper HTTP status
6. Catch unknown exceptions → 500 with generic message
"""

import logging

from backend.services import inspection_service
from backend.utils.exceptions import AppError, ValidationError
from backend.utils.response import created_response, error_response, internal_error_response
from backend.utils.validators import parse_request_body, validate_required_fields

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict, context) -> dict:
    """Lambda entry point for creating an inspection.

    Expected request body:
        {
            "warehouseId": "string",
            "droneId": "string"
        }

    Returns:
        201: Created inspection
        400: Validation error
        500: Internal server error
    """
    logger.info("POST /inspections - Creating new inspection")

    try:
        # 1. Parse request
        body = parse_request_body(event)

        # 2. Validate
        validate_required_fields(body, ["warehouseId", "droneId"])

        # 3. Call service
        inspection = inspection_service.create_inspection(
            warehouse_id=body["warehouseId"],
            drone_id=body["droneId"],
        )

        # 4. Return response
        logger.info("Inspection created: %s", inspection.inspection_id)
        return created_response(inspection.to_dict())

    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.message)
        return error_response(exc.message, status_code=400)

    except AppError as exc:
        logger.error("Application error: %s", exc.message)
        return error_response(exc.message, status_code=500)

    except Exception as exc:
        logger.exception("Unexpected error in create_inspection")
        return internal_error_response()
