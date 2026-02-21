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
    
    def process(self, image: np.ndarray, text_results: List[str] = None, language: str = None) -> Dict[str, Any]:
        """Main processing pipeline"""
        try:
            # Preprocess if needed
            if text_results is None:
                processed_images = self.preprocess(image)
                text_results = self._ocr_images(processed_images, language=language)

            # Extract information
            info = self.extract_info(text_results)

            # Add metadata
            info.update({
                'document_type': self.get_display_name(),
                'processing_method': f"enhanced_{self.document_type}",
                'confidence': 'high' if self._calculate_confidence(info) > self.confidence_threshold else 'medium',
                'country_code': self.get_country_code(),
                'processor': self.__class__.__name__
            })

            return info

        except Exception as e:
            return {
                'error': str(e),
                'document_type': self.get_display_name(),
                'confidence': 'low',
                'processor': self.__class__.__name__
            }

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
