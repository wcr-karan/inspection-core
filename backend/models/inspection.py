"""Inspection domain model.

Uses Python dataclasses — lightweight, stdlib, no external dependency.
Models are plain data containers. They hold NO business logic, NO AWS
imports, and NO database operations. They live at the bottom of the
dependency graph so every layer can import them safely.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class InspectionStatus(str, Enum):
    """Valid statuses for an inspection.

    Inheriting from str allows direct JSON serialization and
    comparison with string values from DynamoDB.
    """
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class Inspection:
    """Represents a drone inspection of a warehouse.

    Attributes:
        inspection_id: Unique identifier (UUID).
        warehouse_id: The warehouse being inspected.
        drone_id: The drone performing the inspection.
        status: Current inspection status.
        created_at: ISO 8601 timestamp of creation.
        updated_at: ISO 8601 timestamp of last update.
    """
    inspection_id: str
    warehouse_id: str
    drone_id: str
    status: InspectionStatus = InspectionStatus.SCHEDULED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """Convert to a plain dictionary for JSON serialization.

        Converts enum values to strings and uses camelCase keys
        to match the DynamoDB attribute names and API response format.
        """
        return {
            "inspectionId": self.inspection_id,
            "warehouseId": self.warehouse_id,
            "droneId": self.drone_id,
            "status": self.status.value,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "Inspection":
        """Create an Inspection from a DynamoDB item.

        DynamoDB stores attributes in camelCase. This factory method
        maps them to the dataclass's snake_case fields.
        """
        return cls(
            inspection_id=item["inspectionId"],
            warehouse_id=item["warehouseId"],
            drone_id=item["droneId"],
            status=InspectionStatus(item.get("status", "SCHEDULED")),
            created_at=item.get("createdAt", ""),
            updated_at=item.get("updatedAt", ""),
        )
