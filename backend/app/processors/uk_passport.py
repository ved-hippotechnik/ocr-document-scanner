"""
UK Passport processor
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class UKPassportProcessor(DocumentProcessor):
    """Processor for United Kingdom Passports"""
    
    def __init__(self):
        super().__init__('United Kingdom', 'uk_passport')
        self.supported_languages = ['eng']
        self.confidence_threshold = 0.75
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a UK Passport"""
        text_lower = text.lower()
        
        # UK passport specific indicators (high confidence)
        uk_specific_indicators = [
            'united kingdom',
            'great britain',
            'british passport',
            'british citizen',
            'hm passport office',
            'passport office',
            'nationality british',
            'british national',
            'gbr',
            'british isles',
            'england',
            'scotland',
            'wales',
            'northern ireland'
        ]
        
        # Less specific indicators that need additional context
        general_indicators = [
            'european union',
            'passport no',
            'place of birth',
            'date of birth',
            'date of issue',
            'date of expiry'
        ]
        
        # Check for passport number pattern (9 digits)
        passport_pattern = r'\b\d{9}\b'
        has_passport_number = bool(re.search(passport_pattern, text))
        
        # Check for UK passport document number pattern
        doc_pattern = r'\b[A-Z]\d{8}\b'
        has_doc_number = bool(re.search(doc_pattern, text))
        
        # Check for MRZ pattern specific to UK
        mrz_pattern = r'P<GBR'
        has_mrz = bool(re.search(mrz_pattern, text))
        
        # Check for specific indicators
        has_specific_indicators = any(indicator in text_lower for indicator in uk_specific_indicators)
        
        # Check for general indicators with UK context (need multiple)
        general_matches = sum(1 for indicator in general_indicators if indicator in text_lower)
        has_multiple_general = general_matches >= 4 and ('british' in text_lower or 'kingdom' in text_lower)
        
        return has_specific_indicators or has_passport_number or has_doc_number or has_mrz or has_multiple_general
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess UK passport image for optimal OCR"""
        processed_images = []
        
        # Original image
        processed_images.append(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply different preprocessing techniques
        # 1. CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
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
        
        # 4. Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from UK passport OCR text"""
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
            'document_type': None,
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
        info['document_type'] = self._extract_document_type(combined_text)
        info['country_code'] = self._extract_country_code(combined_text)
        
        return info
    
    def _extract_passport_number(self, text: str) -> Optional[str]:
        """Extract UK passport number"""
        patterns = [
            r'(?:Passport\s*(?:No|Number)[:\s]+)(\d{9})',
            r'(?:Document\s*(?:No|Number)[:\s]+)([A-Z]\d{8})',
            r'\b(\d{9})\b',
            r'\b([A-Z]\d{8})\b'
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
            r'(?:Nationality[:\s]+)(British|GBR|United Kingdom)',
            r'(?:Citizen of[:\s]+)(United Kingdom|Great Britain)',
            r'\b(British)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return 'GBR'
        return None
    
    def _extract_date_of_birth(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:Date of Birth[:\s]+|DOB[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Birth Date[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Born[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
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
            r'(?:Born in[:\s]+)([A-Za-z\s,]+?)(?:\n|Date)',
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
            r'(?:Expiry Date[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Valid until[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_issuing_authority(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        patterns = [
            r'(?:Issuing Authority[:\s]+)([A-Za-z\s]+?)(?:\n|Date)',
            r'(HM Passport Office)',
            r'(Passport Office)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_document_type(self, text: str) -> Optional[str]:
        """Extract document type"""
        if 'passport' in text.lower():
            return 'P'
        return None
    
    def _extract_country_code(self, text: str) -> Optional[str]:
        """Extract country code"""
        if any(indicator in text.lower() for indicator in ['united kingdom', 'great britain', 'british', 'gbr']):
            return 'GBR'
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to DD/MM/YYYY format (UK standard)"""
        if not date_str:
            return date_str
            
        # Remove extra spaces and clean up
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # Try different date patterns and normalize to DD/MM/YYYY
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{1,2})[.\s](\d{1,2})[.\s](\d{4})',  # DD.MM.YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'   # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                part1, part2, part3 = match.groups()
                
                # Handle YYYY/MM/DD format
                if len(part1) == 4:  # Year first
                    year, month, day = part1, part2, part3
                    # Convert to DD/MM/YYYY
                    day = day.zfill(2)
                    month = month.zfill(2)
                    return f"{day}/{month}/{year}"
                else:
                    # Assume DD/MM/YYYY format for UK documents
                    day, month, year = part1, part2, part3
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
        return "UK Passport"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "GBR"
