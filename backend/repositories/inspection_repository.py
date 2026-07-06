"""Inspection repository — DynamoDB operations for inspections.

This is the ONLY module that interacts with the Inspections DynamoDB table.
The service layer calls these functions; it never touches boto3 directly.

Why this separation?
- Testability: mock this module, not boto3 internals.
- Replaceability: if you switch to PostgreSQL, only this file changes.
- Clarity: each function maps to one DynamoDB operation.
"""

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from backend.config import settings
from backend.models.inspection import Inspection
from backend.utils.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)

# Initialize DynamoDB resource once per Lambda container (reused across invocations)
_dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
_table = _dynamodb.Table(settings.INSPECTIONS_TABLE)


def create_inspection(inspection: Inspection) -> Inspection:
    """Write a new inspection to DynamoDB.

    Args:
        inspection: The Inspection to persist.

    Returns:
        The same Inspection (confirming successful write).

    Raises:
        DatabaseError: If the DynamoDB PutItem operation fails.
    """
    try:
        _table.put_item(Item=inspection.to_dict())
        logger.info(
            "Created inspection %s for warehouse %s",
            inspection.inspection_id,
            inspection.warehouse_id,
        )
        return inspection
    except ClientError as exc:
        logger.error("Failed to create inspection: %s", exc)
        raise DatabaseError("CreateInspection", str(exc))


def get_inspection_by_id(inspection_id: str) -> Inspection:
    """Fetch a single inspection by its ID.

    Args:
        inspection_id: The inspection's partition key.

    Returns:
        The Inspection object.

    Raises:
        NotFoundError: If no inspection exists with this ID.
        DatabaseError: If the DynamoDB GetItem operation fails.
    """
    try:
        response = _table.get_item(Key={"inspectionId": inspection_id})
    except ClientError as exc:
        logger.error("Failed to get inspection %s: %s", inspection_id, exc)
        raise DatabaseError("GetInspection", str(exc))

    item = response.get("Item")
    if not item:
        raise NotFoundError("Inspection", inspection_id)

    return Inspection.from_dynamo_item(item)


def get_inspections_by_warehouse(warehouse_id: str) -> list[Inspection]:
    """Query all inspections for a warehouse using the GSI.

    Uses the warehouseId-createdAt-index GSI. Results are sorted
    by createdAt (newest first) via ScanIndexForward=False.

    Args:
        warehouse_id: The warehouse to query.

    Returns:
        List of Inspection objects, sorted newest first.

    Raises:
        DatabaseError: If the DynamoDB Query operation fails.
    """
    try:
        response = _table.query(
            IndexName=settings.WAREHOUSE_INDEX,
            KeyConditionExpression="warehouseId = :wid",
            ExpressionAttributeValues={":wid": warehouse_id},
            ScanIndexForward=False,
        )
        logger.info(
            "Found %d inspections for warehouse %s",
            response["Count"],
            warehouse_id,
        )
        return [
            Inspection.from_dynamo_item(item)
            for item in response.get("Items", [])
        ]
    except ClientError as exc:
        logger.error(
            "Failed to query inspections for warehouse %s: %s",
            warehouse_id, exc,
        )
        raise DatabaseError("QueryWarehouseInspections", str(exc))


def get_inspections_by_drone(drone_id: str) -> list[Inspection]:
    """Query all inspections for a drone using the GSI.

    Uses the droneId-createdAt-index GSI. Results are sorted
    by createdAt (newest first).

    Args:
        drone_id: The drone to query.

    Returns:
        List of Inspection objects, sorted newest first.

    Raises:
        DatabaseError: If the DynamoDB Query operation fails.
    """
    try:
        response = _table.query(
            IndexName=settings.DRONE_INDEX,
            KeyConditionExpression="droneId = :did",
            ExpressionAttributeValues={":did": drone_id},
            ScanIndexForward=False,
        )
        logger.info(
            "Found %d inspections for drone %s",
            response["Count"],
            drone_id,
        )
        return [
            Inspection.from_dynamo_item(item)
            for item in response.get("Items", [])
        ]
    except ClientError as exc:
        logger.error(
            "Failed to query inspections for drone %s: %s",
            drone_id, exc,
        )
        raise DatabaseError("QueryDroneInspections", str(exc))
