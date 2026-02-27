# Utility modules for OCR document scanner
from .text_processing import (
    normalize_date,
    format_month_date,
    clean_document_number,
    clean_name,
    is_ocr_artifact,
    is_valid_name_part,
    extract_place_of_issue,
    detect_document_type,
    extract_nationality,
    extract_document_info,
    validate_uploaded_file,
    correct_name_order,
)

__all__ = [
    'normalize_date',
    'format_month_date',
    'clean_document_number',
    'clean_name',
    'is_ocr_artifact',
    'is_valid_name_part',
    'extract_place_of_issue',
    'detect_document_type',
    'extract_nationality',
    'extract_document_info',
    'validate_uploaded_file',
    'correct_name_order',
]
