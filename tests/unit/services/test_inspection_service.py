"""Unit tests for InspectionService.

Tests the business logic layer in isolation by mocking the repository.
This is the most important test layer — it verifies your business rules
without needing a real database.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Set env vars before importing any backend modules
os.environ["INSPECTIONS_TABLE"] = "test-inspections"
os.environ["IMAGES_TABLE"] = "test-images"
os.environ["IMAGES_BUCKET"] = "test-bucket"

from backend.models.inspection import Inspection, InspectionStatus
from backend.services import inspection_service
from backend.utils.exceptions import DatabaseError, NotFoundError


class TestCreateInspection(unittest.TestCase):
    """Tests for inspection_service.create_inspection()."""

    @patch("backend.services.inspection_service.inspection_repository")
    def test_create_inspection_success(self, mock_repo):
        """Should create an inspection with SCHEDULED status and UUID."""
        # Arrange: make repo return whatever is passed to it
        mock_repo.create_inspection.side_effect = lambda i: i

        # Act
        result = inspection_service.create_inspection(
            warehouse_id="W-001",
            drone_id="D-001",
        )

        # Assert
        self.assertIsInstance(result, Inspection)
        self.assertEqual(result.warehouse_id, "W-001")
        self.assertEqual(result.drone_id, "D-001")
        self.assertEqual(result.status, InspectionStatus.SCHEDULED)
        self.assertIsNotNone(result.inspection_id)
        self.assertTrue(len(result.inspection_id) == 36)  # UUID format

        # Verify repo was called exactly once
        mock_repo.create_inspection.assert_called_once()

    @patch("backend.services.inspection_service.inspection_repository")
    def test_create_inspection_generates_unique_ids(self, mock_repo):
        """Each inspection should get a unique UUID."""
        mock_repo.create_inspection.side_effect = lambda i: i

        result1 = inspection_service.create_inspection("W-001", "D-001")
        result2 = inspection_service.create_inspection("W-001", "D-001")

        self.assertNotEqual(result1.inspection_id, result2.inspection_id)

    @patch("backend.services.inspection_service.inspection_repository")
    def test_create_inspection_sets_timestamps(self, mock_repo):
        """Should set createdAt and updatedAt timestamps."""
        mock_repo.create_inspection.side_effect = lambda i: i

        result = inspection_service.create_inspection("W-001", "D-001")

        # Timestamps should be valid ISO format
        self.assertIsNotNone(result.created_at)
        self.assertIsNotNone(result.updated_at)
        # Verify they can be parsed
        datetime.fromisoformat(result.created_at)
        datetime.fromisoformat(result.updated_at)

    @patch("backend.services.inspection_service.inspection_repository")
    def test_create_inspection_database_error(self, mock_repo):
        """Should propagate DatabaseError from repository."""
        mock_repo.create_inspection.side_effect = DatabaseError("PutItem", "throttled")

        with self.assertRaises(DatabaseError) as ctx:
            inspection_service.create_inspection("W-001", "D-001")

        self.assertIn("PutItem", ctx.exception.message)


class TestGetWarehouseInspections(unittest.TestCase):
    """Tests for inspection_service.get_warehouse_inspections()."""

    @patch("backend.services.inspection_service.inspection_repository")
    def test_returns_inspections_list(self, mock_repo):
        """Should return list from repository."""
        mock_inspections = [
            Inspection("i-1", "W-001", "D-001"),
            Inspection("i-2", "W-001", "D-002"),
        ]
        mock_repo.get_inspections_by_warehouse.return_value = mock_inspections

        result = inspection_service.get_warehouse_inspections("W-001")

        self.assertEqual(len(result), 2)
        mock_repo.get_inspections_by_warehouse.assert_called_once_with("W-001")

    @patch("backend.services.inspection_service.inspection_repository")
    def test_returns_empty_list_for_unknown_warehouse(self, mock_repo):
        """Should return empty list, not raise error, for unknown warehouse."""
        mock_repo.get_inspections_by_warehouse.return_value = []

        result = inspection_service.get_warehouse_inspections("W-UNKNOWN")

        self.assertEqual(result, [])


class TestGetDroneInspections(unittest.TestCase):
    """Tests for inspection_service.get_drone_inspections()."""

    @patch("backend.services.inspection_service.inspection_repository")
    def test_returns_inspections_list(self, mock_repo):
        """Should return list from repository."""
        mock_inspections = [Inspection("i-1", "W-001", "D-001")]
        mock_repo.get_inspections_by_drone.return_value = mock_inspections

        result = inspection_service.get_drone_inspections("D-001")

        self.assertEqual(len(result), 1)
        mock_repo.get_inspections_by_drone.assert_called_once_with("D-001")


class TestGetInspection(unittest.TestCase):
    """Tests for inspection_service.get_inspection()."""

    @patch("backend.services.inspection_service.inspection_repository")
    def test_returns_inspection(self, mock_repo):
        """Should return inspection from repository."""
        mock_repo.get_inspection_by_id.return_value = Inspection("i-1", "W-001", "D-001")

        result = inspection_service.get_inspection("i-1")

        self.assertEqual(result.inspection_id, "i-1")

    @patch("backend.services.inspection_service.inspection_repository")
    def test_raises_not_found(self, mock_repo):
        """Should propagate NotFoundError."""
        mock_repo.get_inspection_by_id.side_effect = NotFoundError("Inspection", "bad-id")

        with self.assertRaises(NotFoundError):
            inspection_service.get_inspection("bad-id")


if __name__ == "__main__":
    unittest.main()
