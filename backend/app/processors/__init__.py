"""
Base document processor interface for modular OCR processing
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
import io
import logging
import cv2
import numpy as np
from PIL import Image

_base_logger = logging.getLogger(__name__)


class DocumentProcessor(ABC):
    """Abstract base class for document processors"""
    
    def __init__(self, country: str, document_type: str):
        self.country = country
        self.document_type = document_type
        self.supported_languages = []
        self.confidence_threshold = 0.7
    
    @abstractmethod
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document matches this processor's criteria"""
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess image for optimal OCR results"""
        pass
    
    @abstractmethod
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from OCR text"""
        pass
    
    def process(self, image: np.ndarray, text_results: List[str] = None,
                language: str = None, validate_with_vision: bool = False) -> Dict[str, Any]:
        """Main processing pipeline with optional Claude Vision validation."""
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Preprocess if needed
            if text_results is None:
                processed_images = self.preprocess(image)
                text_results = self._ocr_images(processed_images, language=language)

            # Extract information
            info = self.extract_info(text_results)

            # Add metadata
            ocr_confidence = self._calculate_confidence(info)
            info.update({
                'document_type': self.get_display_name(),
                'processing_method': f"enhanced_{self.document_type}",
                'confidence': 'high' if ocr_confidence > self.confidence_threshold else 'medium',
                'country_code': self.get_country_code(),
                'processor': self.__class__.__name__
            })

            # MRZ extraction for passport-type documents
            if 'passport' in self.document_type:
                info = self._try_mrz_extraction(image, info)

            # Auto-fallback: if OCR extraction confidence is very low, try Vision
            if ocr_confidence < 0.25:
                vision_info = self._vision_extract_fallback(image, _logger)
                if vision_info and not vision_info.get('error'):
                    info = self._merge_with_vision(info, vision_info)
                    info['processing_method'] = 'vision_fallback'

            # Vision validation (when enabled and service available)
            if validate_with_vision:
                info = self._vision_validate(image, info, _logger)

            # Add per-field confidence scores
            info = self._add_field_confidence(info)

            return info

        except Exception as e:
            return {
                'error': str(e),
                'document_type': self.get_display_name(),
                'confidence': 'low',
                'processor': self.__class__.__name__
            }

    def _vision_validate(self, image: np.ndarray, info: Dict[str, Any], _logger) -> Dict[str, Any]:
        """Run Claude Vision validation on extracted fields."""
        try:
            from flask import current_app
            vision_service = getattr(current_app, 'vision_service', None)
            if vision_service is None:
                return info

            # Encode the image to bytes for the Vision API
            _, buf = cv2.imencode('.jpg', image)
            image_bytes = buf.tobytes()

            validation = vision_service.validate_extracted_fields(
                image_bytes, info, self.document_type
            )

            if validation.get('corrections'):
                info = self._apply_corrections(info, validation['corrections'])

            info['vision_validated'] = True
            info['vision_corrections'] = validation.get('corrections', [])
            info['vision_confidence'] = validation.get('confidence', 0.0)
            info['vision_missing_fields'] = validation.get('missing_fields', [])
        except RuntimeError:
            pass  # Outside Flask app context
        except Exception as e:
            _logger.warning(f"Vision validation skipped: {e}")

        return info

    @staticmethod
    def _apply_corrections(info: Dict[str, Any], corrections: list) -> Dict[str, Any]:
        """Merge Vision corrections into extracted fields."""
        for correction in corrections:
            field = correction.get('field')
            corrected = correction.get('corrected')
            if field and corrected and field in info:
                info[field] = corrected
        return info

    def _vision_extract_fallback(self, image: np.ndarray, _logger) -> Optional[Dict[str, Any]]:
        """Attempt full field extraction via Claude Vision when OCR confidence is very low."""
        try:
            from flask import current_app
            vision_service = getattr(current_app, 'vision_service', None)
            if vision_service is None:
                return None

            _, buf = cv2.imencode('.jpg', image)
            image_bytes = buf.tobytes()

            return vision_service.extract_fields_direct(image_bytes, self.document_type)
        except RuntimeError:
            return None
        except Exception as e:
            _logger.warning(f"Vision extraction fallback failed: {e}")
            return None

    @staticmethod
    def _merge_with_vision(ocr_info: Dict[str, Any], vision_info: Dict[str, Any]) -> Dict[str, Any]:
        """Merge Vision-extracted fields into OCR results, preferring Vision for empty OCR fields."""
        metadata_keys = {
            'document_type', 'processing_method', 'confidence',
            'country_code', 'processor', 'error',
            'vision_notes', 'vision_confidence',
        }
        for key, value in vision_info.items():
            if key in metadata_keys:
                continue
            # Only override if OCR field is empty/None
            if value and (not ocr_info.get(key) or ocr_info.get(key) is None):
                ocr_info[key] = value
        ocr_info['vision_assisted'] = True
        return ocr_info

    def _ocr_images(self, images: List[np.ndarray], language: str = None) -> List[str]:
        """Perform OCR on preprocessed images"""
        import pytesseract
        import re as _re

        text_results = []
        configs = self._get_ocr_configs()

        # If an explicit language was requested, override -l in every config
        if language:
            configs = [_re.sub(r'-l\s+\S+', f'-l {language}', c) for c in configs]

        for image in images:
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config)
                    if text.strip():
                        text_results.append(text)
                except Exception:
                    continue

        return text_results

    def _get_default_language(self) -> str:
        """Get the default language for this processor based on supported_languages"""
        if self.supported_languages:
            return '+'.join(self.supported_languages)
        return 'eng'

    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations for this document type"""
        lang = self._get_default_language()
        return [
            f'--psm 6 --oem 3 -l {lang}',
            f'--psm 4 --oem 3 -l {lang}',
            f'--psm 3 --oem 3 -l {lang}'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence based on extracted information"""
        confidence = 0.0

        # Check for key fields
        key_fields = ['document_number', 'full_name', 'date_of_birth', 'nationality']

        for field in key_fields:
            if info.get(field) and str(info[field]).strip():
                confidence += 0.25

        return confidence

    def _add_field_confidence(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Add per-field confidence scores to extracted info.

        Produces a 'field_confidence' dict mapping field names to
        ``{value, confidence, method}`` triples.
        """
        metadata_keys = {
            'document_type', 'processing_method', 'confidence',
            'country_code', 'processor', 'error', 'raw_text',
            'vision_validated', 'vision_corrections', 'vision_confidence',
            'vision_missing_fields', 'vision_assisted', 'vision_notes',
            'field_confidence',
        }

        field_conf: Dict[str, Any] = {}
        for key, value in info.items():
            if key in metadata_keys:
                continue

            method = 'regex_match'
            score = 0.0

            if value and str(value).strip():
                score = 0.5  # base: has a value

                # Bonus: regex matched a structured pattern (date, ID number)
                if isinstance(value, str) and len(value) > 1:
                    score += 0.3

                # Vision corrections override
                for corr in info.get('vision_corrections', []):
                    if corr.get('field') == key:
                        method = 'vision_corrected'
                        score = 0.85
                        break
                else:
                    if info.get('vision_validated'):
                        method = 'vision_validated'
                        score = min(score + 0.15, 1.0)

            field_conf[key] = {
                'value': value,
                'confidence': round(min(score, 1.0), 2),
                'method': method,
            }

        info['field_confidence'] = field_conf
        return info
    
    # ------------------------------------------------------------------
    # MRZ helpers (used by passport processors)
    # ------------------------------------------------------------------

    def _try_mrz_extraction(self, image: np.ndarray, info: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt MRZ extraction from a passport image and fill gaps in *info*.

        Uses ``passporteye.read_mrz`` when available.  Fields are only
        populated when the regex-based extraction left them empty.
        """
        try:
            from passporteye import read_mrz as _read_mrz
        except ImportError:
            return info

        try:
            # passporteye expects a file-like object
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            import io as _io
            buf = _io.BytesIO()
            pil_img.save(buf, format='JPEG')
            buf.seek(0)

            mrz = _read_mrz(buf)
            if mrz is None:
                return info

            mrz_data = mrz.to_dict()

            # Map MRZ fields → info keys, only fill blanks
            _map = {
                'number': 'document_number',
                'names': 'given_name',
                'surname': 'surname',
                'nationality': 'nationality',
                'sex': 'sex',
                'date_of_birth': 'date_of_birth',
                'expiration_date': 'date_of_expiry',
            }

            for mrz_key, info_key in _map.items():
                mrz_val = mrz_data.get(mrz_key)
                if mrz_val and not info.get(info_key):
                    # Clean angle-bracket padding from passporteye output
                    if isinstance(mrz_val, str):
                        mrz_val = mrz_val.replace('<', ' ').strip()
                    info[info_key] = mrz_val

            # Derive full_name if missing
            if not info.get('full_name'):
                given = info.get('given_name', '') or ''
                surname = info.get('surname', '') or ''
                full = f"{given} {surname}".strip()
                if full:
                    info['full_name'] = full

            info['mrz_parsed'] = True
        except Exception as exc:
            _base_logger.debug("MRZ extraction failed: %s", exc)

        return info

    # ------------------------------------------------------------------

    def get_display_name(self) -> str:
        """Get human-readable display name for document type"""
        display_names = {
            'emirates_id': 'ID Card',
            'aadhaar_card': 'Aadhaar Card',
            'driving_license': 'Driving License',
            'drivers_license': 'Driver\'s License',
            'passport': 'Passport',
            'state_id': 'State ID',
            'personalausweis': 'Personal ID',
            'mynumber_card': 'My Number Card'
        }
        return display_names.get(self.document_type, self.document_type.replace('_', ' ').title())
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        country_codes = {
            'United Arab Emirates': 'UAE',
            'India': 'IND',
            'United States': 'USA',
            'United Kingdom': 'GBR',
            'Germany': 'DEU',
            'Canada': 'CAN',
            'Japan': 'JPN',
            'Singapore': 'SGP'
        }
        return country_codes.get(self.country, self.country[:3].upper())


def process_pdf(file_bytes: bytes, processor: Optional['DocumentProcessor'] = None,
                 validate_with_vision: bool = False, max_pages: int = 10) -> List[Dict[str, Any]]:
    """Convert PDF pages to images and process each page.

    If *processor* is ``None``, each page is auto-detected via the global
    ``processor_registry``.
    """
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        return [{'error': 'pdf2image not installed — run: pip install pdf2image', 'page': 1}]

    try:
        images = convert_from_bytes(file_bytes, dpi=300)
    except Exception as e:
        return [{'error': f'PDF conversion failed: {e}', 'page': 1}]

    results = []
    for i, pil_img in enumerate(images[:max_pages]):
        img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        page_processor = processor
        if page_processor is None:
            # Auto-detect document type per page
            import pytesseract
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)
            _, page_processor = processor_registry.detect_document_type(text, img_array)

        if page_processor:
            result = page_processor.process(img_array, validate_with_vision=validate_with_vision)
        else:
            result = {'error': 'Could not detect document type', 'raw_text': text[:500] if 'text' in dir() else ''}

        result['page'] = i + 1
        results.append(result)
    return results


