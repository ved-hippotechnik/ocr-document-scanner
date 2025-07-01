"""
Emirates ID document processor
Enhanced processing for UAE Emirates ID cards
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional

from . import DocumentProcessor


class EmiratesIDProcessor(DocumentProcessor):
    """Processor for UAE Emirates ID cards"""
    
    def __init__(self):
        super().__init__("United Arab Emirates", "emirates_id")
        self.supported_languages = ['ara', 'eng']
        self.confidence_threshold = 0.8
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if this is an Emirates ID"""
        text_lower = text.lower()
        
        # Emirates ID specific patterns
        keywords = [
            'emirates id', 'بطاقة الهوية', 'federal authority',
            'uae', 'united arab emirates', 'الإمارات'
        ]
        
        # Check for Emirates ID number pattern
        emirates_pattern = r'784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d'
        
        # Score-based detection
        keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
        pattern_matches = 1 if re.search(emirates_pattern, text, re.IGNORECASE) else 0
        
        return (keyword_matches >= 2) or (keyword_matches >= 1 and pattern_matches >= 1)
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Enhanced preprocessing for Emirates ID"""
        processed_images = []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. CLAHE enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        processed_images.append(enhanced)
        
        # 2. Bilateral filtering for denoising
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        processed_images.append(denoised)
        
        # 3. Adaptive thresholding
        adaptive = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(adaptive)
        
        # 4. Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel)
        processed_images.append(morph)
        
        # 5. Contrast enhancement
        contrast_enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)
        processed_images.append(contrast_enhanced)
        
        # 6. Gamma correction
        gamma = 1.2
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                         for i in np.arange(0, 256)]).astype("uint8")
        gamma_corrected = cv2.LUT(enhanced, table)
        processed_images.append(gamma_corrected)
        
        return processed_images
    
    def _get_ocr_configs(self) -> List[str]:
        """OCR configurations optimized for Emirates ID"""
        return [
            '--psm 6 --oem 3 -l ara+eng',
            '--psm 4 --oem 3 -l ara+eng',
            '--psm 3 --oem 3 -l eng',
            '--psm 8 --oem 3 -l eng',
            '--psm 7 --oem 3 -l eng',
            '--psm 6 --oem 3 -l ara'
        ]
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract Emirates ID specific information"""
        info = {
            'document_number': None,
            'full_name': None,
            'date_of_birth': None,
            'date_of_expiry': None,
            'nationality': 'UAE',
            'gender': None
        }
        
        combined_text = '\n'.join(text_results).replace('\n', ' ')
        
        # Extract information using helper methods
        info['document_number'] = self._extract_document_number(combined_text)
        info['full_name'] = self._extract_name(combined_text)
        info['date_of_birth'] = self._extract_date_of_birth(combined_text)
        info['date_of_expiry'] = self._extract_expiry_date(combined_text)
        info['gender'] = self._extract_gender(combined_text)
        
        return info
    
    def _extract_document_number(self, text: str) -> Optional[str]:
        """Extract Emirates ID number"""
        patterns = [
            r'784[-\s]?(\d{4})[-\s]?(\d{7})[-\s]?(\d)',
            r'(\d{3})[-\s]?(\d{4})[-\s]?(\d{7})[-\s]?(\d)',
            r'ID\s*[:\s]*(784[-\s]?\d{4}[-\s]?\d{7}[-\s]?\d)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._format_emirates_id(match.groups())
        return None
    
    def _format_emirates_id(self, groups: tuple) -> str:
        """Format Emirates ID number consistently"""
        if len(groups) == 1:  # Pattern with ID prefix
            return groups[0].replace(' ', '-')
        elif len(groups) >= 3:
            # Standard pattern with separate groups
            if groups[0] == '784' or len(groups[0]) == 3:
                suffix = groups[3] if len(groups) > 3 else groups[2][-1]
                return f"784-{groups[1]}-{groups[2]}-{suffix}"
            else:
                return f"784-{groups[0]}-{groups[1]}-{groups[2]}"
        return '-'.join(groups)
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name"""
        patterns = [
            r'Name[:\s]+([A-Z][A-Za-z\s]+?)(?:\n|$|[0-9])',
            r'اسم[:\s]+([A-Za-z\s]+?)(?:\n|$)',
            r'(?:Name|اسم)[:\s]*([A-Z][A-Za-z\s]{2,40}?)(?:\s*(?:ID|Date|DOB|Born|\d))',
            r'([A-Z][A-Z\s]{5,40}?)(?:\s+(?:Male|Female|M|F|\d{2}[/-]\d{2}))'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if (len(name) > 4 and 
                    name.replace(' ', '').isalpha() and 
                    not any(x in name.lower() for x in ['emirates', 'authority', 'identity', 'card', 'uae'])):
                    return name
        return None
    
    def _extract_date_of_birth(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:DOB|Date of Birth|Born)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:تاريخ الميلاد)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-](?:19|20)\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _extract_expiry_date(self, text: str) -> Optional[str]:
        """Extract expiry date"""
        patterns = [
            r'(?:Expiry|Expires|Valid Until)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:انتهاء الصلاحية)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _extract_gender(self, text: str) -> Optional[str]:
        """Extract gender"""
        patterns = [
            r'(?:Gender|Sex)[:\s]*(Male|Female|M|F)',
            r'(?:الجنس)[:\s]*(ذكر|أنثى|Male|Female)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gender = match.group(1).upper()
                if gender in ['MALE', 'M', 'ذكر']:
                    return 'M'
                elif gender in ['FEMALE', 'F', 'أنثى']:
                    return 'F'
        return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date format to DD/MM/YYYY"""
        if not date_str:
            return None
        
        # Clean the date string
        date_str = re.sub(r'[^\d/-]', '', date_str.strip())
        
        # Handle DD/MM/YY format (convert to DD/MM/YYYY)
        if re.match(r'\d{1,2}/\d{1,2}/\d{2}$', date_str):
            parts = date_str.split('/')
            year = int(parts[2])
            # Assume years 00-30 are 2000s, 31-99 are 1900s
            full_year = 2000 + year if year <= 30 else 1900 + year
            return f"{int(parts[0]):02d}/{int(parts[1]):02d}/{full_year}"
        
        # Handle DD/MM/YYYY format
        if re.match(r'\d{1,2}/\d{1,2}/\d{4}$', date_str):
            parts = date_str.split('/')
            return f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"
        
        # Handle DD-MM-YYYY format
        if re.match(r'\d{1,2}-\d{1,2}-\d{4}$', date_str):
            parts = date_str.split('-')
            return f"{int(parts[0]):02d}/{int(parts[1]):02d}/{parts[2]}"
        
        return date_str
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate confidence specific to Emirates ID"""
        confidence = 0.0
        
        # Emirates ID number (high weight)
        if info.get('document_number') and '784' in str(info['document_number']):
            confidence += 0.4
        
        # Name extraction
        if info.get('full_name') and len(str(info['full_name'])) > 4:
            confidence += 0.2
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.2
        
        # Nationality (should always be UAE for Emirates ID)
        if info.get('nationality') == 'UAE':
            confidence += 0.1
        
        # Gender
        if info.get('gender') in ['M', 'F']:
            confidence += 0.1
        
        return confidence
