"""Image repository — DynamoDB operations for inspection images.

Handles all reads and writes to the Images DynamoDB table.
The Image table uses a composite key: inspectionId (PK) + imageId (SK),
which allows efficient queries for all images under an inspection.
"""

import logging

import boto3
from botocore.exceptions import ClientError

from backend.config import settings
from backend.models.image import Image
from backend.utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Initialize DynamoDB resource once per Lambda container
_dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
_table = _dynamodb.Table(settings.IMAGES_TABLE)


def create_image(image: Image) -> Image:
    """Write image metadata to DynamoDB.

    Called when a pre-signed upload URL is generated. The metadata
    is saved before the actual upload completes (see design doc Q3).

    Args:
        image: The Image metadata to persist.

    Returns:
        The same Image (confirming successful write).

    Raises:
        DatabaseError: If the DynamoDB PutItem operation fails.
    """
    try:
        _table.put_item(Item=image.to_dict())
        logger.info(
            "Created image %s for inspection %s",
            image.image_id,
            image.inspection_id,
        )
        return image
    except ClientError as exc:
        logger.error("Failed to create image: %s", exc)
        raise DatabaseError("CreateImage", str(exc))


def get_images_by_inspection(inspection_id: str) -> list[Image]:
    """Query all images for an inspection.

    Uses the composite key: inspectionId (PK) to retrieve all images.
    Results are sorted by imageId (SK) which provides consistent ordering.

    Args:
        inspection_id: The inspection to query images for.

    Returns:
        List of Image objects for this inspection.

    Raises:
        DatabaseError: If the DynamoDB Query operation fails.
    """
    try:
        response = _table.query(
            KeyConditionExpression="inspectionId = :iid",
            ExpressionAttributeValues={":iid": inspection_id},
        )
        logger.info(
            "Found %d images for inspection %s",
            response["Count"],
            inspection_id,
        )
        return [
            Image.from_dynamo_item(item)
            for item in response.get("Items", [])
        ]
    except ClientError as exc:
        logger.error(
            "Failed to query images for inspection %s: %s",
            inspection_id, exc,
        )
        raise DatabaseError("QueryInspectionImages", str(exc))
