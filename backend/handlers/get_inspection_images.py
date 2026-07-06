"""Lambda handler for GET /inspections/{inspectionId}/images.

Lists all images associated with a given inspection.
"""

import logging

from backend.services import image_service
from backend.utils.exceptions import AppError, NotFoundError, ValidationError
from backend.utils.response import (
    error_response,
    internal_error_response,
    not_found_response,
    success_response,
)
from backend.utils.validators import get_path_parameter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict, context) -> dict:
    """Lambda entry point for listing inspection images.

    Path parameters:
        inspectionId: The inspection to list images for.

    Returns:
        200: List of images
        400: Validation error
        404: Inspection not found
        500: Internal server error
    """
    logger.info("GET /inspections/{inspectionId}/images")

    try:
        inspection_id = get_path_parameter(event, "inspectionId")

        images = image_service.get_inspection_images(inspection_id)

        return success_response({
            "inspectionId": inspection_id,
            "images": [img.to_dict() for img in images],
            "count": len(images),
        })

    except NotFoundError as exc:
        logger.warning("Not found: %s", exc.message)
        return not_found_response(exc.message)

    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc.message)
        return error_response(exc.message, status_code=400)

    except AppError as exc:
        logger.error("Application error: %s", exc.message)
        return error_response(exc.message, status_code=500)

    except Exception as exc:
        logger.exception("Unexpected error in get_inspection_images")
        return internal_error_response()
