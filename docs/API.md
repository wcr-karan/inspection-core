# API Documentation

## Base URL

```
https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/
```

## Response Format

All responses follow a consistent JSON structure:

**Success:**
```json
{
    "success": true,
    "data": { ... }
}
```

**Error:**
```json
{
    "success": false,
    "message": "Human-readable error description",
    "error": "Optional technical detail"
}
```

---

## Endpoints

### 1. Create Inspection

**`POST /inspections`**

Creates a new drone inspection.

**Request Body:**
```json
{
    "warehouseId": "WH-001",
    "droneId": "DR-001"
}
```

**Success Response (201):**
```json
{
    "success": true,
    "data": {
        "inspectionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "warehouseId": "WH-001",
        "droneId": "DR-001",
        "status": "SCHEDULED",
        "createdAt": "2024-01-15T10:30:00.000000+00:00",
        "updatedAt": "2024-01-15T10:30:00.000000+00:00"
    }
}
```

**Error Response (400):**
```json
{
    "success": false,
    "message": "Missing required fields: warehouseId, droneId"
}
```

**cURL Example:**
```bash
curl -X POST https://{api-url}/inspections \
  -H "Content-Type: application/json" \
  -d '{"warehouseId": "WH-001", "droneId": "DR-001"}'
```

---

### 2. List Warehouse Inspections

**`GET /warehouses/{warehouseId}/inspections`**

Lists all inspections for a given warehouse, sorted newest first.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| warehouseId | string | Yes | The warehouse ID to query |

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "warehouseId": "WH-001",
        "inspections": [
            {
                "inspectionId": "a1b2c3d4-...",
                "warehouseId": "WH-001",
                "droneId": "DR-001",
                "status": "COMPLETED",
                "createdAt": "2024-01-15T10:30:00.000000+00:00",
                "updatedAt": "2024-01-15T12:00:00.000000+00:00"
            }
        ],
        "count": 1
    }
}
```

**cURL Example:**
```bash
curl https://{api-url}/warehouses/WH-001/inspections
```

---

### 3. List Drone Inspections

**`GET /drones/{droneId}/inspections`**

Lists all inspections for a given drone, sorted newest first.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| droneId | string | Yes | The drone ID to query |

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "droneId": "DR-001",
        "inspections": [
            {
                "inspectionId": "a1b2c3d4-...",
                "warehouseId": "WH-001",
                "droneId": "DR-001",
                "status": "SCHEDULED",
                "createdAt": "2024-01-15T10:30:00.000000+00:00",
                "updatedAt": "2024-01-15T10:30:00.000000+00:00"
            }
        ],
        "count": 1
    }
}
```

**cURL Example:**
```bash
curl https://{api-url}/drones/DR-001/inspections
```

---

### 4. Generate Upload URL

**`POST /inspections/{inspectionId}/upload-url`**

Generates a pre-signed S3 URL for direct image upload.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| inspectionId | string | Yes | The inspection to attach the image to |

**Request Body:**
```json
{
    "fileName": "crack-detected.jpg",
    "contentType": "image/jpeg"
}
```

**Allowed Content Types:**
- `image/jpeg`
- `image/png`
- `image/webp`
- `image/tiff`

**Success Response (201):**
```json
{
    "success": true,
    "data": {
        "uploadUrl": "https://s3.amazonaws.com/bucket/inspections/abc/img-id.jpg?X-Amz-...",
        "imageId": "f1e2d3c4-...",
        "s3Key": "inspections/a1b2c3d4/f1e2d3c4.jpg"
    }
}
```

**Error Response (404):**
```json
{
    "success": false,
    "message": "Inspection not found: invalid-id"
}
```

**cURL Example (generate URL, then upload):**
```bash
# Step 1: Get pre-signed URL
curl -X POST https://{api-url}/inspections/{inspectionId}/upload-url \
  -H "Content-Type: application/json" \
  -d '{"fileName": "photo.jpg", "contentType": "image/jpeg"}'

# Step 2: Upload image directly to S3 using the returned URL
curl -X PUT "{uploadUrl}" \
  -H "Content-Type: image/jpeg" \
  --data-binary @photo.jpg
```

---

### 5. List Inspection Images

**`GET /inspections/{inspectionId}/images`**

Lists all images associated with an inspection.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| inspectionId | string | Yes | The inspection to list images for |

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "inspectionId": "a1b2c3d4-...",
        "images": [
            {
                "inspectionId": "a1b2c3d4-...",
                "imageId": "f1e2d3c4-...",
                "s3Key": "inspections/a1b2c3d4/f1e2d3c4.jpg",
                "fileName": "crack-detected.jpg",
                "contentType": "image/jpeg",
                "uploadedAt": "2024-01-15T11:00:00.000000+00:00"
            }
        ],
        "count": 1
    }
}
```

**cURL Example:**
```bash
curl https://{api-url}/inspections/{inspectionId}/images
```

---

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | GET requests that return data |
| 201 | Created | POST requests that create resources |
| 400 | Bad Request | Invalid or missing input |
| 404 | Not Found | Resource does not exist |
| 500 | Internal Error | Unexpected server error |
