"""S3 helper utility for generating pre-signed URLs.

Isolates all S3-specific logic so the service layer doesn't
need to import boto3 or know about S3 API details.
"""

import logging

import boto3
from botocore.exceptions import ClientError

from backend.config import settings
from backend.utils.exceptions import StorageError

logger = logging.getLogger(__name__)

# Initialize S3 client once per Lambda container
_s3_client = boto3.client("s3", region_name=settings.AWS_REGION)


def generate_presigned_upload_url(
    s3_key: str,
    content_type: str,
) -> str:
    """Generate a pre-signed PUT URL for direct S3 upload.

    The client uses this URL to upload the image directly to S3,
    bypassing Lambda entirely. This avoids the 6MB Lambda payload
    limit and reduces Lambda execution time.

    Args:
        s3_key: The S3 object key (e.g., 'inspections/abc/img-1.jpg').
        content_type: The MIME type the client must use when uploading.

    Returns:
        Pre-signed URL string.

    Raises:
        StorageError: If pre-signed URL generation fails.
    """
    try:
        url = _s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.IMAGES_BUCKET,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=settings.PRESIGNED_URL_EXPIRATION,
        )
        logger.info("Generated pre-signed URL for s3://%s/%s", settings.IMAGES_BUCKET, s3_key)
        return url
    except ClientError as exc:
        logger.error("Failed to generate pre-signed URL: %s", exc)
        raise StorageError("GeneratePresignedUrl", str(exc))
