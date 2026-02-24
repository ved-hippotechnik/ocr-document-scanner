"""
Swagger / OpenAPI 2.0 configuration and spec for the OCR Document Scanner API.

Flasgger uses Swagger 2.0 (not OpenAPI 3.0) internally, but the UI renders it
as a fully interactive OpenAPI-style explorer.  All endpoint documentation is
written as YAML docstrings so Flask views stay clean and the spec remains
co-located with the code.
"""

# ---------------------------------------------------------------------------
# Top-level Swagger template
# This is merged with every per-view YAML block by Flasgger at runtime.
# ---------------------------------------------------------------------------

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "OCR Document Scanner API",
        "description": (
            "AI-powered OCR document scanner supporting Emirates ID, Aadhaar Card, "
            "Indian Driving License, Passports, and US Driver's License.  "
            "Provides document classification, quality assessment, batch processing, "
            "and analytics.  "
            "\n\n"
            "**Authentication**: Protected endpoints require a JWT Bearer token obtained "
            "from `POST /api/auth/login`.  Pass it as:\n"
            "```\nAuthorization: Bearer <token>\n```"
        ),
        "version": "3.0.0",
        "contact": {
            "name": "OCR Document Scanner",
            "url": "https://github.com/your-org/ocr-document-scanner",
        },
        "license": {
            "name": "MIT",
        },
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "JWT token in the format: Bearer <token>",
        }
    },
    # Reusable definitions (schemas) referenced via $ref throughout the spec.
    "definitions": {
        # ------------------------------------------------------------------ #
        # Common / shared models                                               #
        # ------------------------------------------------------------------ #
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "example": "Description of what went wrong",
                },
                "code": {
                    "type": "string",
                    "example": "VALIDATION_ERROR",
                },
                "message": {
                    "type": "string",
                    "example": "Detailed human-readable error message",
                },
            },
        },
        # ------------------------------------------------------------------ #
        # Health                                                               #
        # ------------------------------------------------------------------ #
        "BasicHealthResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "example": "healthy",
                    "enum": ["healthy", "degraded", "unhealthy"],
                },
                "service": {
                    "type": "string",
                    "example": "ocr-document-scanner",
                },
            },
        },
        "ComponentHealth": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["ok", "degraded", "error", "disabled"],
                },
                "message": {"type": "string"},
            },
        },
        "DetailedHealthResponse": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["healthy", "degraded", "unhealthy"],
                    "example": "healthy",
                },
                "version": {"type": "string", "example": "3.0.0"},
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "example": "2026-02-22T10:00:00Z",
                },
                "components": {
                    "type": "object",
                    "properties": {
                        "database": {"$ref": "#/definitions/ComponentHealth"},
                        "cache": {"$ref": "#/definitions/ComponentHealth"},
                        "ocr_engine": {"$ref": "#/definitions/ComponentHealth"},
                        "ml_classifier": {"$ref": "#/definitions/ComponentHealth"},
                        "vision_service": {"$ref": "#/definitions/ComponentHealth"},
                    },
                },
            },
        },
        # ------------------------------------------------------------------ #
        # Processors                                                           #
        # ------------------------------------------------------------------ #
        "ProcessorInfo": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "example": "emirates_id"},
                "name": {"type": "string", "example": "Emirates ID"},
                "description": {
                    "type": "string",
                    "example": "United Arab Emirates national identity card",
                },
                "supported_languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": ["eng", "ara"],
                },
            },
        },
        "ProcessorsResponse": {
            "type": "object",
            "properties": {
                "supported_documents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "example": [
                        "Emirates ID",
                        "Aadhaar Card",
                        "Driving License",
                        "Passport",
                        "US Driver's License",
                    ],
                },
                "total_processors": {"type": "integer", "example": 5},
            },
        },
        # ------------------------------------------------------------------ #
        # Document scan result models                                          #
        # ------------------------------------------------------------------ #
        "ExtractedInfo": {
            "type": "object",
            "description": "Fields extracted from the document via OCR.",
            "properties": {
                "full_name": {
                    "type": "string",
                    "nullable": True,
                    "example": "Ahmed Al Mansouri",
                },
                "document_number": {
                    "type": "string",
                    "nullable": True,
                    "example": "784-1990-1234567-1",
                },
                "date_of_birth": {
                    "type": "string",
                    "nullable": True,
                    "example": "01/01/1990",
                },
                "date_of_expiry": {
                    "type": "string",
                    "nullable": True,
                    "example": "31/12/2030",
                },
                "nationality": {
                    "type": "string",
                    "nullable": True,
                    "example": "UAE",
                },
                "gender": {
                    "type": "string",
                    "nullable": True,
                    "enum": ["M", "F", None],
                    "example": "M",
                },
                "unified_number": {
                    "type": "string",
                    "nullable": True,
                    "example": "784199012345671",
                },
                "license_number": {
                    "type": "string",
                    "nullable": True,
                    "example": "DL1234567",
                },
                "issue_date": {
                    "type": "string",
                    "nullable": True,
                    "example": "01/01/2020",
                },
                "place_of_issue": {
                    "type": "string",
                    "nullable": True,
                    "example": "Dubai",
                },
            },
        },
        "ScanResponse": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "example": "Emirates ID",
                },
                "nationality": {
                    "type": "string",
                    "example": "UAE",
                },
                "extracted_info": {"$ref": "#/definitions/ExtractedInfo"},
                "extracted_text": {
                    "type": "string",
                    "example": "Full raw OCR output text...",
                },
                "processing_method": {
                    "type": "string",
                    "example": "enhanced_emirates_id",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "example": "high",
                },
                "quality_score": {
                    "type": "number",
                    "format": "float",
                    "nullable": True,
                    "example": 0.92,
                },
                "duplicate_warning": {
                    "type": "object",
                    "nullable": True,
                    "properties": {
                        "is_duplicate": {"type": "boolean"},
                        "distance": {"type": "number"},
                        "matching_scan": {"type": "string"},
                    },
                },
            },
        },
        # ------------------------------------------------------------------ #
        # Auth models                                                          #
        # ------------------------------------------------------------------ #
        "RegisterRequest": {
            "type": "object",
            "required": ["email", "username", "password"],
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "user@example.com",
                },
                "username": {"type": "string", "example": "john_doe"},
                "password": {
                    "type": "string",
                    "format": "password",
                    "example": "SecureP@ss123",
                    "description": (
                        "Must be at least 8 characters and contain a mix of "
                        "uppercase, lowercase, digits, and special characters."
                    ),
                },
                "first_name": {"type": "string", "example": "John"},
                "last_name": {"type": "string", "example": "Doe"},
                "organization": {"type": "string", "example": "Acme Corp"},
            },
        },
        "LoginRequest": {
            "type": "object",
            "required": ["email", "password"],
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "user@example.com",
                },
                "password": {
                    "type": "string",
                    "format": "password",
                    "example": "SecureP@ss123",
                },
            },
        },
        "UserObject": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "example": "usr_abc123"},
                "email": {"type": "string", "example": "user@example.com"},
                "username": {"type": "string", "example": "john_doe"},
                "first_name": {"type": "string", "example": "John"},
                "last_name": {"type": "string", "example": "Doe"},
                "organization": {"type": "string", "example": "Acme Corp"},
                "is_active": {"type": "boolean", "example": True},
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                    "example": "2026-01-01T00:00:00Z",
                },
                "last_login": {
                    "type": "string",
                    "format": "date-time",
                    "nullable": True,
                    "example": "2026-02-22T08:30:00Z",
                },
            },
        },
        "AuthResponse": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": "Login successful"},
                "user": {"$ref": "#/definitions/UserObject"},
                "access_token": {
                    "type": "string",
                    "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                "refresh_token": {
                    "type": "string",
                    "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                "expires_in": {
                    "type": "integer",
                    "description": "Access token lifetime in seconds",
                    "example": 86400,
                },
            },
        },
        # ------------------------------------------------------------------ #
        # Stats                                                                #
        # ------------------------------------------------------------------ #
        "StatsResponse": {
            "type": "object",
            "properties": {
                "total_scanned": {"type": "integer", "example": 1024},
                "document_types": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                    "example": {
                        "passport": 400,
                        "id_card": 300,
                        "driving_license": 200,
                        "aadhaar": 100,
                        "other": 24,
                    },
                },
                "nationalities": {
                    "type": "object",
                    "additionalProperties": {"type": "integer"},
                    "example": {"UAE": 350, "IND": 280, "USA": 120},
                },
            },
        },
        # ------------------------------------------------------------------ #
        # Batch                                                                #
        # ------------------------------------------------------------------ #
        "BatchDocument": {
            "type": "object",
            "required": ["id", "image"],
            "properties": {
                "id": {
                    "type": "string",
                    "example": "doc_001",
                    "description": "Caller-assigned identifier for this document within the batch.",
                },
                "image": {
                    "type": "string",
                    "description": "Base64-encoded image data (JPEG, PNG, BMP, TIFF, or PDF).",
                    "example": "/9j/4AAQSkZJRgABAQEASABIAAD...",
                },
            },
        },
        "BatchConfig": {
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "default": "normal",
                    "example": "normal",
                },
                "notify_on_completion": {
                    "type": "boolean",
                    "default": False,
                    "example": True,
                },
            },
        },
        "BatchSubmitRequest": {
            "type": "object",
            "required": ["documents"],
            "properties": {
                "documents": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/BatchDocument"},
                    "minItems": 1,
                    "maxItems": 100,
                },
                "config": {"$ref": "#/definitions/BatchConfig"},
            },
        },
        "BatchSubmitResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "job_id": {
                    "type": "string",
                    "example": "job_2026022210300001",
                },
                "message": {
                    "type": "string",
                    "example": "Batch job submitted successfully with 5 documents",
                },
            },
        },
    },
    # Global tags used to group operations in the Swagger UI sidebar.
    "tags": [
        {
            "name": "Health",
            "description": "Service liveness and readiness probes",
        },
        {
            "name": "Scanning",
            "description": "Single-document OCR and data extraction",
        },
        {
            "name": "Processors",
            "description": "Discover available document processors",
        },
        {
            "name": "Statistics",
            "description": "In-memory scan statistics",
        },
        {
            "name": "Authentication",
            "description": "User registration, login, and JWT token management",
        },
        {
            "name": "Batch",
            "description": "Submit and manage multi-document batch processing jobs",
        },
    ],
}

