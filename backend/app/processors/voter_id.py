"""
Voter ID Card processor for India
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class VoterIDProcessor(DocumentProcessor):
    """Processor for Indian Voter ID Cards (Election Commission of India)"""
    
    def __init__(self):
        super().__init__('India', 'voter_id')
        self.supported_languages = ['eng', 'hin', 'tel', 'tam', 'ben', 'guj', 'kan', 'mal', 'ori', 'pun', 'mar']
        self.confidence_threshold = 0.65
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a Voter ID card"""
        text_lower = text.lower()
        
        # Look for Voter ID specific indicators
        voter_id_indicators = [
            'election commission',
            'electors photo identity card',
            'epic',
            'chief electoral officer',
            'elector\'s photo identity card',
            'भारत निर्वाचन आयोग',
            'मतदाता पहचान पत्र',
            'voter id',
            'electoral',
            'assembly constituency',
            'part number',
            'serial number'
        ]
        
        # Check for Voter ID number patterns (varies by state but typically 3 letters + 7 digits)
        voter_id_patterns = [
            r'\b[A-Z]{3}\d{7}\b',  # Standard format
            r'\b[A-Z]{2}\d{8}\b',  # Alternative format
            r'\b[A-Z]{4}\d{6}\b'   # Another format
        ]
        
        has_voter_id_number = any(re.search(pattern, text) for pattern in voter_id_patterns)
        
        # Enhanced detection with multiple criteria
        indicator_count = sum(1 for indicator in voter_id_indicators if indicator in text_lower)
        
        return has_voter_id_number or indicator_count >= 2
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess Voter ID card image for optimal OCR"""
        processed_images = []
        
        # Original image
        processed_images.append(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply different preprocessing techniques
        # 1. CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        processed_images.append(cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR))
        
        # 2. Bilateral filtering for noise reduction while preserving edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        processed_images.append(cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR))
        
        # 3. Gaussian blur and threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Adaptive threshold for varying lighting conditions
        adaptive_thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 5. Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from Voter ID card OCR text"""
        info = {
            'document_number': None,
            'full_name': None,
            'father_name': None,
            'husband_name': None,
            'house_number': None,
            'age': None,
            'sex': None,
            'constituency': None,
            'part_number': None,
            'serial_number': None,
            'nationality': 'Indian',
            'document_type': 'Voter ID',
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields using helper methods
        info['document_number'] = self._extract_voter_id_number(combined_text)
        info['full_name'] = self._extract_name(combined_text)
        info['father_name'] = self._extract_father_name(combined_text)
        info['husband_name'] = self._extract_husband_name(combined_text)
        info['house_number'] = self._extract_house_number(combined_text)
        info['age'] = self._extract_age(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['constituency'] = self._extract_constituency(combined_text)
        info['part_number'] = self._extract_part_number(combined_text)
        info['serial_number'] = self._extract_serial_number(combined_text)
        
        return info
    
    def _extract_voter_id_number(self, text: str) -> Optional[str]:
        """Extract Voter ID number"""
        patterns = [
            r'\b([A-Z]{3}\d{7})\b',  # Standard format
            r'\b([A-Z]{2}\d{8})\b',  # Alternative format
            r'\b([A-Z]{4}\d{6})\b'   # Another format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name"""
        patterns = [
            r'(?:Name[:\s]+|नाम[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|Father|Husband|House|Age)',
            r'^([A-Z][A-Za-z\s]{5,40}?)(?:\n|Father|Husband|S/o|W/o|D/o)',
            r'([A-Z][A-Za-z\s]{8,35}?)(?:\s+(?:Father|Husband|S/o|W/o|D/o))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if (len(name) > 3 and 
                    not re.match(r'^\d+$', name) and
                    'election' not in name.lower() and
                    'commission' not in name.lower() and
                    'identity' not in name.lower() and
                    'elector' not in name.lower()):
                    return name
        return None
    
    def _extract_father_name(self, text: str) -> Optional[str]:
        """Extract father's name"""
        patterns = [
            r'(?:Father\'s Name[:\s]+|Father[:\s]+|S/o[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|House|Age|Sex)',
            r'(?:पिता का नाम[:\s]+)([A-Za-z\s]+?)(?:\n|House|Age|Sex)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                father_name = match.group(1).strip()
                if len(father_name) > 3:
                    return father_name
        return None
    
    def _extract_husband_name(self, text: str) -> Optional[str]:
        """Extract husband's name"""
        patterns = [
            r'(?:Husband\'s Name[:\s]+|Husband[:\s]+|W/o[:\s]+)([A-Z][A-Za-z\s]+?)(?:\n|House|Age|Sex)',
            r'(?:पति का नाम[:\s]+)([A-Za-z\s]+?)(?:\n|House|Age|Sex)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                husband_name = match.group(1).strip()
                if len(husband_name) > 3:
                    return husband_name
        return None
    
    def _extract_house_number(self, text: str) -> Optional[str]:
        """Extract house number"""
        patterns = [
            r'(?:House No[:\s]+|House Number[:\s]+)([A-Z0-9/-]+)',
            r'(?:घर संख्या[:\s]+)([A-Z0-9/-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_age(self, text: str) -> Optional[str]:
        """Extract age"""
        patterns = [
            r'(?:Age[:\s]+|उम्र[:\s]+)(\d{1,3})',
            r'\b(\d{1,3})\s*(?:years|yrs|Y)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 18 <= age <= 120:  # Valid voting age range
                    return str(age)
        return None
    
    def _extract_sex(self, text: str) -> Optional[str]:
        """Extract sex/gender"""
        patterns = [
            r'(?:Sex[:\s]+|Gender[:\s]+|लिंग[:\s]+)(M|F|Male|Female|पुरुष|महिला)',
            r'\b(Male|Female|M|F|पुरुष|महिला)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sex = match.group(1).upper()
                if sex in ['M', 'MALE', 'पुरुष']:
                    return 'Male'
                elif sex in ['F', 'FEMALE', 'महिला']:
                    return 'Female'
        return None
    
    def _extract_constituency(self, text: str) -> Optional[str]:
        """Extract assembly constituency"""
        patterns = [
            r'(?:Assembly Constituency[:\s]+|Constituency[:\s]+)([A-Za-z\s]+?)(?:\n|Part|Serial)',
            r'(?:विधानसभा क्षेत्र[:\s]+)([A-Za-z\s]+?)(?:\n|Part|Serial)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                constituency = match.group(1).strip()
                if len(constituency) > 3:
                    return constituency
        return None
    
    def _extract_part_number(self, text: str) -> Optional[str]:
        """Extract part number"""
        patterns = [
            r'(?:Part No[:\s]+|Part Number[:\s]+)(\d+)',
            r'(?:भाग संख्या[:\s]+)(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_serial_number(self, text: str) -> Optional[str]:
        """Extract serial number"""
        patterns = [
            r'(?:Serial No[:\s]+|Serial Number[:\s]+|Sl No[:\s]+)(\d+)',
            r'(?:क्रम संख्या[:\s]+)(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "Voter ID Card"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "IN"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for Voter ID cards"""
        return [
            '--psm 6 --oem 3 -l eng+hin',
            '--psm 4 --oem 3 -l eng+hin',
            '--psm 3 --oem 3 -l eng',
            '--psm 6 --oem 3 -l eng',
            '--psm 8 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for Voter ID card"""
        confidence = 0.0
        
        # Voter ID number is crucial
        if info.get('document_number'):
            voter_id_patterns = [r'^[A-Z]{3}\d{7}$', r'^[A-Z]{2}\d{8}$', r'^[A-Z]{4}\d{6}$']
            if any(re.match(pattern, info['document_number']) for pattern in voter_id_patterns):
                confidence += 0.4
        
        # Name
        if info.get('full_name') and len(info['full_name']) > 3:
            confidence += 0.2
        
        # Father's or husband's name
        if info.get('father_name') or info.get('husband_name'):
            confidence += 0.15
        
        # Age
        if info.get('age'):
            confidence += 0.1
        
        # Sex
        if info.get('sex'):
            confidence += 0.1
        
        # Part or serial number
        if info.get('part_number') or info.get('serial_number'):
            confidence += 0.05
        
        return min(confidence, 1.0)
