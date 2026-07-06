"""Lambda handler for POST /inspections/{inspectionId}/upload-url.

Generates a pre-signed S3 URL so the client can upload an image
directly to S3 without routing the binary through Lambda.
"""

import logging

from backend.services import image_service
from backend.utils.decorator import lambda_handler
from backend.utils.response import created_response
from backend.utils.validators import (
    get_path_parameter,
    parse_request_body,
    validate_required_fields,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lambda_handler
def handler(event: dict, context) -> dict:
    """Lambda entry point for generating an upload URL.

    Path parameters:
        inspectionId: The inspection to attach the image to.

    Expected request body:
        {
            "fileName": "photo.jpg",
            "contentType": "image/jpeg"
        }

    Returns:
        201: Upload URL, imageId, and s3Key
        400: Validation error
        404: Inspection not found
        500: Internal server error
    """
    logger.info("POST /inspections/{inspectionId}/upload-url")

    inspection_id = get_path_parameter(event, "inspectionId")
    body = parse_request_body(event)
    validate_required_fields(body, ["fileName", "contentType"])

    result = image_service.generate_upload_url(
        inspection_id=inspection_id,
        file_name=body["fileName"],
        content_type=body["contentType"],
    )

    logger.info("Upload URL generated for inspection %s", inspection_id)
    return created_response(result)
