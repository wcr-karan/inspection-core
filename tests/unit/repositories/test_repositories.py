"""Unit tests for the repository layer (inspection_repository and image_repository).

Uses moto to mock AWS DynamoDB so we can test the repository CRUD operations
and query logic against a real local-in-memory DynamoDB database structure.
"""

import os
import unittest
import boto3
from botocore.exceptions import ClientError

# Set environment variables before any module import
os.environ["INSPECTIONS_TABLE"] = "test-inspections"
os.environ["IMAGES_TABLE"] = "test-images"
os.environ["IMAGES_BUCKET"] = "test-bucket"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from moto import mock_aws

# Import models
from backend.models.inspection import Inspection, InspectionStatus
from backend.models.image import Image
from backend.utils.exceptions import DatabaseError, NotFoundError


@mock_aws
class TestRepositories(unittest.TestCase):
    """Test suite for Inspection and Image repositories using mocked DynamoDB."""

    def setUp(self) -> None:
        """Set up mocked DynamoDB tables before each test."""
        self.db = boto3.resource("dynamodb", region_name="us-east-1")

        # 1. Create Inspections Table
        self.inspections_table = self.db.create_table(
            TableName="test-inspections",
            KeySchema=[{"AttributeName": "inspectionId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "inspectionId", "AttributeType": "S"},
                {"AttributeName": "warehouseId", "AttributeType": "S"},
                {"AttributeName": "droneId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "warehouseId-createdAt-index",
                    "KeySchema": [
                        {"AttributeName": "warehouseId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "droneId-createdAt-index",
                    "KeySchema": [
                        {"AttributeName": "droneId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        # 2. Create Images Table
        self.images_table = self.db.create_table(
            TableName="test-images",
            KeySchema=[
                {"AttributeName": "inspectionId", "KeyType": "HASH"},
                {"AttributeName": "imageId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "inspectionId", "AttributeType": "S"},
                {"AttributeName": "imageId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        # Now import repositories *after* the mock has started and tables are created.
        # This ensures the boto3 resources inside the repositories bind to the mocked environment.
        from backend.repositories import inspection_repository, image_repository
        self.inspection_repo = inspection_repository
        self.image_repo = image_repository

        # Re-bind the tables inside the repository modules to the mocked tables
        self.inspection_repo._table = self.inspections_table
        self.image_repo._table = self.images_table

    def tearDown(self) -> None:
        """Clean up tables."""
        try:
            self.inspections_table.delete()
        except Exception:
            pass
        try:
            self.images_table.delete()
        except Exception:
            pass

    # =========================================================================
    # Inspection Repository Tests
    # =========================================================================

    def test_create_and_get_inspection(self):
        """Should save inspection to table and retrieve it correctly by ID."""
        inspection = Inspection(
            inspection_id="insp-123",
            warehouse_id="WH-1",
            drone_id="DR-1",
            status=InspectionStatus.SCHEDULED,
            created_at="2026-07-06T12:00:00Z",
            updated_at="2026-07-06T12:00:00Z"
        )

        # Create
        created = self.inspection_repo.create_inspection(inspection)
        self.assertEqual(created.inspection_id, "insp-123")

        # Get
        retrieved = self.inspection_repo.get_inspection_by_id("insp-123")
        self.assertEqual(retrieved.inspection_id, "insp-123")
        self.assertEqual(retrieved.warehouse_id, "WH-1")
        self.assertEqual(retrieved.drone_id, "DR-1")
        self.assertEqual(retrieved.status, InspectionStatus.SCHEDULED)
        self.assertEqual(retrieved.created_at, "2026-07-06T12:00:00Z")

    def test_get_inspection_not_found(self):
        """Should raise NotFoundError for non-existent inspection."""
        with self.assertRaises(NotFoundError) as ctx:
            self.inspection_repo.get_inspection_by_id("invalid-id")
        self.assertIn("Inspection not found: invalid-id", str(ctx.exception))

    def test_get_inspections_by_warehouse(self):
        """Should query inspections for a specific warehouse sorted newest first."""
        insp1 = Inspection("i-1", "WH-1", "DR-1", created_at="2026-07-06T10:00:00Z")
        insp2 = Inspection("i-2", "WH-1", "DR-2", created_at="2026-07-06T11:00:00Z")
        insp3 = Inspection("i-3", "WH-2", "DR-1", created_at="2026-07-06T12:00:00Z")

        self.inspection_repo.create_inspection(insp1)
        self.inspection_repo.create_inspection(insp2)
        self.inspection_repo.create_inspection(insp3)

        results = self.inspection_repo.get_inspections_by_warehouse("WH-1")

        # Verify count
        self.assertEqual(len(results), 2)
        # Verify ordering (newest first - ScanIndexForward=False)
        self.assertEqual(results[0].inspection_id, "i-2")
        self.assertEqual(results[1].inspection_id, "i-1")

    def test_get_inspections_by_drone(self):
        """Should query inspections for a specific drone sorted newest first."""
        insp1 = Inspection("i-1", "WH-1", "DR-1", created_at="2026-07-06T10:00:00Z")
        insp2 = Inspection("i-2", "WH-2", "DR-1", created_at="2026-07-06T11:00:00Z")
        insp3 = Inspection("i-3", "WH-1", "DR-2", created_at="2026-07-06T12:00:00Z")

        self.inspection_repo.create_inspection(insp1)
        self.inspection_repo.create_inspection(insp2)
        self.inspection_repo.create_inspection(insp3)

        results = self.inspection_repo.get_inspections_by_drone("DR-1")

        # Verify count
        self.assertEqual(len(results), 2)
        # Verify ordering (newest first)
        self.assertEqual(results[0].inspection_id, "i-2")
        self.assertEqual(results[1].inspection_id, "i-1")

    def test_inspection_repo_client_error(self):
        """Should raise DatabaseError when a client error is encountered."""
        # Cause client error by deleting table and attempting write
        self.inspections_table.delete()

        inspection = Inspection("i-err", "WH-1", "DR-1")
        with self.assertRaises(DatabaseError) as ctx:
            self.inspection_repo.create_inspection(inspection)
        self.assertIn("CreateInspection", ctx.exception.operation)

    # =========================================================================
    # Image Repository Tests
    # =========================================================================

    def test_create_and_get_images(self):
        """Should save image metadata and query images by inspection ID."""
        image1 = Image(
            inspection_id="insp-1",
            image_id="img-1",
            s3_key="inspections/insp-1/img-1.jpg",
            file_name="img-1.jpg",
            content_type="image/jpeg",
            uploaded_at="2026-07-06T12:00:00Z"
        )
        image2 = Image(
            inspection_id="insp-1",
            image_id="img-2",
            s3_key="inspections/insp-1/img-2.jpg",
            file_name="img-2.jpg",
            content_type="image/jpeg",
            uploaded_at="2026-07-06T12:05:00Z"
        )
        image3 = Image(
            inspection_id="insp-2",
            image_id="img-3",
            s3_key="inspections/insp-2/img-3.jpg",
            file_name="img-3.jpg",
            content_type="image/jpeg",
            uploaded_at="2026-07-06T12:10:00Z"
        )

        self.image_repo.create_image(image1)
        self.image_repo.create_image(image2)
        self.image_repo.create_image(image3)

        # Query
        results = self.image_repo.get_images_by_inspection("insp-1")

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].image_id, "img-1")
        self.assertEqual(results[1].image_id, "img-2")

    def test_image_repo_client_error(self):
        """Should raise DatabaseError when client error occurs during image operations."""
        self.images_table.delete()

        image = Image("insp-1", "img-1", "s3key", "file.jpg", "image/jpeg")
        with self.assertRaises(DatabaseError) as ctx:
            self.image_repo.create_image(image)
        self.assertIn("CreateImage", ctx.exception.operation)


if __name__ == "__main__":
    unittest.main()
