"""Lambda handler for POST /inspections.

Creates a new drone inspection. Uses the @lambda_handler decorator
for centralized error handling — the handler only contains the happy path.
"""

import logging

from backend.services import inspection_service
from backend.utils.decorator import lambda_handler
from backend.utils.response import created_response
from backend.utils.validators import parse_request_body, validate_required_fields

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lambda_handler
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

    body = parse_request_body(event)
    validate_required_fields(body, ["warehouseId", "droneId"])

    inspection = inspection_service.create_inspection(
        warehouse_id=body["warehouseId"],
        drone_id=body["droneId"],
    )

    logger.info("Inspection created: %s", inspection.inspection_id)
    return created_response(inspection.to_dict())
