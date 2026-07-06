"""Custom exception classes for the Drone Inspection Backend.

Why custom exceptions instead of raising ValueError/KeyError everywhere?

1. Clarity — `raise InspectionNotFoundError(id)` is self-documenting.
2. Granular handling — handlers can catch specific exceptions and return
   the correct HTTP status code (404 vs 400 vs 500).
3. Separation — the service layer raises domain exceptions without knowing
   anything about HTTP. The handler translates them to HTTP responses.
"""


class AppError(Exception):
    """Base exception for all application errors.

    All custom exceptions inherit from this so handlers can catch
    `AppError` as a catch-all for known application errors, separate
    from unexpected exceptions (which become 500s).
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: str) -> None:
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} not found: {resource_id}")


class ValidationError(AppError):
    """Raised when request input fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DatabaseError(AppError):
    """Raised when a DynamoDB operation fails.

    Wraps boto3 ClientError with a cleaner interface so the service
    layer doesn't need to import or handle boto3-specific exceptions.
    """

    def __init__(self, operation: str, detail: str = "") -> None:
        self.operation = operation
        msg = f"Database error during {operation}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


class StorageError(AppError):
    """Raised when an S3 operation fails."""

    def __init__(self, operation: str, detail: str = "") -> None:
        self.operation = operation
        msg = f"Storage error during {operation}"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)