# ---------------------------------------------------------------------------
# Flasgger configuration dict (passed to Swagger(app, config=...) )
# ---------------------------------------------------------------------------

SWAGGER_CONFIG = {
    # Serve the spec JSON at this URL (default is /apispec_1.json).
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/api/docs/apispec.json",
            "rule_filter": lambda rule: True,   # include all rules
            "model_filter": lambda tag: True,   # include all models
        }
    ],
    # Render the Swagger UI at /api/docs.
    "swagger_ui": True,
    "specs_route": "/api/docs",
    # HTML title shown in the browser tab.
    "title": "OCR Document Scanner API",
    # Use the bundled Swagger UI assets (no CDN required).
    "uiversion": 3,
    "favicon": "/favicon.ico",
    # Optional: display the operation ID next to each endpoint.
    "display_operation_id": False,
    "display_request_duration": True,
    "doc_expansion": "list",   # "none" | "list" | "full"
    "default_model_rendering": "example",
    "show_extensions": True,
    "show_common_extensions": True,
    # Persist authentication across page refreshes.
    "supportedSubmitMethods": ["get", "post", "put", "delete", "patch"],
    "headers": [],
}


# ---------------------------------------------------------------------------
# Per-endpoint YAML docstrings
#
# These are *standalone strings* that routes in other modules can import and
# embed verbatim in their view-function docstrings.  Flasgger parses the YAML
# section that starts with "---" inside a docstring.
#
# Alternatively, routes can define their own inline YAML docstrings; the
# definitions below centralise the spec for the endpoints that are defined
# directly in __init__.py (health check, processors, etc.) and for the key
# endpoints listed in the task.
# ---------------------------------------------------------------------------

