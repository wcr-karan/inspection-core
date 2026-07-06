# Drone Inspection Backend

Serverless backend for managing drone inspections across warehouses, built with AWS SAM, Lambda, DynamoDB, and S3.

## Project Overview

This backend manages the lifecycle of drone inspections at warehouses. It provides APIs to create inspections, query them by warehouse or drone, upload inspection images via pre-signed S3 URLs, and list images per inspection.

### Entity Relationships

```
Warehouse (1) ──→ (N) Drones
Warehouse (1) ──→ (N) Inspections
Drone     (1) ──→ (N) Inspections
Inspection(1) ──→ (N) Images
```

## Tech Stack

| Technology | Purpose |
|-----------|---------|
| Python 3.11 | Runtime language |
| AWS Lambda | Serverless compute |
| API Gateway | REST API routing |
| DynamoDB | NoSQL database |
| Amazon S3 | Image storage |
| AWS SAM | Infrastructure as Code |
| boto3 | AWS SDK for Python |

## Architecture

```
Client
  │
  ▼
API Gateway (REST)
  │
  ├── POST /inspections
  ├── GET  /warehouses/{id}/inspections
  ├── GET  /drones/{id}/inspections
  ├── POST /inspections/{id}/upload-url
  └── GET  /inspections/{id}/images
       │
       ▼
  Lambda Handlers  →  Services  →  Repositories  →  DynamoDB
                          │
                          └──→  S3 Helper  →  S3
```

**Layer responsibilities:**

| Layer | Responsibility | AWS Dependency |
|-------|---------------|----------------|
| Handlers | Parse request, validate input, return response | API Gateway event format |
| Services | Business logic, orchestration | None |
| Repositories | Database CRUD operations | DynamoDB via boto3 |
| Models | Data structures (dataclasses) | None |
| Utils | Response builders, validators, S3 helper | boto3 (S3 only) |

## Folder Structure

```
inspection-core/
├── backend/
│   ├── handlers/                  # Lambda entry points (thin)
│   │   ├── create_inspection.py
│   │   ├── get_warehouse_inspections.py
│   │   ├── get_drone_inspections.py
│   │   ├── generate_upload_url.py
│   │   └── get_inspection_images.py
│   ├── services/                  # Business logic
│   │   ├── inspection_service.py
│   │   └── image_service.py
│   ├── repositories/              # DynamoDB operations
│   │   ├── inspection_repository.py
│   │   └── image_repository.py
│   ├── models/                    # Dataclasses
│   │   ├── inspection.py
│   │   └── image.py
│   ├── utils/                     # Shared utilities
│   │   ├── response.py            # API response builders
│   │   ├── exceptions.py          # Custom exception classes
│   │   ├── validators.py          # Input validation
│   │   ├── decorator.py           # Handler error-handling decorator
│   │   └── s3_helper.py           # Pre-signed URL generation
│   └── config/
│       └── settings.py            # Environment configuration
├── tests/
│   └── unit/
│       ├── services/
│       │   ├── test_inspection_service.py
│       │   └── test_image_service.py
│       └── utils/
│           └── test_utils.py
├── docs/
│   └── API.md                     # Full API documentation
├── template.yaml                  # AWS SAM template
├── pyproject.toml                 # Pytest & coverage config
├── Makefile                       # Dev workflow shortcuts
├── requirements.txt               # Production dependencies
└── requirements-dev.txt           # Development dependencies
```

## AWS Resources

| Resource | Type | Purpose |
|----------|------|---------|
| InspectionsTable | DynamoDB Table | Stores inspection records |
| ImagesTable | DynamoDB Table | Stores image metadata |
| ImagesBucket | S3 Bucket | Stores uploaded inspection images |
| InspectionApi | API Gateway | REST API with 5 endpoints |
| 5 Lambda Functions | Lambda | One per API endpoint |

## DynamoDB Design

### Inspections Table

| Attribute | Type | Key |
|-----------|------|-----|
| inspectionId | String (UUID) | Partition Key |
| warehouseId | String | GSI-1 Partition Key |
| droneId | String | GSI-2 Partition Key |
| createdAt | String (ISO 8601) | GSI-1 & GSI-2 Sort Key |
| status | String | — |
| updatedAt | String (ISO 8601) | — |

**GSI-1:** `warehouseId-createdAt-index` — Query inspections by warehouse.
**GSI-2:** `droneId-createdAt-index` — Query inspections by drone.

### Images Table

| Attribute | Type | Key |
|-----------|------|-----|
| inspectionId | String | Partition Key |
| imageId | String (UUID) | Sort Key |
| s3Key | String | — |
| fileName | String | — |
| contentType | String | — |
| uploadedAt | String (ISO 8601) | — |

## API Documentation

See [docs/API.md](docs/API.md) for full API documentation with request/response examples and cURL commands.

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/inspections` | Create a new inspection |
| GET | `/warehouses/{warehouseId}/inspections` | List inspections for a warehouse |
| GET | `/drones/{droneId}/inspections` | List inspections for a drone |
| POST | `/inspections/{inspectionId}/upload-url` | Generate image upload URL |
| GET | `/inspections/{inspectionId}/images` | List images for an inspection |

## Deployment

### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- Python 3.11

### Deploy to AWS

```bash
# Build the application
sam build

# Deploy (first time — guided mode)
sam deploy --guided

# Subsequent deployments
sam deploy
```

### SAM Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| StageName | dev | Deployment stage (dev/staging/prod) |

## Local Development

### Setup

```bash
# Install development dependencies
make install
# or
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage

# Run specific test file
python -m pytest tests/unit/services/test_inspection_service.py -v
```

### Local API Testing

```bash
# Start the API locally
sam local start-api

# Test an endpoint
curl -X POST http://127.0.0.1:3000/inspections \
  -H "Content-Type: application/json" \
  -d '{"warehouseId": "WH-001", "droneId": "DR-001"}'
```

## Testing Strategy

- **Unit tests** mock the repository and AWS service layers using `unittest.mock`
- **Service layer tests** verify business logic in isolation
- **Utility tests** verify response builders, validators, and exception handling
- Coverage target: **70% minimum** (enforced in `pyproject.toml`)

## Error Handling

All errors follow a consistent pattern:

1. Custom exceptions (`NotFoundError`, `ValidationError`, etc.) are raised by services/repositories
2. The `@lambda_handler` decorator catches exceptions and maps them to HTTP status codes
3. All responses use the standardized format from `backend/utils/response.py`

## Future Improvements

- [ ] Add pagination to list endpoints (DynamoDB `LastEvaluatedKey`)
- [ ] Add `PATCH /inspections/{id}` to update inspection status
- [ ] Implement S3 event notifications to confirm successful uploads
- [ ] Add API Gateway request throttling and usage plans
- [ ] Add CloudWatch alarms for error rates and latency
- [ ] Implement integration tests with `moto` for full DynamoDB flows
- [ ] Add API Gateway authorizer (Cognito or Lambda authorizer)
- [ ] Create CI/CD pipeline with GitHub Actions
- [ ] Add OpenAPI/Swagger specification