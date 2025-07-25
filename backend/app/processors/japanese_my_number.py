"""
Japanese My Number Card processor
For Japanese Individual Number cards (マイナンバーカード)
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class JapaneseMyNumberProcessor(DocumentProcessor):
    """Processor for Japanese My Number Cards (Individual Number Cards)"""
    
    def __init__(self):
        super().__init__('Japan', 'japanese_my_number')
        self.supported_languages = ['jpn', 'eng']
        self.confidence_threshold = 0.75
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is a Japanese My Number card"""
        text_lower = text.lower()
        
        # Look for My Number card specific indicators
        my_number_indicators = [
            'マイナンバーカード',
            'my number card',
            'individual number card',
            '個人番号カード',
            'japan',
            '日本',
            'digital agency',
            'デジタル庁',
            '総務省',
            'ministry of internal affairs'
        ]
        
        # Check for My Number pattern (12 digits)
        my_number_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
        has_my_number = bool(re.search(my_number_pattern, text))
        
        # Check for Japanese characters
        has_japanese = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))
        
        # Enhanced detection
        indicator_count = sum(1 for indicator in my_number_indicators if indicator in text_lower)
        
        return (has_my_number and has_japanese) or indicator_count >= 2
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess My Number card image for optimal OCR"""
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
        
        # 2. Bilateral filtering for Japanese characters
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        processed_images.append(cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR))
        
        # 3. Gaussian blur and threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Adaptive threshold for Japanese text
        adaptive_thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 15, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 5. Morphological operations for character clarity
        kernel = np.ones((1, 1), np.uint8)
        morph = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from My Number card OCR text"""
        info = {
            'document_number': None,  # My Number
            'full_name': None,
            'full_name_kana': None,  # Katakana reading
            'date_of_birth': None,
            'address': None,
            'sex': None,
            'date_of_issue': None,
            'date_of_expiry': None,
            'issuing_authority': None,
            'nationality': 'Japanese',
            'document_type': 'My Number Card',
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Extract different fields using helper methods
        info['document_number'] = self._extract_my_number(combined_text)
        info['full_name'] = self._extract_name(combined_text)
        info['full_name_kana'] = self._extract_name_kana(combined_text)
        info['date_of_birth'] = self._extract_date_of_birth(combined_text)
        info['address'] = self._extract_address(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['date_of_issue'] = self._extract_date_of_issue(combined_text)
        info['date_of_expiry'] = self._extract_date_of_expiry(combined_text)
        info['issuing_authority'] = self._extract_issuing_authority(combined_text)
        
        return info
    
    def _extract_my_number(self, text: str) -> Optional[str]:
        """Extract My Number (12 digits)"""
        # My Number format: 4-4-4 digits
        patterns = [
            r'(?:個人番号|マイナンバー|My Number)[:\s]*(\d{4}\s?\d{4}\s?\d{4})',
            r'\b(\d{4}\s?\d{4}\s?\d{4})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                my_number = re.sub(r'\s+', ' ', match.group(1)).strip()
                # Validate 12 digits
                if len(re.sub(r'\D', '', my_number)) == 12:
                    return my_number
        return None
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name (Kanji/Hiragana)"""
        patterns = [
            r'(?:氏名|名前)[:\s]*([一-龯ひ-ゖ\s]+?)(?:\n|生年月日|住所)',
            r'([一-龯]{2,10}\s*[一-龯]{1,10})',  # Kanji name pattern
            r'([ひ-ゖ]{2,15}\s*[ひ-ゖ]{1,15})'   # Hiragana name pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 1:
                    return name
        return None
    
    def _extract_name_kana(self, text: str) -> Optional[str]:
        """Extract name in Katakana reading"""
        patterns = [
            r'(?:フリガナ|カナ)[:\s]*([ァ-ヾ\s]+?)(?:\n|生年月日|住所)',
            r'([ァ-ヾ]{2,15}\s*[ァ-ヾ]{1,15})'  # Katakana pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                kana = match.group(1).strip()
                if len(kana) > 1:
                    return kana
        return None
    
    def _extract_date_of_birth(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:生年月日|生まれ)[:\s]*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2})',
            r'(?:Date of Birth)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',  # Japanese date format
            r'([Hh]\d{1,2}\.\d{1,2}\.\d{1,2})',  # Heisei era format
            r'([Rr]\d{1,2}\.\d{1,2}\.\d{1,2})'   # Reiwa era format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._normalize_japanese_date(match.group(1))
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address"""
        patterns = [
            r'(?:住所)[:\s]*([都道府県市区町村\d一-龯ひ-ゖァ-ヾー\s\-]+?)(?:\n|性別|有効期限)',
            r'([都道府県][市区町村][一-龯\d\s\-]+)',  # Prefecture + city pattern
            r'(\d{3}-\d{4}\s*[都道府県市区町村一-龯\s\-]+)'  # Postal code + address
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                address = match.group(1).strip()
                if len(address) > 5:
                    return address
        return None
    
    def _extract_sex(self, text: str) -> Optional[str]:
        """Extract sex/gender"""
        patterns = [
            r'(?:性別)[:\s]*(男|女|M|F)',
            r'\b(男|女|Male|Female|M|F)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                sex = match.group(1).upper()
                if sex in ['男', 'M', 'MALE']:
                    return 'Male'
                elif sex in ['女', 'F', 'FEMALE']:
                    return 'Female'
        return None
    
    def _extract_date_of_issue(self, text: str) -> Optional[str]:
        """Extract date of issue"""
        patterns = [
            r'(?:交付年月日|発行日)[:\s]*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日交付)',
            r'([HRhr]\d{1,2}\.\d{1,2}\.\d{1,2}交付)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._normalize_japanese_date(match.group(1))
        return None
    
    def _extract_date_of_expiry(self, text: str) -> Optional[str]:
        """Extract date of expiry"""
        patterns = [
            r'(?:有効期限)[:\s]*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日まで)',
            r'([HRhr]\d{1,2}\.\d{1,2}\.\d{1,2}まで)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._normalize_japanese_date(match.group(1))
        return None
    
    def _extract_issuing_authority(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        patterns = [
            r'(デジタル庁)',
            r'(総務省)',
            r'(市区町村長)',
            r'([一-龯]{2,10}市長)',
            r'([一-龯]{2,10}区長)',
            r'([一-龯]{2,10}町長)',
            r'([一-龯]{2,10}村長)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _normalize_japanese_date(self, date_str: str) -> str:
        """Normalize Japanese date format to DD/MM/YYYY"""
        if not date_str:
            return date_str
        
        # Handle Japanese era dates (Heisei, Reiwa)
        if re.match(r'[HhRr]\d', date_str):
            # Convert era to Western calendar
            if date_str.lower().startswith('h'):
                # Heisei era (1989-2019)
                era_match = re.match(r'[Hh](\d{1,2})\.(\d{1,2})\.(\d{1,2})', date_str)
                if era_match:
                    era_year, month, day = era_match.groups()
                    year = 1988 + int(era_year)  # Heisei 1 = 1989
                    return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
            elif date_str.lower().startswith('r'):
                # Reiwa era (2019-)
                era_match = re.match(r'[Rr](\d{1,2})\.(\d{1,2})\.(\d{1,2})', date_str)
                if era_match:
                    era_year, month, day = era_match.groups()
                    year = 2018 + int(era_year)  # Reiwa 1 = 2019
                    return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        # Handle standard Japanese date format (YYYY年MM月DD日)
        japanese_date_match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日?', date_str)
        if japanese_date_match:
            year, month, day = japanese_date_match.groups()
            return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        # Handle Western format dates
        western_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
        ]
        
        for pattern in western_patterns:
            match = re.search(pattern, date_str)
            if match:
                part1, part2, part3 = match.groups()
                
                if len(part1) == 4:  # Year first
                    year, month, day = part1, part2, part3
                else:
                    day, month, year = part1, part2, part3
                
                return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        return date_str
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "Japanese My Number Card"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "JP"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for Japanese text"""
        return [
            '--psm 6 --oem 3 -l jpn+eng',
            '--psm 4 --oem 3 -l jpn+eng',
            '--psm 3 --oem 3 -l jpn',
            '--psm 8 --oem 3 -l jpn',
            '--psm 6 --oem 3 -l eng'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for My Number card"""
        confidence = 0.0
        
        # My Number is crucial
        if info.get('document_number'):
            my_number = re.sub(r'\D', '', info['document_number'])
            if len(my_number) == 12:
                confidence += 0.4
        
        # Name (Kanji/Hiragana)
        if info.get('full_name'):
            confidence += 0.2
        
        # Name reading (Katakana)
        if info.get('full_name_kana'):
            confidence += 0.1
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.15
        
        # Address
        if info.get('address'):
            confidence += 0.1
        
        # Sex
        if info.get('sex'):
            confidence += 0.05
        
        return min(confidence, 1.0)
