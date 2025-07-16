"""
Australian Passport processor
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class AustralianPassportProcessor(DocumentProcessor):
    """Processor for Australian Passports"""
    
    def __init__(self):
        super().__init__('Australia', 'australian_passport')
        self.supported_languages = ['eng']
        self.confidence_threshold = 0.75
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is an Australian Passport"""
        text_lower = text.lower()
        
        # Australian passport specific indicators
        australian_indicators = [
            'australia',
            'australian passport',
            'commonwealth of australia',
            'australian government',
            'department of foreign affairs',
            'passport office',
            'australian citizen',
            'nationality australian',
            'aus',
            'canberra',
            'passport australia'
        ]
        
        # Check for passport number pattern (8 or 9 characters)
        passport_pattern = r'\b[A-Z]\d{7,8}\b'
        has_passport_number = bool(re.search(passport_pattern, text))
        
        # Check for MRZ pattern specific to Australia
        mrz_pattern = r'P<AUS'
        has_mrz = bool(re.search(mrz_pattern, text))
        
        # Check for indicators
        has_indicators = any(indicator in text_lower for indicator in australian_indicators)
        
        return has_indicators or has_passport_number or has_mrz
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess Australian passport image for optimal OCR"""
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
        
        # 2. Gaussian blur and threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 3. Adaptive threshold
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from Australian passport OCR text"""
        info = {
            'passport_number': None,
            'surname': None,
            'given_names': None,
            'nationality': None,
            'date_of_birth': None,
            'place_of_birth': None,
            'sex': None,
            'date_of_issue': None,
            'date_of_expiry': None,
            'issuing_authority': None,
            'country_code': None,
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields
        info['passport_number'] = self._extract_passport_number(combined_text)
        info['surname'] = self._extract_surname(combined_text)
        info['given_names'] = self._extract_given_names(combined_text)
        info['nationality'] = self._extract_nationality(combined_text)
        info['date_of_birth'] = self._extract_date_of_birth(combined_text)
        info['place_of_birth'] = self._extract_place_of_birth(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['date_of_issue'] = self._extract_date_of_issue(combined_text)
        info['date_of_expiry'] = self._extract_date_of_expiry(combined_text)
        info['issuing_authority'] = self._extract_issuing_authority(combined_text)
        info['country_code'] = self._extract_country_code(combined_text)
        
        return info
    
    def _extract_passport_number(self, text: str) -> Optional[str]:
        """Extract Australian passport number"""
        patterns = [
            r'(?:Passport\s*(?:No|Number)[:\s]+)([A-Z]\d{7,8})',
            r'\b([A-Z]\d{7,8})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_surname(self, text: str) -> Optional[str]:
        """Extract surname"""
        patterns = [
            r'(?:Surname[:\s]+)([A-Za-z\s]+?)(?:\n|Given|First)',
            r'(?:Family\s*Name[:\s]+)([A-Za-z\s]+?)(?:\n|Given|First)',
            r'Surname[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                surname = match.group(1).strip()
                if len(surname) > 1:
                    return surname.upper()
        return None
    
    def _extract_given_names(self, text: str) -> Optional[str]:
        """Extract given names"""
        patterns = [
            r'(?:Given\s*Names?[:\s]+)([A-Za-z\s]+?)(?:\n|Nationality|Date)',
            r'(?:First\s*Name[:\s]+)([A-Za-z\s]+?)(?:\n|Date)',
            r'Given\s*Names?[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                names = match.group(1).strip()
                if len(names) > 1:
                    return names.upper()
        return None
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality"""
        patterns = [
            r'(?:Nationality[:\s]+)(Australian|AUS|Australia)',
            r'\b(Australian)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return 'AUS'
        return None
    
    def _extract_date_of_birth(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:Date of Birth[:\s]+|DOB[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Birth Date[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_place_of_birth(self, text: str) -> Optional[str]:
        """Extract place of birth"""
        patterns = [
            r'(?:Place of Birth[:\s]+)([A-Za-z\s,]+?)(?:\n|Date|Sex)',
            r'Place of Birth[:\s]+([A-Za-z\s,]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                if len(place) > 2:
                    return place
        return None
    
    def _extract_sex(self, text: str) -> Optional[str]:
        """Extract sex/gender"""
        patterns = [
            r'(?:Sex[:\s]+)(M|F|Male|Female)',
            r'\b(Male|Female|M|F)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sex = match.group(1).upper()
                if sex in ['M', 'MALE']:
                    return 'M'
                elif sex in ['F', 'FEMALE']:
                    return 'F'
        return None
    
    def _extract_date_of_issue(self, text: str) -> Optional[str]:
        """Extract date of issue"""
        patterns = [
            r'(?:Date of Issue[:\s]+|Issued[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Issue Date[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_date_of_expiry(self, text: str) -> Optional[str]:
        """Extract date of expiry"""
        patterns = [
            r'(?:Date of Expiry[:\s]+|Expires[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Expiry Date[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_issuing_authority(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        patterns = [
            r'(Australian Government)',
            r'(Department of Foreign Affairs)',
            r'(Passport Office)',
            r'(Commonwealth of Australia)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_country_code(self, text: str) -> Optional[str]:
        """Extract country code"""
        if any(indicator in text.lower() for indicator in ['australia', 'australian', 'aus']):
            return 'AUS'
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to DD/MM/YYYY format"""
        if not date_str:
            return date_str
            
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # Australian date format is typically DD/MM/YYYY
        pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        match = re.search(pattern, date_str)
        
        if match:
            day, month, year = match.groups()
            day = day.zfill(2)
            month = month.zfill(2)
            return f"{day}/{month}/{year}"
        
        return date_str
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "Australian Passport"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "AUS"
