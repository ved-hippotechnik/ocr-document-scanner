"""
US Drivers License processor
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class USDriversLicenseProcessor(DocumentProcessor):
    """Processor for US Driver's Licenses"""
    
    def __init__(self):
        super().__init__('United States', 'drivers_license')  
        self.supported_languages = ['eng']
        self.confidence_threshold = 0.65
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a US driver's license"""
        text_lower = text.lower()
        
        # Look for US driver's license specific indicators
        us_dl_specific_indicators = [
            'driver license',
            'drivers license',
            'driver\'s license',
            'department of motor vehicles',
            'dmv',
            'dl no',
            'lic no',
            'license no',
            'license number',
            'restrictions',
            'endorsements'
        ]
        
        # General indicators that need context
        general_indicators = [
            'expires',
            'issued',
            'height',
            'weight',
            'eyes',
            'hair',
            'class'
        ]
        
        # Check for US DL number patterns (only if license context is present)
        us_dl_patterns = [
            r'\b[A-Z]{1,2}[\d]{6,8}\b',  # Many states
            r'\b\d{8,9}\b',  # Numeric format
            r'\b[A-Z]\d{8}\b',  # Letter + 8 digits
            r'\b[A-Z]{2}\d{6}\b'  # 2 letters + 6 digits
        ]

        has_dl_pattern = False
        if 'license' in text_lower or 'driver' in text_lower or 'dmv' in text_lower:
            has_dl_pattern = any(bool(re.search(pattern, text)) for pattern in us_dl_patterns)
        
        # Check for specific indicators
        has_specific_indicators = any(indicator in text_lower for indicator in us_dl_specific_indicators)
        
        # Check for state names with driver license context (use word boundaries)
        us_states = [
            r'\balabama\b', r'\balaska\b', r'\barizona\b', r'\barkansas\b', r'\bcalifornia\b', r'\bcolorado\b',
            r'\bconnecticut\b', r'\bdelaware\b', r'\bflorida\b', r'\bgeorgia\b', r'\bhawaii\b', r'\bidaho\b',
            r'\billinois\b', r'\bindiana\b', r'\biowa\b', r'\bkansas\b', r'\bkentucky\b', r'\blouisiana\b',
            r'\bmaine\b', r'\bmaryland\b', r'\bmassachusetts\b', r'\bmichigan\b', r'\bminnesota\b',
            r'\bmississippi\b', r'\bmissouri\b', r'\bmontana\b', r'\bnebraska\b', r'\bnevada\b',
            r'\bnew hampshire\b', r'\bnew jersey\b', r'\bnew mexico\b', r'\bnew york\b',
            r'\bnorth carolina\b', r'\bnorth dakota\b', r'\bohio\b', r'\boklahoma\b', r'\boregon\b',
            r'\bpennsylvania\b', r'\brhode island\b', r'\bsouth carolina\b', r'\bsouth dakota\b',
            r'\btennessee\b', r'\btexas\b', r'\butah\b', r'\bvermont\b', r'\bvirginia\b', r'\bwashington\b',
            r'\bwest virginia\b', r'\bwisconsin\b', r'\bwyoming\b'
        ]
        
        has_state_with_license = any(bool(re.search(state, text_lower)) for state in us_states) and ('license' in text_lower or 'driver' in text_lower)
        
        # Count general indicators
        general_matches = sum(1 for indicator in general_indicators if indicator in text_lower)
        has_multiple_general = general_matches >= 3
        
        return has_specific_indicators or has_dl_pattern or has_state_with_license or has_multiple_general
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess US driver's license image for optimal OCR"""
        processed_images = []
        
        # Original image
        processed_images.append(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply different preprocessing techniques
        # 1. CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        processed_images.append(cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR))
        
        # 2. Gaussian blur and adaptive threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        adaptive_thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 3. OTSU threshold
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(otsu_thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Morphological operations
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(otsu_thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        # 5. Sharpen for better text recognition
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        processed_images.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from US driver's license OCR text"""
        info = {
            'document_number': None,
            'full_name': None,
            'first_name': None,
            'last_name': None,
            'date_of_birth': None,
            'address': None,
            'city': None,
            'state': None,
            'zip_code': None,
            'issue_date': None,
            'expiration_date': None,
            'class': None,
            'restrictions': None,
            'endorsements': None,
            'height': None,
            'weight': None,
            'sex': None,
            'eyes': None,
            'hair': None,
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields
        info['document_number'] = self._extract_dl_number(combined_text)
        info['full_name'] = self._extract_full_name(combined_text)
        info['first_name'] = self._extract_first_name(combined_text)
        info['last_name'] = self._extract_last_name(combined_text)
        info['date_of_birth'] = self._extract_dob(combined_text)
        info['address'] = self._extract_address(combined_text)
        info['city'] = self._extract_city(combined_text)
        info['state'] = self._extract_state(combined_text)
        info['zip_code'] = self._extract_zip_code(combined_text)
        info['issue_date'] = self._extract_issue_date(combined_text)
        info['expiration_date'] = self._extract_expiration_date(combined_text)
        info['class'] = self._extract_class(combined_text)
        info['restrictions'] = self._extract_restrictions(combined_text)
        info['endorsements'] = self._extract_endorsements(combined_text)
        info['height'] = self._extract_height(combined_text)
        info['weight'] = self._extract_weight(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['eyes'] = self._extract_eyes(combined_text)
        info['hair'] = self._extract_hair(combined_text)
        
        return info
    
    def _extract_dl_number(self, text: str) -> Optional[str]:
        """Extract driver's license number"""
        patterns = [
            r'(?:DL\s*NO[:\s]+|LIC\s*NO[:\s]+|LICENSE\s*NO[:\s]+)([A-Z0-9]{6,12})',
            r'(?:DL[:\s]+|LIC[:\s]+)([A-Z0-9]{6,12})',
            r'\b([A-Z]{1,2}[\d]{6,8})\b',
            r'\b(\d{8,9})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_full_name(self, text: str) -> Optional[str]:
        """Extract full name"""
        patterns = [
            r'([A-Z][A-Za-z]+,\s*[A-Z][A-Za-z]+)',  # Last, First format
            r'([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)',  # First Last format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3:
                    return name
        return None
    
    def _extract_first_name(self, text: str) -> Optional[str]:
        """Extract first name"""
        patterns = [
            r'(?:FN[:\s]+|FIRST[:\s]+)([A-Za-z]+)',
            r',\s*([A-Z][A-Za-z]+)'  # After comma in "Last, First" format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_last_name(self, text: str) -> Optional[str]:
        """Extract last name"""
        patterns = [
            r'(?:LN[:\s]+|LAST[:\s]+)([A-Za-z]+)',
            r'([A-Z][A-Za-z]+),'  # Before comma in "Last, First" format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_dob(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:DOB[:\s]+|DATE OF BIRTH[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:DOB[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{2})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address"""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'address' in line.lower() or 'addr' in line.lower():
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return None
    
    def _extract_city(self, text: str) -> Optional[str]:
        """Extract city"""
        patterns = [
            r'(?:CITY[:\s]+)([A-Za-z\s]+)',
            r'([A-Za-z\s]+),\s*[A-Z]{2}\s*\d{5}'  # City, ST ZIP format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_state(self, text: str) -> Optional[str]:
        """Extract state"""
        patterns = [
            r'(?:STATE[:\s]+)([A-Z]{2})',
            r',\s*([A-Z]{2})\s*\d{5}'  # In City, ST ZIP format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_zip_code(self, text: str) -> Optional[str]:
        """Extract ZIP code"""
        pattern = r'\b(\d{5}(?:-\d{4})?)\b'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return None
    
    def _extract_issue_date(self, text: str) -> Optional[str]:
        """Extract issue date"""
        patterns = [
            r'(?:ISSUED[:\s]+|ISS[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:ISSUED[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_expiration_date(self, text: str) -> Optional[str]:
        """Extract expiration date"""
        patterns = [
            r'(?:EXPIRES[:\s]+|EXP[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:EXPIRES[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_class(self, text: str) -> Optional[str]:
        """Extract license class"""
        patterns = [
            r'(?:CLASS[:\s]+)([A-Z0-9]+)',
            r'(?:CL[:\s]+)([A-Z0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_restrictions(self, text: str) -> Optional[str]:
        """Extract restrictions"""
        patterns = [
            r'(?:RESTRICTIONS[:\s]+)([A-Z0-9\s,]+)',
            r'(?:RESTR[:\s]+)([A-Z0-9\s,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_endorsements(self, text: str) -> Optional[str]:
        """Extract endorsements"""
        patterns = [
            r'(?:ENDORSEMENTS[:\s]+)([A-Z0-9\s,]+)',
            r'(?:ENDORSE[:\s]+)([A-Z0-9\s,]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_height(self, text: str) -> Optional[str]:
        """Extract height"""
        patterns = [
            r'(?:HEIGHT[:\s]+|HT[:\s]+)(\d+\'-\d+"|[5-7]\'-[0-9]"|[5-7]\d+")',
            r'(?:HEIGHT[:\s]+)(\d{3})'  # Height in cm
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_weight(self, text: str) -> Optional[str]:
        """Extract weight"""
        patterns = [
            r'(?:WEIGHT[:\s]+|WT[:\s]+)(\d{2,3})',
            r'(?:WEIGHT[:\s]+)(\d{2,3}\s*LBS?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_sex(self, text: str) -> Optional[str]:
        """Extract sex"""
        patterns = [
            r'(?:SEX[:\s]+)([MF])',
            r'\b(MALE|FEMALE|M|F)\b'
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
    
    def _extract_eyes(self, text: str) -> Optional[str]:
        """Extract eye color"""
        patterns = [
            r'(?:EYES[:\s]+)([A-Z]{3})',
            r'(?:EYE[:\s]+)([A-Z]{3})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _extract_hair(self, text: str) -> Optional[str]:
        """Extract hair color"""
        patterns = [
            r'(?:HAIR[:\s]+)([A-Z]{3})',
            r'(?:HAIR[:\s]+)([A-Z]{3})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "US Driver's License"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "US"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for US driver's licenses"""
        return [
            '--psm 6 --oem 3 -l eng',
            '--psm 4 --oem 3 -l eng',
            '--psm 3 --oem 3 -l eng',
            '--psm 11 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for US driver's license"""
        confidence = 0.0
        
        # DL number is crucial
        if info.get('document_number'):
            confidence += 0.3
        
        # Name fields
        if info.get('full_name') or (info.get('first_name') and info.get('last_name')):
            confidence += 0.25
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.2
        
        # State
        if info.get('state'):
            confidence += 0.15
        
        # Expiration date
        if info.get('expiration_date'):
            confidence += 0.1
        
        return min(confidence, 1.0)
