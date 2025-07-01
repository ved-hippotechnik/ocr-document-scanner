"""
Passport processor for India
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class PassportProcessor(DocumentProcessor):
    """Processor for Indian Passports"""
    
    def __init__(self):
        super().__init__('India', 'passport')
        self.supported_languages = ['eng']
        self.confidence_threshold = 0.7
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a passport"""
        text_lower = text.lower()
        
        # Look for passport specific indicators
        passport_indicators = [
            'passport',
            'republic of india',
            'भारत गणराज्य',
            'government of india',
            'भारत सरकार',
            'ministry of external affairs',
            'विदेश मंत्रालय',
            'type/प्रकार',
            'country code/देश कोड',
            'passport no',
            'given name',
            'surname',
            'nationality',
            'place of birth',
            'date of issue',
            'date of expiry'
        ]
        
        # Check for passport number pattern
        passport_pattern = r'\b[A-Z]\d{7}\b'  # Standard Indian passport format
        has_passport_number = bool(re.search(passport_pattern, text))
        
        # Check for indicators
        has_indicators = any(indicator in text_lower for indicator in passport_indicators)
        
        # Check for MRZ (Machine Readable Zone) pattern
        mrz_pattern = r'P<IND[A-Z0-9<]+|[A-Z0-9<]{44}'
        has_mrz = bool(re.search(mrz_pattern, text))
        
        return has_indicators or has_passport_number or has_mrz
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess passport image for optimal OCR"""
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
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 3. Adaptive threshold for better text detection
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Edge enhancement
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        processed_images.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        # 5. Morphological operations
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from passport OCR text"""
        info = {
            'document_number': None,
            'document_type': None,
            'country_code': None,
            'surname': None,
            'given_name': None,
            'nationality': None,
            'date_of_birth': None,
            'place_of_birth': None,
            'sex': None,
            'date_of_issue': None,
            'date_of_expiry': None,
            'place_of_issue': None,
            'file_number': None,
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields
        info['document_number'] = self._extract_passport_number(combined_text)
        info['document_type'] = self._extract_document_type(combined_text)
        info['country_code'] = self._extract_country_code(combined_text)
        info['surname'] = self._extract_surname(combined_text)
        info['given_name'] = self._extract_given_name(combined_text)
        info['nationality'] = self._extract_nationality(combined_text)
        info['date_of_birth'] = self._extract_dob(combined_text)
        info['place_of_birth'] = self._extract_place_of_birth(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['date_of_issue'] = self._extract_issue_date(combined_text)
        info['date_of_expiry'] = self._extract_expiry_date(combined_text)
        info['place_of_issue'] = self._extract_place_of_issue(combined_text)
        info['file_number'] = self._extract_file_number(combined_text)
        
        return info
    
    def _extract_passport_number(self, text: str) -> Optional[str]:
        """Extract passport number"""
        patterns = [
            r'(?:Passport\s*No[:\s]+|PASSPORT\s*NO[:\s]+)([A-Z]\d{7})',
            r'\b([A-Z]\d{7})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_document_type(self, text: str) -> Optional[str]:
        """Extract document type"""
        patterns = [
            r'(?:Type[/:\s]+|प्रकार[/:\s]+)([A-Z]+)',
            r'Type[/:\s]+([A-Z])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_country_code(self, text: str) -> Optional[str]:
        """Extract country code"""
        patterns = [
            r'(?:Country\s*Code[/:\s]+|देश\s*कोड[/:\s]+)([A-Z]{3})',
            r'Country\s*Code[/:\s]+([A-Z]{3})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_surname(self, text: str) -> Optional[str]:
        """Extract surname"""
        patterns = [
            r'(?:Surname[/:\s]+|उपनाम[/:\s]+)([A-Za-z\s]+?)(?:\n|Given|Name)',
            r'Surname[/:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                surname = match.group(1).strip()
                if len(surname) > 1:
                    return surname
        return None
    
    def _extract_given_name(self, text: str) -> Optional[str]:
        """Extract given name"""
        patterns = [
            r'(?:Given\s*Name[/:\s]+|नाम[/:\s]+)([A-Za-z\s]+?)(?:\n|Nationality|Sex)',
            r'Given\s*Name[/:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                given_name = match.group(1).strip()
                if len(given_name) > 1:
                    return given_name
        return None
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality"""
        patterns = [
            r'(?:Nationality[/:\s]+|राष्ट्रीयता[/:\s]+)([A-Za-z\s]+?)(?:\n|Date|Sex)',
            r'Nationality[/:\s]+([A-Z]{3})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nationality = match.group(1).strip()
                if len(nationality) > 1:
                    return nationality
        return None
    
    def _extract_dob(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:Date of Birth[/:\s]+|जन्म तिथि[/:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:DOB[/:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_place_of_birth(self, text: str) -> Optional[str]:
        """Extract place of birth"""
        patterns = [
            r'(?:Place of Birth[/:\s]+|जन्म स्थान[/:\s]+)([A-Za-z\s,]+?)(?:\n|Date|Sex)',
            r'Place of Birth[/:\s]+([A-Za-z\s,]+?)(?:\n|$)'
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
            r'(?:Sex[/:\s]+|लिंग[/:\s]+)(M|F|Male|Female)',
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
    
    def _extract_issue_date(self, text: str) -> Optional[str]:
        """Extract date of issue"""
        patterns = [
            r'(?:Date of Issue[/:\s]+|जारी करने की तिथि[/:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Issue Date[/:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extract date of expiry"""
        patterns = [
            r'(?:Date of Expiry[/:\s]+|समाप्ति तिथि[/:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Expiry Date[/:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_place_of_issue(self, text: str) -> Optional[str]:
        """Extract place of issue"""
        patterns = [
            r'(?:Place of Issue[/:\s]+|जारी करने का स्थान[/:\s]+)([A-Za-z\s,]+?)(?:\n|Date|File)',
            r'Place of Issue[/:\s]+([A-Za-z\s,]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                if len(place) > 2:
                    return place
        return None
    
    def _extract_file_number(self, text: str) -> Optional[str]:
        """Extract file number"""
        patterns = [
            r'(?:File\s*No[/:\s]+|फाइल नं[/:\s]+)([A-Z0-9/-]+)',
            r'File\s*No[/:\s]+([A-Z0-9/-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "Passport"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "IN"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for passports"""
        return [
            '--psm 6 --oem 3 -l eng',
            '--psm 4 --oem 3 -l eng',
            '--psm 3 --oem 3 -l eng',
            '--psm 11 --oem 3 -l eng',
            '--psm 8 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for passport"""
        confidence = 0.0
        
        # Passport number is crucial
        if info.get('document_number'):
            passport_pattern = r'^[A-Z]\d{7}$'
            if re.match(passport_pattern, info['document_number']):
                confidence += 0.4
        
        # Given name and surname
        if info.get('given_name') and len(info['given_name']) > 1:
            confidence += 0.2
        
        if info.get('surname') and len(info['surname']) > 1:
            confidence += 0.2
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.1
        
        # Date of expiry
        if info.get('date_of_expiry'):
            confidence += 0.05
        
        # Date of issue
        if info.get('date_of_issue'):
            confidence += 0.05
        
        return min(confidence, 1.0)
