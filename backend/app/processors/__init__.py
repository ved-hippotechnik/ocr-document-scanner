"""
Base document processor interface for modular OCR processing
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np
from PIL import Image


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

            # Auto-fallback: if OCR extraction confidence is very low, try Vision
            if ocr_confidence < 0.25:
                vision_info = self._vision_extract_fallback(image, _logger)
                if vision_info and not vision_info.get('error'):
                    info = self._merge_with_vision(info, vision_info)
                    info['processing_method'] = 'vision_fallback'

            # Vision validation (when enabled and service available)
            if validate_with_vision:
                info = self._vision_validate(image, info, _logger)

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
