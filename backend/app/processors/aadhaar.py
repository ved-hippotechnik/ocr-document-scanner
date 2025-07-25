"""
Aadhaar Card processor for India
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class AadhaarProcessor(DocumentProcessor):
    """Processor for Indian Aadhaar Cards"""
    
    def __init__(self):
        super().__init__('India', 'aadhaar')
        self.supported_languages = ['eng', 'hin', 'tel', 'tam', 'ben', 'guj', 'kan', 'mal', 'ori', 'pun', 'mar']
        self.confidence_threshold = 0.6
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is an Aadhaar card"""
        text_lower = text.lower()
        
        # Look for Aadhaar-specific indicators
        aadhaar_indicators = [
            'aadhaar',
            'आधार',
            'unique identification authority',
            'uidai',
            'government of india',
            'भारत सरकार'
        ]
        
        # Check for Aadhaar number pattern (12 digits, often grouped)
        aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
        has_aadhaar_number = bool(re.search(aadhaar_pattern, text))
        
        # Check for indicators
        has_indicators = any(indicator in text_lower for indicator in aadhaar_indicators)
        
        return has_indicators or has_aadhaar_number
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess Aadhaar card image for optimal OCR"""
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
        
        # 2. Bilateral filtering for denoising while preserving edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        processed_images.append(cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR))
        
        # 3. Gaussian blur and threshold
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Adaptive threshold for varying lighting conditions
        adaptive_thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 5. Morphological operations to clean up text (using safe constant)
        kernel = np.ones((2, 2), np.uint8)
        # Use cv2.MORPH_CLOSE instead of cv2.MORPH_OPEN for better text cleanup
        morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        # 6. Sharpen the image for better OCR
        kernel_sharpen = np.array([[-1, -1, -1],
                                   [-1, 9, -1],
                                   [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
        processed_images.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from Aadhaar card OCR text"""
        info = {
            'document_number': None,
            'full_name': None,
            'date_of_birth': None,
            'gender': None,
            'address': None,
            'father_name': None,
            'mobile': None,
            'email': None,
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields using helper methods
        info['document_number'] = self._extract_aadhaar_number(combined_text)
        info['full_name'] = self._extract_name(combined_text)
        info['date_of_birth'] = self._extract_dob(combined_text)
        info['gender'] = self._extract_gender(combined_text)
        info['father_name'] = self._extract_father_name(combined_text)
        info['mobile'] = self._extract_mobile(combined_text)
        info['email'] = self._extract_email(combined_text)
        info['address'] = self._extract_address(combined_text)
        
        return info
    
    def _extract_aadhaar_number(self, text: str) -> Optional[str]:
        """Extract Aadhaar number"""
        aadhaar_pattern = r'\b(\d{4}\s?\d{4}\s?\d{4})\b'
        match = re.search(aadhaar_pattern, text)
        if match:
            return re.sub(r'\s+', ' ', match.group(1)).strip()
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name with enhanced patterns"""
        patterns = [
            # English patterns
            r'(?:Name[:\s]+|नाम[:\s]+)([A-Za-z\s]+?)(?:\n|Date|DOB|जन्म|Father|S/o)',
            r'(?:नाम\s*/\s*Name[:\s]+)([A-Za-z\s]+?)(?:\n|Date|DOB|जन्म)',
            r'^([A-Z][A-Za-z\s]+?)(?:\n|Date|DOB|Father|S/o|जन्म)',
            r'([A-Z][A-Za-z\s]{5,30}?)(?:\s+(?:Male|Female|पुरुष|महिला))',
            # Handle names before Aadhaar number
            r'([A-Z][A-Za-z\s]{3,25}?)\s*\n?\s*(?:\d{4}\s?\d{4}\s?\d{4})',
            # Names near government headers
            r'(?:Government of India|भारत सरकार).*?([A-Z][A-Za-z\s]{5,25}?)(?:\n|Date|DOB)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
            if match:
                name = match.group(1).strip()
                # Enhanced filtering
                if (len(name) > 2 and 
                    not re.match(r'^\d+$', name) and
                    'government' not in name.lower() and
                    'india' not in name.lower() and
                    'aadhaar' not in name.lower() and
                    'unique' not in name.lower() and
                    'identification' not in name.lower() and
                    'authority' not in name.lower() and
                    'qr code' not in name.lower() and
                    'photo' not in name.lower() and
                    len(name.split()) <= 4):  # Reasonable name length
                    return name
        return None
    
    def _extract_dob(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:DOB[:\s]+|Date of Birth[:\s]+|जन्म तिथि[:\s]+)(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender"""
        patterns = [
            r'(?:Gender[:\s]+|लिंग[:\s]+)?(Male|Female|पुरुष|महिला)',
            r'\b(Male|Female|पुरुष|महिला)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).lower()
                if gender in ['male', 'पुरुष']:
                    return 'Male'
                elif gender in ['female', 'महिला']:
                    return 'Female'
        return None
    
    def _extract_father_name(self, text: str) -> Optional[str]:
        """Extract father's name"""
        patterns = [
            r'(?:Father[:\s]+|पिता[:\s]+|S/o[:\s]+)([A-Za-z\s]+?)(?:\n|Address)',
            r'S/o[:\s]+([A-Za-z\s]+?)(?:\n|$)',
            r'Father[:\s]+([A-Za-z\s]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                father_name = match.group(1).strip()
                if len(father_name) > 2:
                    return father_name
        return None
    
    def _extract_mobile(self, text: str) -> Optional[str]:
        """Extract mobile number"""
        pattern = r'(?:Mobile[:\s]+|Mob[:\s]+)?(\+91[\s-]?)?([6-9]\d{9})'
        match = re.search(pattern, text)
        if match:
            return match.group(2)
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address"""
        address_lines = []
        lines = text.split('\n')
        
        address_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if any(indicator in line.lower() for indicator in ['address', 'पता', 'addr']):
                address_started = True
                addr_match = re.search(r'(?:Address[:\s]+|पता[:\s]+|Addr[:\s]+)(.+)', line, re.IGNORECASE)
                if addr_match:
                    address_lines.append(addr_match.group(1).strip())
                continue
            
            if address_started:
                if any(field in line.lower() for field in ['aadhaar', 'आधार', 'uid', 'issue', 'enrol']):
                    break
                if len(line) > 5 and not re.match(r'^\d{4}\s?\d{4}\s?\d{4}$', line):
                    address_lines.append(line)
        
        if address_lines:
            return ' '.join(address_lines).strip()
        return None
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "Aadhaar Card"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "IN"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for Aadhaar cards"""
        return [
            '--psm 6 --oem 3 -l eng+hin',
            '--psm 4 --oem 3 -l eng+hin',
            '--psm 3 --oem 3 -l eng',
            '--psm 6 --oem 3 -l eng',
            '--psm 8 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for Aadhaar card"""
        confidence = 0.0
        
        # Aadhaar number is crucial
        if info.get('document_number'):
            aadhaar_num = re.sub(r'\s+', '', info['document_number'])
            if len(aadhaar_num) == 12 and aadhaar_num.isdigit():
                confidence += 0.4
        
        # Name
        if info.get('full_name') and len(info['full_name']) > 2:
            confidence += 0.2
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.2
        
        # Gender
        if info.get('gender'):
            confidence += 0.1
        
        # Address
        if info.get('address') and len(info['address']) > 10:
            confidence += 0.1
        
        return min(confidence, 1.0)