HEALTH_BASIC_SPEC = """
Basic health check.
---
tags:
  - Health
operationId: healthCheck
summary: Basic liveness probe
description: >
  Returns a simple JSON payload indicating the service is running.
  Use this endpoint for load-balancer or container orchestration health checks.
responses:
  200:
    description: Service is healthy.
    schema:
      $ref: '#/definitions/BasicHealthResponse'
    examples:
      application/json:
        status: healthy
        service: ocr-document-scanner
"""

PROCESSORS_SPEC = """
List available document processors.
---
tags:
  - Processors
operationId: listProcessors
summary: Get supported document types and processor count
description: >
  Returns the list of document types the OCR engine can detect and process,
  together with the number of active processor modules.
responses:
  200:
    description: Available processors retrieved successfully.
    schema:
      $ref: '#/definitions/ProcessorsResponse'
    examples:
      application/json:
        supported_documents:
          - Emirates ID
          - Aadhaar Card
          - Driving License
          - Passport
          - US Driver License
        total_processors: 5
"""

SCAN_V3_SPEC = """
Scan a single document image (v3).
---
tags:
  - Scanning
operationId: scanDocumentV3
summary: Upload and OCR a document (recommended endpoint)
description: >
  Upload a document image (JPEG, PNG, BMP, TIFF, or PDF) as multipart/form-data.
  The engine will:

  1. Validate and sanitise the uploaded file.
  2. Auto-classify the document type using the ML classifier.
  3. Apply the matching specialist OCR processor.
  4. Return structured extracted fields together with the raw OCR text.

  Supported document types: Emirates ID, Aadhaar Card, Indian Driving License,
  Passport (various countries), US Driver's License.

  **Rate limit**: 10 requests / minute per IP.
consumes:
  - multipart/form-data
parameters:
  - in: formData
    name: image
    type: file
    required: true
    description: >
      The document image file.  Accepted MIME types:
      image/jpeg, image/png, image/bmp, image/tiff, application/pdf.
      Maximum size: 16 MB.
  - in: formData
    name: language
    type: string
    required: false
    description: >
      ISO 639-3 language code for OCR hints (e.g. eng, ara, hin).
      If omitted the engine auto-detects the language.
    example: eng
  - in: formData
    name: validate_with_vision
    type: boolean
    required: false
    default: false
    description: >
      When true, pass the extracted text through Claude Vision for an additional
      validation and confidence boost.  Requires ANTHROPIC_API_KEY to be set.
responses:
  200:
    description: Document scanned and data extracted successfully.
    schema:
      $ref: '#/definitions/ScanResponse'
  400:
    description: Bad request — missing file, invalid format, or empty file.
    schema:
      $ref: '#/definitions/ErrorResponse'
    examples:
      application/json:
        error: Missing required file
        code: FILE_REQUIRED
        message: No image file provided in request
  413:
    description: File exceeds the 16 MB upload limit.
    schema:
      $ref: '#/definitions/ErrorResponse'
  429:
    description: Rate limit exceeded.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal OCR processing error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

SCAN_BASIC_SPEC = """
Scan a single document image (v1 — legacy).
---
tags:
  - Scanning
