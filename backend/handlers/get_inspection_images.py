"""Lambda handler for GET /inspections/{inspectionId}/images.

Lists all images associated with a given inspection.
"""

import logging

from backend.services import image_service
from backend.utils.decorator import lambda_handler
from backend.utils.response import success_response
from backend.utils.validators import get_path_parameter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lambda_handler
def handler(event: dict, context) -> dict:
    """Lambda entry point for listing inspection images."""
    logger.info("GET /inspections/{inspectionId}/images")

    inspection_id = get_path_parameter(event, "inspectionId")
    images = image_service.get_inspection_images(inspection_id)

    return success_response({
        "inspectionId": inspection_id,
        "images": [img.to_dict() for img in images],
        "count": len(images),
    })
