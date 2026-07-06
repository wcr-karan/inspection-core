"""Lambda handler decorator for centralized error handling and logging.

Every handler repeats the same try/except pattern. This decorator
extracts that pattern so handlers become even thinner. This is a
refactor — the handlers already work, but this reduces duplication.

Before (in every handler):
    try:
        ...
    except ValidationError as exc:
        return error_response(...)
    except NotFoundError as exc:
        return not_found_response(...)
    except AppError as exc:
        return error_response(...)
    except Exception:
        return internal_error_response()

After (with decorator):
    @lambda_handler
    def handler(event, context):
        ...  # just the happy path
"""

import functools
import logging
from typing import Callable

from backend.utils.exceptions import AppError, NotFoundError, ValidationError
from backend.utils.response import (
    error_response,
    internal_error_response,
    not_found_response,
)

logger = logging.getLogger(__name__)


def lambda_handler(func: Callable) -> Callable:
    """Decorator that wraps a Lambda handler with standardized error handling.

    Catches known exceptions and maps them to proper HTTP responses.
    Logs all errors at appropriate levels.

    Usage:
        @lambda_handler
        def handler(event, context):
            # only write the happy path
            return success_response(data)
    """

    @functools.wraps(func)
    def wrapper(event: dict, context) -> dict:
        try:
            return func(event, context)

        except NotFoundError as exc:
            logger.warning("Not found: %s", exc.message)
            return not_found_response(exc.message)

        except ValidationError as exc:
            logger.warning("Validation failed: %s", exc.message)
            return error_response(exc.message, status_code=400)

        except AppError as exc:
            logger.error("Application error: %s", exc.message)
            return error_response(exc.message, status_code=500)

        except Exception:
            logger.exception("Unexpected error in %s", func.__name__)
            return internal_error_response()

    return wrapper
