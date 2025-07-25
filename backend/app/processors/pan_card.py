"""
PAN Card processor for India
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class PANCardProcessor(DocumentProcessor):
    """Processor for Indian PAN (Permanent Account Number) Cards"""
    
    def __init__(self):
        super().__init__('India', 'pan_card')
        self.supported_languages = ['eng', 'hin']
        self.confidence_threshold = 0.7
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a PAN card"""
        text_lower = text.lower()
        
        # Look for PAN card specific indicators
        pan_indicators = [
            'permanent account number',
            'income tax department',
            'govt. of india',
            'government of india',
            'pan card',
            'account number',
            'signature',
            'father\'s name',
            'date of birth'
        ]
        
        # Check for PAN number pattern (5 letters + 4 digits + 1 letter)
        pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
        has_pan_number = bool(re.search(pan_pattern, text))
        
        # Check for indicators
        has_indicators = any(indicator in text_lower for indicator in pan_indicators)
        
        # Enhanced detection with multiple criteria
        indicator_count = sum(1 for indicator in pan_indicators if indicator in text_lower)
        
        return has_pan_number or indicator_count >= 2
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess PAN card image for optimal OCR"""
        processed_images = []
        
        # Original image
        processed_images.append(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply different preprocessing techniques
        # 1. CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        processed_images.append(cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR))
        
        # 2. Gaussian blur and threshold for text clarity
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 3. Adaptive threshold for varying lighting
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Morphological operations to clean up text
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        # 5. Sharpen the image for better text recognition
        kernel_sharpen = np.array([[-1, -1, -1],
                                   [-1, 9, -1],
                                   [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
        processed_images.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from PAN card OCR text"""
        info = {
            'document_number': None,
            'full_name': None,
            'father_name': None,
            'date_of_birth': None,
            'nationality': 'Indian',
            'document_type': 'PAN Card',
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields using helper methods
        info['document_number'] = self._extract_pan_number(combined_text)
        info['full_name'] = self._extract_name(combined_text)
        info['father_name'] = self._extract_father_name(combined_text)
        info['date_of_birth'] = self._extract_dob(combined_text)
        
        return info
    
    def _extract_pan_number(self, text: str) -> Optional[str]:
        """Extract PAN number"""
        # PAN format: 5 letters + 4 digits + 1 letter
        pan_pattern = r'\b([A-Z]{5}\d{4}[A-Z])\b'
        match = re.search(pan_pattern, text)
        if match:
            return match.group(1)
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name"""
        patterns = [
            r'(?:Name[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|Father|DOB|Date)',
            r'^([A-Z][A-Za-z\s]{5,40}?)(?:\n|Father|Son|Daughter)',
            r'([A-Z][A-Za-z\s]{8,35}?)(?:\s+Father|\s+Son|\s+Daughter)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if (len(name) > 3 and 
                    not re.match(r'^\d+$', name) and
                    'permanent' not in name.lower() and
                    'account' not in name.lower() and
                    'number' not in name.lower() and
                    'income' not in name.lower()):
                    return name
        return None
    
    def _extract_father_name(self, text: str) -> Optional[str]:
        """Extract father's name"""
        patterns = [
            r'(?:Father\'s Name[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|Date|DOB)',
            r'(?:Father[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|Date|DOB)',
            r'(?:S/o[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|Date|DOB)',
            r'(?:Son of[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|Date|DOB)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                father_name = match.group(1).strip()
                if len(father_name) > 3:
                    return father_name
        return None
    
    def _extract_dob(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:Date of Birth[:\s]+|DOB[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Birth[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip()
                return self._normalize_date(date_str)
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to DD/MM/YYYY format"""
        if not date_str:
            return date_str
        
        # Try different date patterns and normalize to DD/MM/YYYY
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'   # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                part1, part2, part3 = match.groups()
                
                # Handle YYYY/MM/DD format
                if len(part1) == 4:  # Year first
                    year, month, day = part1, part2, part3
                else:
                    # Assume DD/MM/YYYY format for Indian documents
                    day, month, year = part1, part2, part3
                
                # Ensure proper formatting
                day = day.zfill(2)
                month = month.zfill(2)
                
                # Validate date components
                try:
                    day_int = int(day)
                    month_int = int(month)
                    year_int = int(year)
                    
                    if 1 <= day_int <= 31 and 1 <= month_int <= 12 and 1900 <= year_int <= 2100:
                        return f"{day}/{month}/{year}"
                except ValueError:
                    continue
        
        # Return original if no pattern matches
        return date_str
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "PAN Card"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "IN"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for PAN cards"""
        return [
            '--psm 6 --oem 3 -l eng',
            '--psm 4 --oem 3 -l eng',
            '--psm 3 --oem 3 -l eng',
            '--psm 8 --oem 3 -l eng',
            '--psm 7 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for PAN card"""
        confidence = 0.0
        
        # PAN number is crucial
        if info.get('document_number'):
            pan_pattern = r'^[A-Z]{5}\d{4}[A-Z]$'
            if re.match(pan_pattern, info['document_number']):
                confidence += 0.5
        
        # Name
        if info.get('full_name') and len(info['full_name']) > 3:
            confidence += 0.2
        
        # Father's name
        if info.get('father_name') and len(info['father_name']) > 3:
            confidence += 0.15
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.15
        
        return min(confidence, 1.0)