def dewarp_document(image: np.ndarray) -> np.ndarray:
    """Detect document edges and apply perspective correction.

    Falls back to the original image if a quadrilateral contour
    cannot be found.
    """
    orig = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for cnt in contours[:5]:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype('float32')
            # Order: top-left, top-right, bottom-right, bottom-left
            s = pts.sum(axis=1)
            d = np.diff(pts, axis=1)
            ordered = np.array([
                pts[np.argmin(s)],
                pts[np.argmin(d)],
                pts[np.argmax(s)],
                pts[np.argmax(d)],
            ], dtype='float32')

            w = max(
                np.linalg.norm(ordered[0] - ordered[1]),
                np.linalg.norm(ordered[2] - ordered[3]),
            )
            h = max(
                np.linalg.norm(ordered[0] - ordered[3]),
                np.linalg.norm(ordered[1] - ordered[2]),
            )

            dst = np.array([
                [0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]
            ], dtype='float32')

            M = cv2.getPerspectiveTransform(ordered, dst)
            return cv2.warpPerspective(orig, M, (int(w), int(h)))

    return orig  # no quad found


class ProcessorRegistry:
    """Registry for managing document processors"""
    
    def __init__(self):
        self.processors: List[DocumentProcessor] = []
    
    def register(self, processor: DocumentProcessor):
        """Register a new processor"""
        self.processors.append(processor)
    
    def detect_document_type(self, text: str, image: np.ndarray = None) -> Tuple[str, Optional[DocumentProcessor]]:
        """Detect document type and return appropriate processor"""
        for processor in self.processors:
            if processor.detect(text, image):
                return processor.get_display_name(), processor
        
        return 'Unknown', None
    
    def get_processor(self, country: str, document_type: str) -> Optional[DocumentProcessor]:
        """Get specific processor by country and document type"""
        for processor in self.processors:
            if processor.country == country and processor.document_type == document_type:
                return processor
        return None
    
    def list_supported_documents(self) -> List[Dict[str, str]]:
        """List all supported document types"""
        return [
            {
                'country': proc.country,
                'document_type': proc.document_type,
                'display_name': proc.get_display_name(),
                'country_code': proc.get_country_code()
            }
            for proc in self.processors
        ]


# Global registry instance
processor_registry = ProcessorRegistry()
