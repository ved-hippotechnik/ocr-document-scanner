"""
Canadian Passport processor
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class CanadianPassportProcessor(DocumentProcessor):
    """Processor for Canadian Passports"""
    
    def __init__(self):
        super().__init__('Canada', 'canadian_passport')
        self.supported_languages = ['eng', 'fra']
        self.confidence_threshold = 0.75
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a Canadian Passport"""
        text_lower = text.lower()
        
        # Canadian passport specific indicators (high confidence)
        canadian_specific_indicators = [
            'canadian passport',
            'passeport canadien',
            'passport canada',
            'gouvernement du canada',
            'government of canada',
            'citizenship and immigration',
            'citoyenneté et immigration',
            'passport office',
            'bureau des passeports',
            'nationality canadian',
            'nationalité canadienne'
        ]
        
        # General indicators that need additional context
        general_indicators = [
            'canada',
            'can',
            'ottawa'
        ]
        
        # Check for passport number pattern
        passport_pattern = r'\b[A-Z]{2}\d{6}\b'
        has_passport_number = bool(re.search(passport_pattern, text))
        
        # Check for MRZ pattern specific to Canada
        mrz_pattern = r'P<CAN'
        has_mrz = bool(re.search(mrz_pattern, text))
        
        # Check for specific indicators
        has_specific_indicators = any(indicator in text_lower for indicator in canadian_specific_indicators)
        
        # Check for general indicators with passport context
        has_general_with_passport = any(indicator in text_lower for indicator in general_indicators) and 'passport' in text_lower
        
        return has_specific_indicators or has_passport_number or has_mrz or has_general_with_passport
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess Canadian passport image for optimal OCR"""
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
        """Extract structured information from Canadian passport OCR text"""
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
        """Extract Canadian passport number"""
        patterns = [
            r'(?:Passport\s*(?:No|Number)[:\s]+)([A-Z]{2}\d{6})',
            r'(?:Passeport\s*(?:No|Numéro)[:\s]+)([A-Z]{2}\d{6})',
            r'\b([A-Z]{2}\d{6})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_surname(self, text: str) -> Optional[str]:
        """Extract surname (English and French)"""
        patterns = [
            r'(?:Surname[:\s]+|Nom de famille[:\s]+)([A-Za-z\s]+?)(?:\n|Given|Prénoms)',
            r'Surname[:\s]+([A-Za-z\s]+?)(?:\n|$)',
            r'Nom de famille[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                surname = match.group(1).strip()
                if len(surname) > 1:
                    return surname.upper()
        return None
    
    def _extract_given_names(self, text: str) -> Optional[str]:
        """Extract given names (English and French)"""
        patterns = [
            r'(?:Given\s*Names?[:\s]+|Prénoms[:\s]+)([A-Za-z\s]+?)(?:\n|Nationality|Date)',
            r'Given\s*Names?[:\s]+([A-Za-z\s]+?)(?:\n|$)',
            r'Prénoms[:\s]+([A-Za-z\s]+?)(?:\n|$)'
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
            r'(?:Nationality[:\s]+|Nationalité[:\s]+)(Canadian|CAN|Canada)',
            r'\b(Canadian)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return 'CAN'
        return None
    
    def _extract_date_of_birth(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:Date of Birth[:\s]+|Date de naissance[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:DOB[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_place_of_birth(self, text: str) -> Optional[str]:
        """Extract place of birth"""
        patterns = [
            r'(?:Place of Birth[:\s]+|Lieu de naissance[:\s]+)([A-Za-z\s,]+?)(?:\n|Date|Sex)',
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
        """Extract sex/gender (English and French)"""
        patterns = [
            r'(?:Sex[:\s]+|Sexe[:\s]+)(M|F|Male|Female|Masculin|Féminin)',
            r'\b(Male|Female|M|F|Masculin|Féminin)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sex = match.group(1).upper()
                if sex in ['M', 'MALE', 'MASCULIN']:
                    return 'M'
                elif sex in ['F', 'FEMALE', 'FÉMININ']:
                    return 'F'
        return None
    
    def _extract_date_of_issue(self, text: str) -> Optional[str]:
        """Extract date of issue"""
        patterns = [
            r'(?:Date of Issue[:\s]+|Date de délivrance[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Issued[:\s]+|Délivré[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_date_of_expiry(self, text: str) -> Optional[str]:
        """Extract date of expiry"""
        patterns = [
            r'(?:Date of Expiry[:\s]+|Date d\'expiration[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Expires[:\s]+|Expire[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_issuing_authority(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        patterns = [
            r'(Government of Canada|Gouvernement du Canada)',
            r'(Passport Office|Bureau des passeports)',
            r'(Citizenship and Immigration|Citoyenneté et Immigration)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_country_code(self, text: str) -> Optional[str]:
        """Extract country code"""
        if any(indicator in text.lower() for indicator in ['canada', 'canadian', 'can']):
            return 'CAN'
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to DD/MM/YYYY format"""
        if not date_str:
            return date_str
            
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # Canadian date format is typically DD/MM/YYYY
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
        return "Canadian Passport"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "CAN"
