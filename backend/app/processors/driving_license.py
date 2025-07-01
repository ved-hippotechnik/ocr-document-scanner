"""
Driving License processor for India
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class DrivingLicenseProcessor(DocumentProcessor):
    """Processor for Indian Driving Licenses"""
    
    def __init__(self):
        super().__init__('India', 'driving_license')
        self.supported_languages = ['eng', 'hin']
        self.confidence_threshold = 0.65
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a driving license"""
        text_lower = text.lower()
        
        # Look for driving license specific indicators
        dl_indicators = [
            'driving licence',
            'driving license',
            'ड्राइविंग लाइसेंस',
            'government of india',
            'भारत सरकार',
            'transport',
            'motor vehicle',
            'dl no',
            'licence no',
            'license no',
            'class of vehicle',
            'validity',
            'issue date',
            'issuing authority',
            'rto'
        ]
        
        # Check for DL number pattern
        dl_pattern = r'\b[A-Z]{2}[\d]{2}[\d]{4}[\d]{7}\b'  # Standard DL format
        has_dl_number = bool(re.search(dl_pattern, text))
        
        # Check for indicators
        has_indicators = any(indicator in text_lower for indicator in dl_indicators)
        
        # Additional patterns for DL number variations
        dl_patterns = [
            r'\b[A-Z]{2}-?\d{2}-?\d{4}-?\d{7}\b',
            r'\bDL\s*NO[:\s]+[A-Z0-9-]{10,20}\b',
            r'\bLICENCE\s*NO[:\s]+[A-Z0-9-]{10,20}\b'
        ]
        
        has_dl_pattern = any(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in dl_patterns)
        
        return has_indicators or has_dl_number or has_dl_pattern
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess driving license image for optimal OCR"""
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
        
        # 2. Gaussian blur and adaptive threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        adaptive_thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 3. OTSU threshold
        _, otsu_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(otsu_thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Morphological operations for text enhancement
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(otsu_thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        # 5. Dilation to thicken text
        kernel = np.ones((1, 2), np.uint8)
        dilated = cv2.dilate(otsu_thresh, kernel, iterations=1)
        processed_images.append(cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from driving license OCR text"""
        info = {
            'document_number': None,
            'full_name': None,
            'father_name': None,
            'date_of_birth': None,
            'address': None,
            'issue_date': None,
            'validity_upto': None,
            'issuing_authority': None,
            'class_of_vehicle': None,
            'blood_group': None,
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields
        info['document_number'] = self._extract_dl_number(combined_text)
        info['full_name'] = self._extract_name(combined_text)
        info['father_name'] = self._extract_father_name(combined_text)
        info['date_of_birth'] = self._extract_dob(combined_text)
        info['address'] = self._extract_address(combined_text)
        info['issue_date'] = self._extract_issue_date(combined_text)
        info['validity_upto'] = self._extract_validity(combined_text)
        info['issuing_authority'] = self._extract_issuing_authority(combined_text)
        info['class_of_vehicle'] = self._extract_vehicle_class(combined_text)
        info['blood_group'] = self._extract_blood_group(combined_text)
        
        return info
    
    def _extract_dl_number(self, text: str) -> Optional[str]:
        """Extract driving license number"""
        patterns = [
            r'(?:DL\s*NO[:\s]+|LICENCE\s*NO[:\s]+|LICENSE\s*NO[:\s]+)([A-Z0-9-]{10,20})',
            r'\b([A-Z]{2}[\d]{2}[\d]{4}[\d]{7})\b',
            r'\b([A-Z]{2}-?\d{2}-?\d{4}-?\d{7})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dl_num = match.group(1).replace('-', '').replace(' ', '')
                return dl_num
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name"""
        patterns = [
            r'(?:Name[:\s]+|नाम[:\s]+)([A-Za-z\s]+?)(?:\n|S/o|Father|DOB|Date)',
            r'^([A-Z][A-Za-z\s]+?)(?:\n|S/o|Father)',
            r'([A-Z][A-Za-z\s]{5,40}?)(?:\s+S/o|\s+Father|\s+DOB)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2 and not re.match(r'^\d+$', name):
                    # Filter out common false positives
                    if not any(word in name.lower() for word in ['government', 'india', 'licence', 'authority']):
                        return name
        return None
    
    def _extract_father_name(self, text: str) -> Optional[str]:
        """Extract father's name"""
        patterns = [
            r'(?:S/o[:\s]+|Father[:\s]+|Son of[:\s]+)([A-Za-z\s]+?)(?:\n|DOB|Date|Address)',
            r'S/o[:\s]+([A-Za-z\s]+?)(?:\n|$)',
            r'Father[:\s]*([A-Za-z\s]+?)(?:\n|DOB|Date)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                father_name = match.group(1).strip()
                if len(father_name) > 2:
                    return father_name
        return None
    
    def _extract_dob(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:DOB[:\s]+|Date of Birth[:\s]+|जन्म तिथि[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:DOB[:\s]+|Date of Birth[:\s]+)(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return self._process_address_lines(lines)
    
    def _process_address_lines(self, lines: List[str]) -> Optional[str]:
        """Process lines to extract address"""
        address_lines = []
        address_started = False
        
        for line in lines:
            if self._is_address_indicator(line):
                address_started = True
                extracted = self._extract_address_from_line(line)
                if extracted:
                    address_lines.append(extracted)
                continue
            
            if address_started:
                if self._should_stop_address_extraction(line):
                    break
                if self._is_valid_address_line(line):
                    address_lines.append(line)
        
        return ' '.join(address_lines).strip() if address_lines else None
    
    def _extract_address_from_line(self, line: str) -> Optional[str]:
        """Extract address from a line with address indicator"""
        addr_match = re.search(r'(?:Address[:\s]+|पता[:\s]+|Addr[:\s]+)(.+)', line, re.IGNORECASE)
        return addr_match.group(1).strip() if addr_match else None
    
    def _is_address_indicator(self, line: str) -> bool:
        """Check if line contains address indicators"""
        return any(indicator in line.lower() for indicator in ['address', 'addr', 'पता'])
    
    def _should_stop_address_extraction(self, line: str) -> bool:
        """Check if we should stop extracting address"""
        stop_words = ['validity', 'issue', 'rto', 'class', 'blood']
        return any(field in line.lower() for field in stop_words)
    
    def _is_valid_address_line(self, line: str) -> bool:
        """Check if line is a valid address line"""
        return len(line) > 5 and not re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}$', line)
    
    def _extract_issue_date(self, text: str) -> Optional[str]:
        """Extract issue date"""
        patterns = [
            r'(?:Issue Date[:\s]+|Issued on[:\s]+|Date of Issue[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Issue[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_validity(self, text: str) -> Optional[str]:
        """Extract validity date"""
        patterns = [
            r'(?:Valid\s*till[:\s]+|Validity[:\s]+|Valid\s*upto[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(?:Valid\s*till[:\s]+)(\d{1,2}-\d{1,2}-\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_issuing_authority(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        patterns = [
            r'(?:Issuing Authority[:\s]+|RTO[:\s]+)([A-Za-z\s,.-]+?)(?:\n|$)',
            r'(RTO[A-Za-z\s,-]*)',
            r'(Transport.*Authority.*[A-Za-z\s,.-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                authority = match.group(1).strip()
                if len(authority) > 3:
                    return authority
        return None
    
    def _extract_vehicle_class(self, text: str) -> Optional[str]:
        """Extract class of vehicle"""
        patterns = [
            r'(?:Class of Vehicle[:\s]+|COV[:\s]+|Class[:\s]+)([A-Za-z0-9\s,/-]+?)(?:\n|Blood|Issue)',
            r'(?:Class[:\s]+)([A-Z0-9,\s/-]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vehicle_class = match.group(1).strip()
                if len(vehicle_class) > 1:
                    return vehicle_class
        return None
    
    def _extract_blood_group(self, text: str) -> Optional[str]:
        """Extract blood group"""
        patterns = [
            r'(?:Blood Group[:\s]+|BG[:\s]+)([ABO][+-]?)',
            r'\b([ABO][+-])\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "Driving License"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "IN"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for driving licenses"""
        return [
            '--psm 6 --oem 3 -l eng+hin',
            '--psm 4 --oem 3 -l eng+hin',
            '--psm 3 --oem 3 -l eng',
            '--psm 6 --oem 3 -l eng',
            '--psm 11 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for driving license"""
        confidence = 0.0
        
        # DL number is crucial
        if info.get('document_number'):
            dl_num = re.sub(r'[-\s]', '', info['document_number'])
            if len(dl_num) >= 10:  # Minimum DL number length
                confidence += 0.35
        
        # Name
        if info.get('full_name') and len(info['full_name']) > 2:
            confidence += 0.25
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.15
        
        # Issue date or validity
        if info.get('issue_date') or info.get('validity_upto'):
            confidence += 0.15
        
        # Class of vehicle
        if info.get('class_of_vehicle'):
            confidence += 0.1
        
        return min(confidence, 1.0)
