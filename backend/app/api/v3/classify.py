"""
api/v3/classify.py
==================
Document classification and quality assessment endpoints.

Routes
------
POST /api/v3/classify   — classify a document image without full extraction
POST /api/v3/quality    — assess image quality for OCR readability

Both routes accept JSON with a base64-encoded image (same schema as
``POST /api/v2/classify`` and ``POST /api/v2/quality`` in
``routes_enhanced.py``).

Authentication
--------------
Both routes require JWT Bearer token **or** API key.
"""
from __future__ import annotations

import time
import logging

import cv2
import numpy as np
from flask import Blueprint, request
import pytesseract

from app.auth.jwt_utils import token_or_api_key_required
from app.classification import document_classifier
from app.quality import quality_analyzer
from app.validation import validate_request_json, handle_processing_errors, ErrorHandler, ProcessingError, add_security_headers

logger = logging.getLogger(__name__)

v3_classify_bp = Blueprint("v3_classify", __name__, url_prefix="/api/v3")


@v3_classify_bp.after_request
def _add_security_headers(response):
    """Attach security headers to every response from this blueprint."""
    return add_security_headers(response)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@v3_classify_bp.route("/classify", methods=["POST"])
@token_or_api_key_required
@validate_request_json()
@handle_processing_errors()
def classify_document(validated_data):
    """
    Classify document type without extracting all fields.
    ---
    tags:
      - Classification
    operationId: classifyDocumentV3
    summary: Identify document type from an image
    description: >
      Submit a document image encoded as base64 JSON.  The endpoint runs the
      ML document classifier and returns the detected type together with a
      confidence score.  Unlike ``POST /api/v3/scan`` this endpoint does
      **not** extract individual fields — it is useful when you only need to
      know what kind of document you are dealing with.

      **Authentication**: JWT Bearer token or API key required.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - image
          properties:
            image:
              type: string
              description: Base64-encoded document image.
    responses:
      200:
        description: Document classified successfully.
      400:
        description: Could not identify document type (check image quality).
      401:
        description: Authentication required.
      500:
        description: Classification engine error.
    """
    start_time = time.time()

    # Extract the PIL image that validate_request_json decoded
    image = validated_data["image"]

    # Convert to OpenCV (BGR) for the classifier
    image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Run text OCR first, then feed both text + image to the classifier
    gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    ocr_text = pytesseract.image_to_string(gray, timeout=60)

    cls_results = document_classifier.classify_document(ocr_text, image_array)

    if cls_results:
        best = cls_results[0]
        classification_result = {
            "document_type": best.document_type,
            "confidence": best.confidence,
        }
    else:
        classification_result = {"document_type": "unknown", "confidence": 0.0}

    if classification_result["document_type"] == "unknown":
        raise ProcessingError(
            "Could not identify document type. Please check image quality and try again.",
            "DOCUMENT_NOT_DETECTED",
        )

    classification_result["processing_time"] = round(time.time() - start_time, 3)
    return ErrorHandler.create_success_response(classification_result)


@v3_classify_bp.route("/quality", methods=["POST"])
@token_or_api_key_required
@validate_request_json()
@handle_processing_errors()
def quality_check(validated_data):
    """
    Assess document image quality for OCR readability.
    ---
    tags:
      - Classification
    operationId: qualityCheckV3
    summary: Score an image's OCR-readability
    description: >
      Submit a document image encoded as base64 JSON.  The endpoint evaluates
      sharpness, contrast, brightness, and other factors to produce a
      0–1 quality score along with a list of specific issues found.

      Use this before submitting for scanning if you want to give the user
      feedback about image quality before committing to a full OCR run.

      **Authentication**: JWT Bearer token or API key required.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - image
          properties:
            image:
              type: string
              description: Base64-encoded document image.
    responses:
      200:
        description: Quality assessment completed.
      401:
        description: Authentication required.
      500:
        description: Quality assessment engine error.
    """
    start_time = time.time()

    image = validated_data["image"]
    image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    quality_result = quality_analyzer.analyze_quality(image_array)
    quality_result["processing_time"] = round(time.time() - start_time, 3)

    return ErrorHandler.create_success_response(quality_result)
