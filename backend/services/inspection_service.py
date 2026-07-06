"""Inspection service — business logic for inspection operations.

This is the orchestration layer. It:
- Receives validated input from handlers
- Applies business rules
- Calls repositories for data access
- Returns domain objects

The service layer is where you'd add things like:
- Checking if a warehouse/drone combination is valid
- Enforcing limits on concurrent inspections
- Sending notifications when inspections are created
- Business rule validation beyond simple input validation
"""

import logging
import uuid
from datetime import datetime, timezone

from backend.models.inspection import Inspection, InspectionStatus
from backend.repositories import inspection_repository

logger = logging.getLogger(__name__)


def create_inspection(warehouse_id: str, drone_id: str) -> Inspection:
    """Create a new drone inspection.

    Business rules applied:
    - Generate a unique inspection ID (UUID v4)
    - Set initial status to SCHEDULED
    - Record creation timestamp

    Args:
        warehouse_id: The warehouse to inspect.
        drone_id: The drone that will perform the inspection.

    Returns:
        The created Inspection with all fields populated.
    """
    inspection = Inspection(
        inspection_id=str(uuid.uuid4()),
        warehouse_id=warehouse_id,
        drone_id=drone_id,
        status=InspectionStatus.SCHEDULED,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )

    logger.info(
        "Creating inspection %s: warehouse=%s, drone=%s",
        inspection.inspection_id,
        warehouse_id,
        drone_id,
    )

    return inspection_repository.create_inspection(inspection)


def get_warehouse_inspections(warehouse_id: str) -> list[Inspection]:
    """Get all inspections for a warehouse.

    Args:
        warehouse_id: The warehouse to list inspections for.

    Returns:
        List of inspections, sorted newest first.
    """
    logger.info("Listing inspections for warehouse %s", warehouse_id)
    return inspection_repository.get_inspections_by_warehouse(warehouse_id)


def get_drone_inspections(drone_id: str) -> list[Inspection]:
    """Get all inspections for a drone.

    Args:
        drone_id: The drone to list inspections for.

    Returns:
        List of inspections, sorted newest first.
    """
    logger.info("Listing inspections for drone %s", drone_id)
    return inspection_repository.get_inspections_by_drone(drone_id)


def get_inspection(inspection_id: str) -> Inspection:
    """Get a single inspection by ID.

    Args:
        inspection_id: The inspection to retrieve.

    Returns:
        The Inspection object.

    Raises:
        NotFoundError: If the inspection doesn't exist.
    """
    return inspection_repository.get_inspection_by_id(inspection_id)
