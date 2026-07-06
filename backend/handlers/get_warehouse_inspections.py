"""Lambda handler for GET /warehouses/{warehouseId}/inspections.

Lists all inspections for a given warehouse, sorted newest first.
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
    """Lambda entry point for listing warehouse inspections."""
    logger.info("GET /warehouses/{warehouseId}/inspections")

    warehouse_id = get_path_parameter(event, "warehouseId")
    inspections = inspection_service.get_warehouse_inspections(warehouse_id)

    return success_response({
        "warehouseId": warehouse_id,
        "inspections": [i.to_dict() for i in inspections],
        "count": len(inspections),
    })
