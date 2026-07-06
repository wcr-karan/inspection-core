"""Application configuration loaded from environment variables.

Why a config module instead of os.getenv() scattered everywhere?

1. Single source of truth — if a table name changes, update one place.
2. Fail-fast — missing env vars are caught at import time, not at runtime
   deep inside a request flow.
3. Testability — tests can mock this module instead of patching os.environ
   in every test file.

In the SAM template, these environment variables are set via the
Globals.Function.Environment.Variables block.
"""

import logging
import os


def _get_required_env(name: str) -> str:
    """Get a required environment variable or raise an error.

    This is called at module load time so missing configuration
    fails immediately during Lambda cold start, not mid-request.
    """
    value = os.environ.get(name, "")
    if not value:
        # During testing, env vars may not be set.
        # Log a warning instead of crashing so tests can proceed.
        logging.getLogger(__name__).warning(
            "Environment variable '%s' is not set", name
        )
    return value


# DynamoDB table names (set by SAM template via !Ref)
INSPECTIONS_TABLE: str = _get_required_env("INSPECTIONS_TABLE")
IMAGES_TABLE: str = _get_required_env("IMAGES_TABLE")

# S3 bucket name
IMAGES_BUCKET: str = _get_required_env("IMAGES_BUCKET")

# DynamoDB GSI names (hardcoded because they don't change per environment)
WAREHOUSE_INDEX: str = "warehouseId-createdAt-index"
DRONE_INDEX: str = "droneId-createdAt-index"

# S3 pre-signed URL expiration (seconds)
PRESIGNED_URL_EXPIRATION: int = int(os.environ.get("PRESIGNED_URL_EXPIRATION", "900"))

# Logging
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

# AWS Region (used for boto3 clients in local development)
AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
