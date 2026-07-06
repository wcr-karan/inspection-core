"""Image domain model.

Represents metadata about an image uploaded for a drone inspection.
The actual image binary lives in S3; this model tracks the metadata
stored in DynamoDB.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Image:
    """Represents an image associated with an inspection.

    Attributes:
        inspection_id: The inspection this image belongs to.
        image_id: Unique identifier for this image (UUID).
        s3_key: The S3 object key where the image is stored.
        file_name: Original file name provided by the client.
        content_type: MIME type (e.g., 'image/jpeg').
        uploaded_at: ISO 8601 timestamp of metadata creation.
    """
    inspection_id: str
    image_id: str
    s3_key: str
    file_name: str
    content_type: str
    uploaded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Convert to a plain dictionary for JSON serialization."""
        return {
            "inspectionId": self.inspection_id,
            "imageId": self.image_id,
            "s3Key": self.s3_key,
            "fileName": self.file_name,
            "contentType": self.content_type,
            "uploadedAt": self.uploaded_at,
        }

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "Image":
        """Create an Image from a DynamoDB item."""
        return cls(
            inspection_id=item["inspectionId"],
            image_id=item["imageId"],
            s3_key=item["s3Key"],
            file_name=item["fileName"],
            content_type=item["contentType"],
            uploaded_at=item.get("uploadedAt", ""),
        )