operationId: scanDocumentV1
summary: Upload and OCR a document (legacy endpoint)
description: >
  Original scanning endpoint.  Accepts a document image via multipart/form-data
  and returns extracted fields.  For new integrations prefer `POST /api/v3/scan`
  which includes stricter validation and better error messages.

  **Rate limit**: 10 requests / minute per IP.
consumes:
  - multipart/form-data
parameters:
  - in: formData
    name: image
    type: file
    required: true
    description: Document image (JPEG, PNG, BMP, TIFF, or PDF). Max 16 MB.
  - in: formData
    name: language
    type: string
    required: false
    description: ISO 639-3 OCR language hint (e.g. eng, ara, hin).
  - in: formData
    name: validate_with_vision
    type: boolean
    required: false
    default: false
    description: Enable Claude Vision secondary validation.
responses:
  200:
    description: Document scanned successfully.
    schema:
      $ref: '#/definitions/ScanResponse'
  400:
    description: Validation error.
    schema:
      $ref: '#/definitions/ErrorResponse'
  429:
    description: Rate limit exceeded.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

STATS_SPEC = """
Get processing statistics.
---
tags:
  - Statistics
operationId: getStats
summary: In-memory scan counters
description: >
  Returns running totals for the current server process: number of documents
  scanned, breakdown by document type, and breakdown by detected nationality.
  These counters reset when the server restarts.

  **Rate limit**: 60 requests / minute per IP.
responses:
  200:
    description: Statistics retrieved successfully.
    schema:
      $ref: '#/definitions/StatsResponse'
"""

HEALTH_V3_SPEC = """
Comprehensive health check (v3).
---
tags:
  - Health
operationId: healthCheckV3
summary: Detailed component health check
description: >
  Probes each internal subsystem (database, cache, OCR engine, ML classifier,
  optional Claude Vision service) and aggregates a single top-level status.

  * **healthy** — all critical components are operational.
  * **degraded** — one or more non-critical components have issues.
  * **unhealthy** — one or more critical components have failed.
responses:
  200:
    description: Health check completed (see `status` field for outcome).
    schema:
      $ref: '#/definitions/DetailedHealthResponse'
    examples:
      application/json:
        status: healthy
        version: 3.0.0
        timestamp: "2026-02-22T10:00:00Z"
        components:
          database:
            status: ok
          cache:
            status: ok
          ocr_engine:
            status: ok
          ml_classifier:
            status: ok
          vision_service:
            status: disabled
            message: ANTHROPIC_API_KEY not configured
"""

