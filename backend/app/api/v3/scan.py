"""
api/v3/scan.py
==============
POST /api/v3/scan — recommended scanning endpoint.

Implementation ported from ``app/routes_improved.py`` (the ``improved``
blueprint's ``scan_document_v3`` view), which provides:

  - Strict filename + file-security validation
  - Marshmallow parameter schema validation
  - Image dimension checks (100 x 100 minimum, 10 000 x 10 000 maximum)
  - Optional image quality gate (rejects images scoring below 0.3)
  - Optional image enhancement (denoising + adaptive threshold)
  - Configurable OCR timeout (``OCR_TIMEOUT`` config key)
  - Idempotency support (via ``@idempotent`` decorator)
  - Back-pressure limiting (max 20 concurrent requests)
  - Prometheus metric emission (``ocr_processing_time``, ``ocr_timeout_count``)
  - ScanHistory DB persistence for both successful and failed attempts

Authentication
--------------
Every route in this blueprint requires either a valid JWT Bearer token **or**
a valid API key in the ``X-API-Key`` header (``@token_or_api_key_required``).
"""
from __future__ import annotations

import time
import traceback
import logging
from datetime import datetime, timezone

import cv2
import numpy as np
import pytesseract
from flask import Blueprint, current_app, g, jsonify, request
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import RequestEntityTooLarge

from app.auth.jwt_utils import token_or_api_key_required
from app.processors.registry import processor_registry
from app.rate_limiter import ratelimit_scan
from app.validation.schemas import DocumentScanSchema, FileUploadValidator
from app.security.file_validator import FileValidator
from app.database import db, ScanHistory
from app.resilience import idempotent, backpressure, structured_error
from app.monitoring import ocr_processing_time, ocr_timeout_count

logger = logging.getLogger(__name__)

v3_scan_bp = Blueprint("v3_scan", __name__, url_prefix="/api/v3")

# Module-level validator instances (created once at import time)
_scan_schema = DocumentScanSchema()
_file_upload_validator = FileUploadValidator()
_file_security_validator = FileValidator()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _assess_image_quality(image: np.ndarray) -> float:
    """Return a 0-1 quality score for OCR readability.

    Combines blur (Laplacian variance), contrast, and brightness into a
    weighted score.  Returns 0.5 on error so a bad metric never blocks
    processing outright.
    """
    try:
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        min_val = float(np.min(image))
        max_val = float(np.max(image))
        contrast = (max_val - min_val) / 255.0
        brightness = float(np.mean(image)) / 255.0

        blur_score = min(laplacian_var / 1000.0, 1.0)
        quality_score = blur_score * 0.5 + contrast * 0.3 + brightness * 0.2
        return float(min(max(quality_score, 0.0), 1.0))
    except Exception as exc:
        current_app.logger.error("Quality assessment error: %s", exc)
        return 0.5


def _enhance_image(image: np.ndarray) -> np.ndarray:
    """Apply denoising + adaptive threshold for better OCR results.

    Falls back to the original image on error.
    """
    try:
        denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        enhanced = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2,
        )
        return enhanced
    except Exception as exc:
        current_app.logger.error("Image enhancement error: %s", exc)
        return image


