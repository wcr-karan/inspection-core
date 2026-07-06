"""Unit tests for utility modules: validators, response, and exceptions."""

import json
import os
import unittest

os.environ.setdefault("INSPECTIONS_TABLE", "test-inspections")
os.environ.setdefault("IMAGES_TABLE", "test-images")
os.environ.setdefault("IMAGES_BUCKET", "test-bucket")

from backend.utils.exceptions import (
    AppError,
    DatabaseError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from backend.utils.response import (
    created_response,
    error_response,
    internal_error_response,
    not_found_response,
    success_response,
)
from backend.utils.validators import (
    get_path_parameter,
    get_query_parameter,
    parse_request_body,
    validate_allowed_values,
    validate_required_fields,
)


class TestResponseHelpers(unittest.TestCase):
    """Tests for backend.utils.response."""

    def test_success_response_shape(self):
        resp = success_response({"key": "value"})
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["key"], "value")

    def test_created_response_status(self):
        resp = created_response({"id": "123"})
        self.assertEqual(resp["statusCode"], 201)

    def test_error_response_shape(self):
        resp = error_response("bad input", status_code=422, error="ValidationError")
        body = json.loads(resp["body"])
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "bad input")
        self.assertEqual(body["error"], "ValidationError")

    def test_error_response_without_error_detail(self):
        resp = error_response("missing field")
        body = json.loads(resp["body"])
        self.assertNotIn("error", body)

    def test_not_found_response(self):
        resp = not_found_response("Item missing")
        self.assertEqual(resp["statusCode"], 404)

    def test_internal_error_response(self):
        resp = internal_error_response()
        self.assertEqual(resp["statusCode"], 500)

    def test_cors_headers_present(self):
        resp = success_response({})
        self.assertEqual(resp["headers"]["Access-Control-Allow-Origin"], "*")
        self.assertIn("Content-Type", resp["headers"])


class TestValidators(unittest.TestCase):
    """Tests for backend.utils.validators."""

    def test_parse_valid_body(self):
        event = {"body": json.dumps({"key": "val"})}
        result = parse_request_body(event)
        self.assertEqual(result, {"key": "val"})

    def test_parse_missing_body(self):
        with self.assertRaises(ValidationError):
            parse_request_body({})

    def test_parse_invalid_json(self):
        with self.assertRaises(ValidationError):
            parse_request_body({"body": "not json"})

    def test_parse_non_object_body(self):
        with self.assertRaises(ValidationError):
            parse_request_body({"body": json.dumps([1, 2])})

    def test_get_path_parameter_success(self):
        event = {"pathParameters": {"id": "abc"}}
        self.assertEqual(get_path_parameter(event, "id"), "abc")

    def test_get_path_parameter_missing(self):
        with self.assertRaises(ValidationError):
            get_path_parameter({"pathParameters": {}}, "id")

    def test_get_path_parameter_null_params(self):
        with self.assertRaises(ValidationError):
            get_path_parameter({"pathParameters": None}, "id")

    def test_validate_required_fields_pass(self):
        # Should not raise
        validate_required_fields({"a": "1", "b": "2"}, ["a", "b"])

    def test_validate_required_fields_missing(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_required_fields({"a": "1"}, ["a", "b", "c"])
        self.assertIn("b", ctx.exception.message)
        self.assertIn("c", ctx.exception.message)

    def test_validate_required_fields_empty_string(self):
        with self.assertRaises(ValidationError):
            validate_required_fields({"a": "  "}, ["a"])

    def test_validate_allowed_values_pass(self):
        validate_allowed_values("A", "field", ["A", "B"])

    def test_validate_allowed_values_fail(self):
        with self.assertRaises(ValidationError):
            validate_allowed_values("C", "field", ["A", "B"])

    def test_get_query_parameter_present(self):
        event = {"queryStringParameters": {"limit": "10"}}
        self.assertEqual(get_query_parameter(event, "limit"), "10")

    def test_get_query_parameter_default(self):
        self.assertEqual(get_query_parameter({}, "limit", "20"), "20")


class TestExceptions(unittest.TestCase):
    """Tests for backend.utils.exceptions."""

    def test_all_inherit_from_app_error(self):
        exceptions = [
            NotFoundError("Resource", "id"),
            ValidationError("msg"),
            DatabaseError("op"),
            StorageError("op"),
        ]
        for exc in exceptions:
            self.assertIsInstance(exc, AppError)

    def test_not_found_error_message(self):
        exc = NotFoundError("Inspection", "abc-123")
        self.assertEqual(exc.message, "Inspection not found: abc-123")
        self.assertEqual(exc.resource, "Inspection")
        self.assertEqual(exc.resource_id, "abc-123")

    def test_database_error_with_detail(self):
        exc = DatabaseError("PutItem", "throttled")
        self.assertIn("PutItem", exc.message)
        self.assertIn("throttled", exc.message)

    def test_database_error_without_detail(self):
        exc = DatabaseError("Query")
        self.assertIn("Query", exc.message)
        self.assertNotIn(":", exc.message.split("Query")[1])


if __name__ == "__main__":
    unittest.main()
