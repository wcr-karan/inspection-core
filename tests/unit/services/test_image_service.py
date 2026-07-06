"""Unit tests for ImageService.

Tests image upload URL generation and image listing logic
by mocking repositories and S3 helper.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

# Set env vars before importing backend modules
os.environ.setdefault("INSPECTIONS_TABLE", "test-inspections")
os.environ.setdefault("IMAGES_TABLE", "test-images")
os.environ.setdefault("IMAGES_BUCKET", "test-bucket")

from backend.models.image import Image
from backend.models.inspection import Inspection
from backend.services import image_service
from backend.utils.exceptions import NotFoundError, ValidationError


class TestGenerateUploadUrl(unittest.TestCase):
    """Tests for image_service.generate_upload_url()."""

    @patch("backend.services.image_service.s3_helper")
    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_generate_upload_url_success(self, mock_insp_svc, mock_img_repo, mock_s3):
        """Should generate URL, save metadata, and return result."""
        # Arrange
        mock_insp_svc.get_inspection.return_value = Inspection("i-1", "W-1", "D-1")
        mock_img_repo.create_image.side_effect = lambda img: img
        mock_s3.generate_presigned_upload_url.return_value = "https://s3.amazonaws.com/presigned"

        # Act
        result = image_service.generate_upload_url(
            inspection_id="i-1",
            file_name="photo.jpg",
            content_type="image/jpeg",
        )

        # Assert
        self.assertIn("uploadUrl", result)
        self.assertIn("imageId", result)
        self.assertIn("s3Key", result)
        self.assertEqual(result["uploadUrl"], "https://s3.amazonaws.com/presigned")
        self.assertTrue(result["s3Key"].startswith("inspections/i-1/"))
        self.assertTrue(result["s3Key"].endswith(".jpg"))

        # Verify all three dependencies were called
        mock_insp_svc.get_inspection.assert_called_once_with("i-1")
        mock_img_repo.create_image.assert_called_once()
        mock_s3.generate_presigned_upload_url.assert_called_once()

    @patch("backend.services.image_service.s3_helper")
    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_generate_upload_url_inspection_not_found(self, mock_insp_svc, mock_img_repo, mock_s3):
        """Should raise NotFoundError when inspection doesn't exist."""
        mock_insp_svc.get_inspection.side_effect = NotFoundError("Inspection", "bad-id")

        with self.assertRaises(NotFoundError):
            image_service.generate_upload_url("bad-id", "photo.jpg", "image/jpeg")

        # Image repo and S3 should NOT be called
        mock_img_repo.create_image.assert_not_called()
        mock_s3.generate_presigned_upload_url.assert_not_called()

    @patch("backend.services.image_service.s3_helper")
    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_invalid_content_type(self, mock_insp_svc, mock_img_repo, mock_s3):
        """Should raise ValidationError for unsupported content types."""
        mock_insp_svc.get_inspection.return_value = Inspection("i-1", "W-1", "D-1")

        with self.assertRaises(ValidationError) as ctx:
            image_service.generate_upload_url("i-1", "doc.pdf", "application/pdf")

        self.assertIn("application/pdf", ctx.exception.message)
        mock_img_repo.create_image.assert_not_called()

    @patch("backend.services.image_service.s3_helper")
    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_preserves_file_extension(self, mock_insp_svc, mock_img_repo, mock_s3):
        """S3 key should preserve the original file extension."""
        mock_insp_svc.get_inspection.return_value = Inspection("i-1", "W-1", "D-1")
        mock_img_repo.create_image.side_effect = lambda img: img
        mock_s3.generate_presigned_upload_url.return_value = "https://url"

        result = image_service.generate_upload_url("i-1", "scan.png", "image/png")
        self.assertTrue(result["s3Key"].endswith(".png"))

        result = image_service.generate_upload_url("i-1", "scan.webp", "image/webp")
        self.assertTrue(result["s3Key"].endswith(".webp"))


class TestGetInspectionImages(unittest.TestCase):
    """Tests for image_service.get_inspection_images()."""

    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_returns_images_list(self, mock_insp_svc, mock_img_repo):
        """Should return list of images for the inspection."""
        mock_insp_svc.get_inspection.return_value = Inspection("i-1", "W-1", "D-1")
        mock_images = [
            Image("i-1", "img-1", "s3key1", "a.jpg", "image/jpeg"),
            Image("i-1", "img-2", "s3key2", "b.png", "image/png"),
        ]
        mock_img_repo.get_images_by_inspection.return_value = mock_images

        result = image_service.get_inspection_images("i-1")

        self.assertEqual(len(result), 2)
        mock_insp_svc.get_inspection.assert_called_once_with("i-1")

    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_inspection_not_found(self, mock_insp_svc, mock_img_repo):
        """Should raise NotFoundError when inspection doesn't exist."""
        mock_insp_svc.get_inspection.side_effect = NotFoundError("Inspection", "bad-id")

        with self.assertRaises(NotFoundError):
            image_service.get_inspection_images("bad-id")

        mock_img_repo.get_images_by_inspection.assert_not_called()

    @patch("backend.services.image_service.image_repository")
    @patch("backend.services.image_service.inspection_service")
    def test_returns_empty_list(self, mock_insp_svc, mock_img_repo):
        """Should return empty list when no images exist."""
        mock_insp_svc.get_inspection.return_value = Inspection("i-1", "W-1", "D-1")
        mock_img_repo.get_images_by_inspection.return_value = []

        result = image_service.get_inspection_images("i-1")

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
