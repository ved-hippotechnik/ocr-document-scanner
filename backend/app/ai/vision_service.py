"""
Claude Vision Service for document classification, field validation, and extraction.

Provides a hybrid VLM layer that:
- Classifies document types zero-shot from images
- Validates and corrects OCR-extracted fields
- Falls back to full VLM extraction when Tesseract fails
"""

import base64
import json
import logging
import mimetypes
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Map of our internal document type codes to display names
DOCUMENT_TYPE_MAP = {
    'aadhaar': 'Aadhaar Card',
    'emirates_id': 'Emirates ID',
    'driving_license': 'Indian Driving License',
    'passport': 'Indian Passport',
    'us_drivers_license': 'US Driver\'s License',
    'us_green_card': 'US Green Card',
    'pan_card': 'PAN Card',
    'voter_id': 'Voter ID',
    'uk_passport': 'UK Passport',
    'canadian_passport': 'Canadian Passport',
    'australian_passport': 'Australian Passport',
    'german_passport': 'German Passport',
    'eu_id_card': 'EU ID Card',
    'japanese_my_number': 'Japanese My Number Card',
}

# Reverse map: display name → code
DISPLAY_NAME_TO_CODE = {}
for code, name in DOCUMENT_TYPE_MAP.items():
    DISPLAY_NAME_TO_CODE[name.lower()] = code
    DISPLAY_NAME_TO_CODE[code] = code

# Common aliases Claude might use
_ALIASES = {
    'aadhaar': 'aadhaar',
    'aadhar': 'aadhaar',
    'emirates id card': 'emirates_id',
    'uae id': 'emirates_id',
    'indian driving license': 'driving_license',
    'indian driving licence': 'driving_license',
    'driving licence': 'driving_license',
    'indian passport': 'passport',
    'us driver\'s license': 'us_drivers_license',
    'us drivers license': 'us_drivers_license',
    'american driver\'s license': 'us_drivers_license',
    'green card': 'us_green_card',
    'permanent resident card': 'us_green_card',
    'pan card': 'pan_card',
    'voter id': 'voter_id',
    'election card': 'voter_id',
    'uk passport': 'uk_passport',
    'british passport': 'uk_passport',
    'canadian passport': 'canadian_passport',
    'australian passport': 'australian_passport',
    'german passport': 'german_passport',
    'eu id card': 'eu_id_card',
    'european id card': 'eu_id_card',
    'my number card': 'japanese_my_number',
    'japanese my number': 'japanese_my_number',
    'passport': 'passport',
}
DISPLAY_NAME_TO_CODE.update(_ALIASES)

# Standard fields by document type for extraction prompts
DOCUMENT_FIELDS = {
    'aadhaar': ['full_name', 'document_number', 'date_of_birth', 'gender', 'address', 'father_name'],
    'emirates_id': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'gender', 'unified_number'],
    'driving_license': ['full_name', 'license_number', 'date_of_birth', 'date_of_issue', 'date_of_expiry', 'address', 'vehicle_class'],
    'passport': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'date_of_issue', 'gender', 'place_of_birth', 'place_of_issue'],
    'us_drivers_license': ['full_name', 'license_number', 'date_of_birth', 'date_of_expiry', 'address', 'state', 'gender'],
    'us_green_card': ['full_name', 'document_number', 'date_of_birth', 'country_of_birth', 'date_of_issue', 'date_of_expiry', 'category'],
    'pan_card': ['full_name', 'document_number', 'date_of_birth', 'father_name'],
    'voter_id': ['full_name', 'document_number', 'date_of_birth', 'gender', 'address', 'father_name'],
    'uk_passport': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'gender', 'place_of_birth'],
    'canadian_passport': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'gender', 'place_of_birth'],
    'australian_passport': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'gender', 'place_of_birth'],
    'german_passport': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'gender', 'place_of_birth'],
    'eu_id_card': ['full_name', 'document_number', 'nationality', 'date_of_birth', 'date_of_expiry', 'gender'],
    'japanese_my_number': ['full_name', 'document_number', 'date_of_birth', 'gender', 'address'],
}