BATCH_SCAN_SPEC = """
Submit a batch processing job.
---
tags:
  - Batch
operationId: submitBatch
summary: Queue multiple documents for background OCR processing
description: >
  Submit up to 100 documents encoded as base64 strings for asynchronous
  processing.  The endpoint returns a `job_id` immediately; use
  `GET /api/batch/status/{job_id}` to poll for completion.

  **Authentication**: JWT Bearer token required.

  **Rate limit**: 5 requests / minute per user.
security:
  - BearerAuth: []
parameters:
  - in: body
    name: body
    required: true
    schema:
      $ref: '#/definitions/BatchSubmitRequest'
responses:
  200:
    description: Batch job queued successfully.
    schema:
      $ref: '#/definitions/BatchSubmitResponse'
  400:
    description: Validation error — malformed request or empty documents array.
    schema:
      $ref: '#/definitions/ErrorResponse'
  401:
    description: Missing or invalid JWT token.
    schema:
      $ref: '#/definitions/ErrorResponse'
  429:
    description: Rate limit exceeded.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

AUTH_REGISTER_SPEC = """
Register a new user.
---
tags:
  - Authentication
operationId: registerUser
summary: Create a new user account
description: >
  Creates a user account and returns a JWT access token and refresh token.
  Passwords must be at least 8 characters and contain uppercase letters,
  lowercase letters, digits, and at least one special character.

  **Rate limit**: 5 requests / minute per IP.
parameters:
  - in: body
    name: body
    required: true
    schema:
      $ref: '#/definitions/RegisterRequest'
responses:
  201:
    description: User registered successfully.
    schema:
      $ref: '#/definitions/AuthResponse'
  400:
    description: Validation error — missing fields, invalid email, or weak password.
    schema:
      $ref: '#/definitions/ErrorResponse'
    examples:
      application/json:
        error: Invalid email format
  409:
    description: Email or username already in use.
    schema:
      $ref: '#/definitions/ErrorResponse'
    examples:
      application/json:
        error: Email already registered
  429:
    description: Rate limit exceeded.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

AUTH_LOGIN_SPEC = """
Authenticate a user.
---
tags:
  - Authentication
operationId: loginUser
summary: Log in and receive JWT tokens
description: >
  Validates the provided credentials and returns a short-lived access token
  (default: 24 h) and a long-lived refresh token (default: 30 days).
  Include the access token as `Authorization: Bearer <token>` on protected
  endpoints.

  Accounts are temporarily locked after 5 consecutive failed attempts.

  **Rate limit**: 5 requests / minute per IP.
parameters:
  - in: body
    name: body
    required: true
    schema:
      $ref: '#/definitions/LoginRequest'
responses:
  200:
    description: Login successful.
    schema:
      $ref: '#/definitions/AuthResponse'
  400:
    description: Missing email or password.
    schema:
      $ref: '#/definitions/ErrorResponse'
  401:
    description: Invalid credentials or deactivated account.
    schema:
      $ref: '#/definitions/ErrorResponse'
    examples:
      application/json:
        error: Invalid credentials
  423:
    description: Account locked due to repeated failed login attempts.
    schema:
      $ref: '#/definitions/ErrorResponse'
    examples:
      application/json:
        error: Account temporarily locked due to multiple failed login attempts
  429:
    description: Rate limit exceeded.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

AUTH_REFRESH_SPEC = """
Refresh access token.
---
tags:
  - Authentication
operationId: refreshToken
summary: Exchange a refresh token for a new access token
description: >
  Present a valid refresh token to receive a fresh access token without
  requiring the user to log in again.
parameters:
  - in: body
    name: body
    required: true
    schema:
      type: object
      required:
        - refresh_token
      properties:
        refresh_token:
          type: string
          example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
responses:
  200:
    description: New access token issued.
    schema:
      type: object
      properties:
        access_token:
          type: string
          example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        expires_in:
          type: integer
          example: 86400
  400:
    description: Missing refresh token.
    schema:
      $ref: '#/definitions/ErrorResponse'
  401:
    description: Invalid or expired refresh token.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""

AUTH_PROFILE_SPEC = """
Get current user profile.
---
tags:
  - Authentication
operationId: getUserProfile
summary: Retrieve authenticated user information
description: >
  Returns the profile for the authenticated user identified by the JWT token.

  **Authentication**: JWT Bearer token required.
security:
  - BearerAuth: []
responses:
  200:
    description: Profile retrieved successfully.
    schema:
      type: object
      properties:
        user:
          $ref: '#/definitions/UserObject'
  401:
    description: Missing or invalid JWT token.
    schema:
      $ref: '#/definitions/ErrorResponse'
  500:
    description: Internal server error.
    schema:
      $ref: '#/definitions/ErrorResponse'
"""
