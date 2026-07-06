"""Lambda handler for GET /drones/{droneId}/inspections.

Lists all inspections for a given drone, sorted newest first.
"""

import logging

from backend.services import inspection_service
from backend.utils.decorator import lambda_handler
from backend.utils.response import success_response
from backend.utils.validators import get_path_parameter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lambda_handler
def handler(event: dict, context) -> dict:
    """Lambda entry point for listing drone inspections."""
    logger.info("GET /drones/{droneId}/inspections")

    drone_id = get_path_parameter(event, "droneId")
    inspections = inspection_service.get_drone_inspections(drone_id)

    return success_response({
        "droneId": drone_id,
        "inspections": [i.to_dict() for i in inspections],
        "count": len(inspections),
    })