def _guess_media_type(image_data: bytes) -> str:
    """Guess MIME type from image magic bytes."""
    if image_data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if image_data[:2] == b'\xff\xd8':
        return 'image/jpeg'
    if image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
        return 'image/webp'
    if image_data[:3] == b'GIF':
        return 'image/gif'
    if image_data[:4] in (b'II*\x00', b'MM\x00*'):
        return 'image/tiff'
    if image_data[:2] == b'BM':
        return 'image/bmp'
    return 'image/jpeg'


class ClaudeVisionService:
    """Wrapper around the Anthropic API for document vision tasks."""

    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-20250514'):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.timeout = 30

    def _encode_image(self, image_data: bytes) -> tuple:
        """Encode image bytes to base64 and detect media type."""
        media_type = _guess_media_type(image_data)
        b64 = base64.standard_b64encode(image_data).decode('utf-8')
        return media_type, b64

    # ------------------------------------------------------------------
    # 1. Document Classification
    # ------------------------------------------------------------------

    def classify_document(self, image_data: bytes) -> Dict:
        """
        Classify a document image using Claude Vision.

        Returns:
            {
                'document_type': str,       # internal code
                'document_name': str,       # display name
                'confidence': float,        # 0.0–1.0
                'reasoning': str,           # why this type
                'classifier': 'vision',
            }
        """
        media_type, b64 = self._encode_image(image_data)
        known_types = ', '.join(DOCUMENT_TYPE_MAP.values())

        system_prompt = (
            "You are a document classification expert. Given an image of an identity document, "
            "determine its type. Respond ONLY with valid JSON, no markdown fences.\n\n"
            f"Known document types: {known_types}\n\n"
            "Response schema:\n"
            '{"document_type": "<type name>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}\n\n'
            "If the image is not an identity document or is unrecognizable, "
            'use document_type "unknown" with low confidence.'
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                system=system_prompt,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': 'Classify this document.'},
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': media_type,
                                'data': b64,
                            },
                        },
                    ],
                }],
            )

            raw = response.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)

            doc_type_raw = result.get('document_type', 'unknown').lower().strip()
            doc_code = DISPLAY_NAME_TO_CODE.get(doc_type_raw, 'unknown')
            doc_name = DOCUMENT_TYPE_MAP.get(doc_code, 'Unknown Document')

            return {
                'document_type': doc_code,
                'document_name': doc_name,
                'confidence': float(result.get('confidence', 0.0)),
                'reasoning': result.get('reasoning', ''),
                'classifier': 'vision',
            }

        except Exception as e:
            logger.error(f"Vision classification failed: {e}")
            return {
                'document_type': 'unknown',
                'document_name': 'Unknown Document',
                'confidence': 0.0,
                'reasoning': f'Vision API error: {e}',
                'classifier': 'vision',
                'error': str(e),
            }

    # ------------------------------------------------------------------
    # 2. Field Validation / Correction
    # ------------------------------------------------------------------

    def validate_extracted_fields(
        self,
        image_data: bytes,
        extracted_info: Dict,
        document_type: str,
    ) -> Dict:
        """
        Validate OCR-extracted fields against the document image.

        Returns:
            {
                'verified_fields': {field: value, ...},
                'corrections': [{'field': str, 'original': str, 'corrected': str, 'reason': str}, ...],
                'confidence': float,
                'missing_fields': [str, ...],
            }
        """
        media_type, b64 = self._encode_image(image_data)

        # Build a clean representation of extracted fields
        fields_str = json.dumps(
            {k: v for k, v in extracted_info.items()
             if k not in ('document_type', 'processing_method', 'confidence',
                          'country_code', 'processor', 'error')
             and v is not None},
            indent=2,
        )

        doc_name = DOCUMENT_TYPE_MAP.get(document_type, document_type)

        system_prompt = (
            "You are a document data verification expert. You will be given an image of a "
            f"{doc_name} and a set of fields extracted by OCR.\n\n"
            "Your job:\n"
            "1. Compare each extracted field against what you see in the document image\n"
            "2. Correct any OCR errors (e.g., letter O instead of zero, I instead of 1)\n"
            "3. Identify any fields that are wrong or missing\n\n"
            "Respond ONLY with valid JSON, no markdown fences.\n"
            "Response schema:\n"
            "{\n"
            '  "verified_fields": {<field_name>: <corrected_value>, ...},\n'
            '  "corrections": [{"field": "<name>", "original": "<ocr_value>", "corrected": "<correct_value>", "reason": "<why>"}],\n'
            '  "missing_fields": ["<field_name>", ...],\n'
            '  "confidence": <0.0-1.0>\n'
            "}"
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f'OCR extracted these fields from a {doc_name}:\n\n{fields_str}\n\nVerify and correct them against the document image.',
                        },
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': media_type,
                                'data': b64,
                            },
                        },
                    ],
                }],
            )

            raw = response.content[0].text.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)

            return {
                'verified_fields': result.get('verified_fields', {}),
                'corrections': result.get('corrections', []),
                'missing_fields': result.get('missing_fields', []),
                'confidence': float(result.get('confidence', 0.0)),
            }

        except Exception as e:
            logger.error(f"Vision field validation failed: {e}")
            return {
                'verified_fields': {},
                'corrections': [],
                'missing_fields': [],
                'confidence': 0.0,
                'error': str(e),
            }

    # ------------------------------------------------------------------
    # 3. Direct Field Extraction (full VLM, no Tesseract)
    # ------------------------------------------------------------------

    def extract_fields_direct(
        self,
        image_data: bytes,
        document_type: str,
    ) -> Dict:
        """
        Extract all fields directly from a document image using Vision.
        Used as fallback when Tesseract extraction confidence is too low.

        Returns a dict matching the processor output format.
        """
        media_type, b64 = self._encode_image(image_data)
        doc_name = DOCUMENT_TYPE_MAP.get(document_type, document_type)
        fields = DOCUMENT_FIELDS.get(document_type, [
            'full_name', 'document_number', 'date_of_birth', 'nationality',
        ])
        fields_list = ', '.join(fields)

        system_prompt = (
            f"You are a document data extraction expert. Extract all fields from this {doc_name}.\n\n"
            f"Expected fields: {fields_list}\n\n"
            "Rules:\n"
            "- Use null for any field you cannot read\n"
            "- Dates should be in DD/MM/YYYY format\n"
            "- Names should be in their original script and also transliterated to Latin if applicable\n"
            "- Document numbers should preserve exact formatting\n\n"
            "Respond ONLY with valid JSON, no markdown fences.\n"
            "Response schema:\n"
            "{\n"
            '  "fields": {<field_name>: <value or null>, ...},\n'
            '  "confidence": <0.0-1.0>,\n'
            '  "notes": "<any observations about document quality or readability>"\n'
            "}"
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f'Extract all fields from this {doc_name}.',
                        },
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': media_type,
                                'data': b64,
                            },
                        },
                    ],
                }],
            )

            raw = response.content[0].text.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            result = json.loads(raw)
            extracted = result.get('fields', {})

            # Add metadata to match processor output format
            extracted['document_type'] = doc_name
            extracted['processing_method'] = 'vision_extraction'
            extracted['confidence'] = 'high' if result.get('confidence', 0) > 0.7 else 'medium'
            extracted['vision_notes'] = result.get('notes', '')
            extracted['vision_confidence'] = float(result.get('confidence', 0.0))

            return extracted

        except Exception as e:
            logger.error(f"Vision field extraction failed: {e}")
            return {
                'document_type': doc_name,
                'processing_method': 'vision_extraction',
                'confidence': 'low',
                'error': str(e),
            }
