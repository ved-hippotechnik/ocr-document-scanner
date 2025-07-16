"""
US Green Card processor
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class USGreenCardProcessor(DocumentProcessor):
    """Processor for US Permanent Resident Cards (Green Cards)"""
    
    def __init__(self):
        super().__init__('United States', 'us_green_card')
        self.supported_languages = ['eng']
        self.confidence_threshold = 0.7
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a US Green Card"""
        text_lower = text.lower()
        
        # Look for Green Card specific indicators (more specific)
        green_card_specific_indicators = [
            'permanent resident card',
            'department of homeland security',
            'u.s. citizenship and immigration services',
            'uscis',
            'alien registration',
            'alien number',
            'green card',
            'lawful permanent resident',
            'card expires',
            'resident since'
        ]
        
        # Less specific indicators that need multiple matches
        general_indicators = [
            'united states of america',
            'category',
            'country of birth'
        ]
        
        # Check for USCIS number pattern (typically 9 digits)
        uscis_pattern = r'\b\d{9}\b'
        has_uscis_number = bool(re.search(uscis_pattern, text))
        
        # Check for A-number (Alien number) pattern
        a_number_pattern = r'A\d{8,9}'
        has_a_number = bool(re.search(a_number_pattern, text))
        
        # Check for green card number pattern (3 letters + 10 digits)
        card_number_pattern = r'\b[A-Z]{3}\d{10}\b'
        has_card_number = bool(re.search(card_number_pattern, text))
        
        # Check for specific indicators
        has_specific_indicators = any(indicator in text_lower for indicator in green_card_specific_indicators)
        
        # Check for general indicators (need at least 2)
        general_matches = sum(1 for indicator in general_indicators if indicator in text_lower)
        has_multiple_general = general_matches >= 2
        
        # Must have either specific indicators, unique patterns, or multiple general indicators
        return has_specific_indicators or has_uscis_number or has_a_number or has_card_number or has_multiple_general
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess Green Card image for optimal OCR"""
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
        
        # 2. Gaussian blur and threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 3. Adaptive threshold for better text detection
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 9, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Edge enhancement
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        processed_images.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        # 5. Morphological operations for text cleanup
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from Green Card OCR text"""
        info = {
            'card_number': None,
            'alien_number': None,
            'uscis_number': None,
            'given_name': None,
            'family_name': None,
            'date_of_birth': None,
            'country_of_birth': None,
            'sex': None,
            'date_of_expiry': None,
            'resident_since': None,
            'category': None,
            'card_expires': None,
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields
        info['card_number'] = self._extract_card_number(combined_text)
        info['alien_number'] = self._extract_alien_number(combined_text)
        info['uscis_number'] = self._extract_uscis_number(combined_text)
        info['given_name'] = self._extract_given_name(combined_text)
        info['family_name'] = self._extract_family_name(combined_text)
        info['date_of_birth'] = self._extract_date_of_birth(combined_text)
        info['country_of_birth'] = self._extract_country_of_birth(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['date_of_expiry'] = self._extract_expiry_date(combined_text)
        info['card_expires'] = self._extract_card_expires(combined_text)
        info['resident_since'] = self._extract_resident_since(combined_text)
        info['category'] = self._extract_category(combined_text)
        
        return info
    
    def _extract_card_number(self, text: str) -> Optional[str]:
        """Extract Green Card number"""
        patterns = [
            r'\b([A-Z]{3}\d{10})\b',  # Standard format: 3 letters + 10 digits
            r'Card\s*(?:No|Number)[:\s]+([A-Z]{3}\d{10})',
            r'(?:Card|Number)[:\s]+([A-Z]{3}\d{10})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_alien_number(self, text: str) -> Optional[str]:
        """Extract Alien Registration Number"""
        patterns = [
            r'(?:Alien\s*(?:Registration\s*)?(?:No|Number)[:\s]+|A\s*#\s*)(A?\d{8,9})',
            r'\b(A\d{8,9})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                if not number.startswith('A'):
                    number = 'A' + number
                return number
        return None
    
    def _extract_uscis_number(self, text: str) -> Optional[str]:
        """Extract USCIS number"""
        patterns = [
            r'(?:USCIS\s*(?:No|Number)[:\s]+)(\d{9})',
            r'\b(\d{9})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_given_name(self, text: str) -> Optional[str]:
        """Extract given name"""
        patterns = [
            r'(?:Given\s*Name[:\s]+|First\s*Name[:\s]+)([A-Za-z\s]+?)(?:\n|Family|Last|Sex)',
            r'Given\s*Name[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 1:
                    return name
        return None
    
    def _extract_family_name(self, text: str) -> Optional[str]:
        """Extract family name"""
        patterns = [
            r'(?:Family\s*Name[:\s]+|Last\s*Name[:\s]+|Surname[:\s]+)([A-Za-z\s]+?)(?:\n|Given|Date)',
            r'Family\s*Name[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 1:
                    return name
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
    
    def _extract_country_of_birth(self, text: str) -> Optional[str]:
        """Extract country of birth"""
        patterns = [
            r'(?:Country of Birth[:\s]+|Birth Country[:\s]+)([A-Za-z\s]+?)(?:\n|Sex|Date)',
            r'Country of Birth[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                if len(country) > 2:
                    return country
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
    
    def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extract card expiry date"""
        patterns = [
            r'(?:Card Expires[:\s]+|Expires[:\s]+|Expiry[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Valid until[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Expiration Date[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_card_expires(self, text: str) -> Optional[str]:
        """Extract card expires date (alternative method)"""
        return self._extract_expiry_date(text)
    
    def _extract_resident_since(self, text: str) -> Optional[str]:
        """Extract resident since date"""
        patterns = [
            r'(?:Resident Since[:\s]+|Since[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:LPR Since[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1).strip())
        return None
    
    def _extract_category(self, text: str) -> Optional[str]:
        """Extract immigration category"""
        patterns = [
            r'(?:Category[:\s]+)([A-Z0-9]{2,5})',
            r'(?:Class[:\s]+)([A-Z0-9]{2,5})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to MM/DD/YYYY format (US standard)"""
        if not date_str:
            return date_str
            
        # Remove extra spaces and clean up
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # Try different date patterns and normalize to MM/DD/YYYY
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{1,2})[.\s](\d{1,2})[.\s](\d{4})',  # MM.DD.YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'   # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                part1, part2, part3 = match.groups()
                
                # Handle YYYY/MM/DD format
                if len(part1) == 4:  # Year first
                    year, month, day = part1, part2, part3
                    # Convert to MM/DD/YYYY
                    month = month.zfill(2)
                    day = day.zfill(2)
                    return f"{month}/{day}/{year}"
                else:
                    # Assume MM/DD/YYYY format for US documents
                    month, day, year = part1, part2, part3
                    month = month.zfill(2)
                    day = day.zfill(2)
                    
                    # Validate date components
                    try:
                        day_int = int(day)
                        month_int = int(month)
                        year_int = int(year)
                        
                        if 1 <= day_int <= 31 and 1 <= month_int <= 12 and 1900 <= year_int <= 2100:
                            return f"{month}/{day}/{year}"
                    except ValueError:
                        continue
        
        # Return original if no pattern matches
        return date_str
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "US Green Card"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "US"
