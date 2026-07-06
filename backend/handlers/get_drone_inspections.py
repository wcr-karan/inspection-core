"""Lambda handler for GET /drones/{droneId}/inspections.

Lists all inspections for a given drone, sorted newest first.
"""

import logging

from backend.services import inspection_service
from backend.utils.exceptions import AppError, ValidationError
from backend.utils.response import error_response, internal_error_response, success_response
from backend.utils.validators import get_path_parameter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict, context) -> dict:
    """Lambda entry point for listing drone inspections.

    Path parameters:
        droneId: The drone to list inspections for.

    Returns:
        200: List of inspections
        400: Validation error
        500: Internal server error
    """
    logger.info("GET /drones/{droneId}/inspections")

    try:
        drone_id = get_path_parameter(event, "droneId")

        inspections = inspection_service.get_drone_inspections(drone_id)

        return success_response({
            "droneId": drone_id,
            "inspections": [i.to_dict() for i in inspections],
            "count": len(inspections),
        })

    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.message)
        return error_response(exc.message, status_code=400)

    except AppError as exc:
        logger.error("Application error: %s", exc.message)
        return error_response(exc.message, status_code=500)

    except Exception as exc:
        logger.exception("Unexpected error in get_drone_inspections")
        return internal_error_response()
