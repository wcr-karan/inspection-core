"""Image service — business logic for image operations.

Orchestrates image upload URL generation and image listing.
Coordinates between the image repository (DynamoDB) and
the S3 helper (pre-signed URLs).
"""

import logging
import uuid
from pathlib import PurePosixPath

from backend.models.image import Image
from backend.repositories import image_repository
from backend.services import inspection_service
from backend.utils import s3_helper
from backend.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Allowed MIME types for image uploads
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
}


def generate_upload_url(
    inspection_id: str,
    file_name: str,
    content_type: str,
) -> dict:
    """Generate a pre-signed S3 URL for image upload.

    Flow:
    1. Verify the inspection exists (raises NotFoundError if not)
    2. Validate the content type
    3. Generate a unique image ID and S3 key
    4. Save image metadata to DynamoDB
    5. Generate and return the pre-signed URL

    Args:
        inspection_id: The inspection to attach the image to.
        file_name: Original file name from the client.
        content_type: MIME type (must be an allowed image type).

    Returns:
        Dict with uploadUrl, imageId, and s3Key.

    Raises:
        NotFoundError: If the inspection doesn't exist.
        ValidationError: If the content type is not allowed.
    """
    # Step 1: Verify inspection exists
    inspection_service.get_inspection(inspection_id)

    # Step 2: Validate content type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            f"Invalid content type: '{content_type}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
        )

    # Step 3: Generate unique image ID and S3 key
    image_id = str(uuid.uuid4())
    file_extension = PurePosixPath(file_name).suffix or ".jpg"
    s3_key = f"inspections/{inspection_id}/{image_id}{file_extension}"

    # Step 4: Save image metadata to DynamoDB
    image = Image(
        inspection_id=inspection_id,
        image_id=image_id,
        s3_key=s3_key,
        file_name=file_name,
        content_type=content_type,
    )
    image_repository.create_image(image)

    # Step 5: Generate pre-signed URL
    upload_url = s3_helper.generate_presigned_upload_url(s3_key, content_type)

    logger.info(
        "Generated upload URL for inspection %s, image %s",
        inspection_id,
        image_id,
    )

    return {
        "uploadUrl": upload_url,
        "imageId": image_id,
        "s3Key": s3_key,
    }


def get_inspection_images(inspection_id: str) -> list[Image]:
    """List all images for an inspection.

    Verifies the inspection exists before querying images.

    Args:
        inspection_id: The inspection to list images for.

    Returns:
        List of Image objects.

    Raises:
        NotFoundError: If the inspection doesn't exist.
    """
    # Verify inspection exists
    inspection_service.get_inspection(inspection_id)

    logger.info("Listing images for inspection %s", inspection_id)
    return image_repository.get_images_by_inspection(inspection_id)