def _validate_extracted_data(data: dict, doc_type: str) -> dict:
    """Validate required fields for known document types.

    Returns a dict with ``is_valid`` (bool), ``errors`` (list), and
    ``warnings`` (list).
    """
    result: dict = {"is_valid": True, "errors": [], "warnings": []}

    if not data:
        result["is_valid"] = False
        result["errors"].append("No data extracted")
        return result

    required_fields: dict[str, list[str]] = {
        "passport": ["passport_number", "name", "date_of_birth"],
        "emirates_id": ["id_number", "name"],
        "aadhaar_card": ["aadhaar_number", "name"],
        "driving_license": ["license_number", "name"],
    }

    for field in required_fields.get(doc_type, []):
        if not data.get(field):
            result["errors"].append(f"Missing required field: {field}")
            result["is_valid"] = False

    if "expiry_date" in data:
        try:
            expiry = datetime.strptime(data["expiry_date"], "%d/%m/%Y")
            if expiry < datetime.now():
                result["warnings"].append("Document appears to be expired")
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@v3_scan_bp.route("/scan", methods=["POST"])
@token_or_api_key_required
@ratelimit_scan()
@idempotent()
@backpressure(max_concurrent=20)
def scan_document_v3():
    """
    Scan a single document image (v3 — recommended).
    ---
    tags:
      - Scanning
    operationId: scanDocumentV3
    summary: Upload and OCR a document (recommended endpoint)
    description: >
      Upload a document image (JPEG, PNG, BMP, TIFF, or PDF) as
      multipart/form-data.  The engine validates and sanitises the file,
      auto-classifies the document type using the ML classifier, applies the
      matching specialist OCR processor, and returns structured extracted
      fields together with the raw OCR text.

      Supported document types: Emirates ID, Aadhaar Card, Indian Driving
      License, Passport (various countries), US Driver's License.

      **Authentication**: JWT Bearer token **or** ``X-API-Key`` header required.

      **Rate limit**: 10 requests / minute per IP.
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: image
        type: file
        required: true
        description: >
          Document image file.  Accepted: image/jpeg, image/png, image/bmp,
          image/tiff, application/pdf.  Maximum size: 16 MB.
          Minimum dimensions: 100x100 px.
      - in: formData
        name: language
        type: string
        required: false
        description: ISO 639-3 language code for OCR hints (e.g. eng, ara, hin).
        example: eng
      - in: formData
        name: document_type
        type: string
        required: false
        default: auto
        description: Force a specific document processor; 'auto' (default) auto-detects.
        enum:
          - auto
          - emirates_id
          - aadhaar_card
          - driving_license
          - passport
          - us_drivers_license
      - in: formData
        name: validate_with_vision
        type: boolean
        required: false
        default: false
        description: Pass the image through Claude Vision for additional validation.
      - in: formData
        name: quality_check
        type: boolean
        required: false
        default: true
        description: Reject images with a quality score below 0.3.
      - in: formData
        name: enhance_image
        type: boolean
        required: false
        default: false
        description: Apply denoising and sharpening before OCR.
    responses:
      200:
        description: Document scanned and data extracted successfully.
      400:
        description: Bad request — missing file, invalid format, poor quality, or unsupported type.
      413:
        description: File exceeds the 16 MB upload limit.
      429:
        description: Rate limit exceeded.
      500:
        description: Internal OCR processing error.
    """
    # Track start time for performance metrics
    start_time = time.time()
    if not hasattr(g, "request_start_time"):
        g.request_start_time = start_time

    try:
        # Step 1: Validate request has file
        if "image" not in request.files:
            return structured_error("Missing required file", "FILE_REQUIRED", 400)

        file = request.files["image"]

        # Step 2: Validate filename
        if not file.filename:
            return structured_error("Invalid file", "INVALID_FILENAME", 400)

        if not _file_upload_validator.validate_filename(file.filename):
            return structured_error(
                "Invalid filename", "INVALID_FILENAME", 400,
                details=f"Filename contains invalid characters or extension: {file.filename}",
            )

        # Step 3: Security validation (content sniffing, size)
        is_valid, error_msg, file_metadata = _file_security_validator.validate_file(file)
        if not is_valid:
            current_app.logger.warning("File validation failed: %s", error_msg)
            if hasattr(current_app, "security_logger"):
                current_app.security_logger.log_file_upload(
                    user_id=g.get("user_id", "anonymous"),
                    filename=file.filename,
                    file_size=file_metadata.get("size", 0),
                    validation_result=error_msg,
                )
            return structured_error(
                "File validation failed", "FILE_VALIDATION_FAILED", 400, details=error_msg
            )

        # Reset file pointer after validation
        file.seek(0)

        # Step 4: Validate form parameters via Marshmallow schema
        try:
            params = _scan_schema.load(request.form.to_dict())
        except MarshmallowValidationError as exc:
            return structured_error(
                "Invalid parameters", "INVALID_PARAMETERS", 400,
                details=exc.messages,
            )

        # Step 5: Read and validate image data
        try:
            file_bytes = file.read()
            if not file_bytes:
                return structured_error("Empty file", "EMPTY_FILE", 400)

            img_array = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                return structured_error(
                    "Invalid image data", "INVALID_IMAGE", 400,
                    details="Unable to decode image data. File may be corrupted or not a valid image.",
                )

            height, width = img.shape[:2]
            if height < 100 or width < 100:
                return structured_error(
                    "Image too small", "IMAGE_TOO_SMALL", 400,
                    details=f"Image dimensions {width}x{height} are too small. Minimum is 100x100.",
                )

            if height > 10000 or width > 10000:
                return structured_error(
                    "Image too large", "IMAGE_TOO_LARGE", 400,
                    details=f"Image dimensions {width}x{height} are too large. Maximum is 10000x10000.",
                )
        except Exception as exc:
            current_app.logger.error(
                "Image processing error: %s (request_id=%s)", exc,
                getattr(g, "request_id", "unknown"),
            )
            return structured_error(
                "Image processing failed", "IMAGE_PROCESSING_ERROR", 400, details=exc
            )

        # Step 6: OCR processing pipeline
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Optional quality gate
            quality_score = None
            if params.get("quality_check", True):
                quality_score = _assess_image_quality(gray)
                if quality_score < 0.3:
                    return structured_error(
                        "Poor image quality", "POOR_IMAGE_QUALITY", 400,
                        details=(
                            f"Image quality score {quality_score:.2f} is too low. "
                            "Please provide a clearer image."
                        ),
                    )

            # Optional image enhancement
            if params.get("enhance_image", False):
                gray = _enhance_image(gray)

            # OCR with configurable timeout
            ocr_timeout = current_app.config.get("OCR_TIMEOUT", 60)
            ocr_start = time.time()
            try:
                initial_text = pytesseract.image_to_string(
                    gray,
                    lang=params.get("language", "eng"),
                    timeout=ocr_timeout,
                )
            except RuntimeError:
                # pytesseract raises RuntimeError on timeout
                ocr_timeout_count.labels(document_type="unknown").inc()
                current_app.logger.error(
                    "OCR timed out after %ds (request_id=%s)", ocr_timeout,
                    getattr(g, "request_id", "unknown"),
                )
                return structured_error(
                    "OCR processing timed out", "OCR_TIMEOUT", 504,
                    details=f"Tesseract did not finish within {ocr_timeout}s",
                    component="tesseract",
                )
            finally:
                ocr_elapsed = time.time() - ocr_start
                ocr_processing_time.labels(
                    document_type="unknown", status="completed"
                ).observe(ocr_elapsed)

            if not initial_text or len(initial_text.strip()) < 10:
                return structured_error(
                    "No text detected", "NO_TEXT_DETECTED", 400,
                    details="Unable to extract text from image. Image may be blank or text is not readable.",
                )

            # Detect or force document type
            doc_type = params.get("document_type", "auto")
            if doc_type == "auto":
                doc_display_name, processor = processor_registry.detect_document_type(
                    initial_text, img
                )
            else:
                processor = processor_registry.get_processor(doc_type)
                doc_display_name = doc_type

            if not processor:
                return structured_error(
                    "Document type not supported", "UNSUPPORTED_DOCUMENT", 400,
                    details=(
                        f'Document type "{doc_type}" is not supported or could not be detected'
                    ),
                )

            # Run specialist processor
            validate_vision = params.get("validate_with_vision", False)
            result = processor.process(img, validate_with_vision=validate_vision)

            # Optional field-level validation
            if params.get("validate_document", True):
                validation_result = _validate_extracted_data(result, doc_display_name)
                if not validation_result["is_valid"]:
                    result["validation"] = validation_result

            # Persist to database
            scan_record = ScanHistory(
                user_id=g.get("user_id"),
                session_id=params.get("session_id", "unknown"),
                document_type=doc_display_name,
                confidence_score=result.get("confidence", 0),
                quality_score=quality_score,
                processing_time=(time.time() - g.request_start_time),
                file_size=len(file_bytes),
                file_format=file_metadata.get("mime_type", "unknown"),
                filename=file_metadata.get("safe_filename"),
                extracted_data=str(result),
                ip_address=g.get("client_ip", request.remote_addr),
                user_agent=request.user_agent.string,
                status="completed",
            )
            db.session.add(scan_record)
            try:
                db.session.commit()
            except Exception as db_err:
                db.session.rollback()
                current_app.logger.error(
                    "DB commit failed for scan record: %s (request_id=%s)", db_err,
                    getattr(g, "request_id", "unknown"),
                )

            # Update metric with the resolved document type
            ocr_processing_time.labels(
                document_type=doc_display_name, status="success"
            ).observe(time.time() - g.request_start_time)

            return jsonify({
                "success": True,
                "document_type": doc_display_name,
                "data": result,
                "metadata": {
                    "scan_id": getattr(scan_record, "id", None),
                    "quality_score": quality_score,
                    "processing_time": round(time.time() - g.request_start_time, 3),
                    "file_hash": file_metadata.get("hash"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }), 200

        except Exception as exc:
            current_app.logger.error(
                "OCR processing error: %s (request_id=%s)\n%s", exc,
                getattr(g, "request_id", "unknown"), traceback.format_exc(),
            )
            # Persist failed attempt
            try:
                failed_record = ScanHistory(
                    user_id=g.get("user_id"),
                    session_id=params.get("session_id", "unknown"),
                    document_type="unknown",
                    error_message=str(exc),
                    file_size=len(file_bytes) if "file_bytes" in dir() else 0,
                    filename=file.filename,
                    ip_address=g.get("client_ip", request.remote_addr),
                    user_agent=request.user_agent.string,
                    status="failed",
                )
                db.session.add(failed_record)
                db.session.commit()
            except Exception as db_err:
                db.session.rollback()
                current_app.logger.error("DB commit failed for failed scan record: %s", db_err)

            return structured_error("Processing failed", "PROCESSING_ERROR", 500, details=exc, component="ocr")

    except RequestEntityTooLarge:
        return structured_error(
            "File too large", "FILE_TOO_LARGE", 413,
            details=(
                f"File size exceeds maximum allowed size of "
                f"{current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)} bytes"
            ),
        )
    except Exception as exc:
        current_app.logger.error(
            "Unexpected error (request_id=%s): %s\n%s",
            getattr(g, "request_id", "unknown"), exc, traceback.format_exc(),
        )
        return structured_error("Internal server error", "INTERNAL_ERROR", 500, details=exc)
