"""
European Union ID Card processor
Supports ID cards from EU member states
"""
import re
import cv2
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from . import DocumentProcessor


class EUIDCardProcessor(DocumentProcessor):
    """Processor for European Union ID Cards"""
    
    def __init__(self):
        super().__init__('European Union', 'eu_id_card')
        self.supported_languages = ['eng', 'deu', 'fra', 'ita', 'spa', 'nld', 'por']
        self.confidence_threshold = 0.7
        
        # EU country codes and indicators
        self.eu_countries = {
            'DEU': ['deutschland', 'germany', 'bundesrepublik'],
            'FRA': ['france', 'république française', 'republique francaise'],
            'ITA': ['italia', 'italy', 'repubblica italiana'],
            'ESP': ['españa', 'spain', 'reino de españa'],
            'NLD': ['nederland', 'netherlands', 'koninkrijk der nederlanden'],
            'BEL': ['belgique', 'belgium', 'belgië', 'koninkrijk belgië'],
            'AUT': ['österreich', 'austria', 'republik österreich'],
            'PRT': ['portugal', 'república portuguesa'],
            'GRC': ['ελλάδα', 'greece', 'hellenic republic'],
            'IRL': ['ireland', 'éire', 'poblacht na héireann'],
            'FIN': ['finland', 'suomi', 'republic of finland'],
            'SWE': ['sweden', 'sverige', 'kingdom of sweden'],
            'DNK': ['denmark', 'danmark', 'kingdom of denmark'],
            'POL': ['poland', 'polska', 'republic of poland'],
            'CZE': ['czech republic', 'česká republika'],
            'HUN': ['hungary', 'magyarország'],
            'SVK': ['slovakia', 'slovenská republika'],
            'SVN': ['slovenia', 'slovenija'],
            'EST': ['estonia', 'eesti'],
            'LVA': ['latvia', 'latvija'],
            'LTU': ['lithuania', 'lietuva'],
            'LUX': ['luxembourg', 'lëtzebuerg'],
            'MLT': ['malta', 'repubblika ta\' malta'],
            'CYP': ['cyprus', 'κύπρος'],
            'BGR': ['bulgaria', 'българия'],
            'ROU': ['romania', 'românia'],
            'HRV': ['croatia', 'hrvatska'],
        }
    
    def detect(self, text: str, image: np.ndarray = None) -> bool:
        """Detect if the document is an EU ID card"""
        text_lower = text.lower()
        
        # Look for EU-specific indicators
        eu_indicators = [
            'identity card',
            'personalausweis',
            'carte d\'identité',
            'carta d\'identità',
            'documento nacional de identidad',
            'identiteitskaart',
            'documento de identidade',
            'european union',
            'union européenne',
            'unión europea',
            'europäische union'
        ]
        
        # Check for EU country indicators
        country_matches = 0
        detected_country = None
        for country_code, country_names in self.eu_countries.items():
            if any(name in text_lower for name in country_names):
                country_matches += 1
                detected_country = country_code
                break
        
        # Check for ID card specific patterns
        id_patterns = [
            r'\b[A-Z]{2}\d{6,9}\b',  # Common EU ID format
            r'\b\d{9}\b',            # 9-digit ID numbers
            r'\b[A-Z]\d{8}\b',       # Letter + 8 digits
            r'\b\d{6}[A-Z]{2}\b'     # 6 digits + 2 letters
        ]
        
        has_id_pattern = any(re.search(pattern, text) for pattern in id_patterns)
        
        # Enhanced detection
        indicator_count = sum(1 for indicator in eu_indicators if indicator in text_lower)
        
        return (country_matches > 0 and indicator_count >= 1) or has_id_pattern
    
    def preprocess(self, image: np.ndarray) -> List[np.ndarray]:
        """Preprocess EU ID card image for optimal OCR"""
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
        
        # 2. Bilateral filtering for noise reduction
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        processed_images.append(cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR))
        
        # 3. Gaussian blur and threshold
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
        
        # 4. Adaptive threshold
        adaptive_thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                              cv2.THRESH_BINARY, 11, 2)
        processed_images.append(cv2.cvtColor(adaptive_thresh, cv2.COLOR_GRAY2BGR))
        
        # 5. Edge enhancement
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        processed_images.append(cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR))
        
        return processed_images
    
    def extract_info(self, text_results: List[str]) -> Dict[str, Any]:
        """Extract structured information from EU ID card OCR text"""
        info = {
            'document_number': None,
            'surname': None,
            'given_names': None,
            'date_of_birth': None,
            'place_of_birth': None,
            'nationality': None,
            'sex': None,
            'date_of_issue': None,
            'date_of_expiry': None,
            'issuing_authority': None,
            'country_code': None,
            'document_type': 'EU ID Card',
            'raw_text': ' '.join(text_results)
        }
        
        combined_text = ' '.join(text_results)
        
        # Detect country first
        info['country_code'] = self._detect_country(combined_text)
        info['nationality'] = self._extract_nationality(combined_text)
        
        # Extract fields using helper methods
        info['document_number'] = self._extract_id_number(combined_text)
        info['surname'] = self._extract_surname(combined_text)
        info['given_names'] = self._extract_given_names(combined_text)
        info['date_of_birth'] = self._extract_date_of_birth(combined_text)
        info['place_of_birth'] = self._extract_place_of_birth(combined_text)
        info['sex'] = self._extract_sex(combined_text)
        info['date_of_issue'] = self._extract_date_of_issue(combined_text)
        info['date_of_expiry'] = self._extract_date_of_expiry(combined_text)
        info['issuing_authority'] = self._extract_issuing_authority(combined_text)
        
        return info
    
    def _detect_country(self, text: str) -> Optional[str]:
        """Detect which EU country issued the ID"""
        text_lower = text.lower()
        
        for country_code, country_names in self.eu_countries.items():
            if any(name in text_lower for name in country_names):
                return country_code
        return None
    
    def _extract_id_number(self, text: str) -> Optional[str]:
        """Extract ID number based on various EU formats"""
        patterns = [
            r'\b([A-Z]{2}\d{6,9})\b',  # Common EU format
            r'\b(\d{9})\b',            # 9-digit numbers
            r'\b([A-Z]\d{8})\b',       # Letter + 8 digits
            r'\b(\d{6}[A-Z]{2})\b',    # 6 digits + 2 letters
            r'(?:ID[:\s]+|Nr[:\s]+|No[:\s]+)([A-Z0-9]{6,12})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_surname(self, text: str) -> Optional[str]:
        """Extract surname (family name)"""
        patterns = [
            r'(?:Surname[:\s]+|Nachname[:\s]+|Nom[:\s]+|Cognome[:\s]+|Apellidos[:\s]+)([A-Z][A-Za-z\s-]+?)(?:\n|Given|Vorname|Prénom)',
            r'(?:Family Name[:\s]+|Nom de famille[:\s]+)([A-Z][A-Za-z\s-]+?)(?:\n|Given|First)',
            r'^([A-Z][A-Z\s-]+?)(?:\n|,|\s{2,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                surname = match.group(1).strip()
                if len(surname) > 1:
                    return surname
        return None
    
    def _extract_given_names(self, text: str) -> Optional[str]:
        """Extract given names (first names)"""
        patterns = [
            r'(?:Given Names[:\s]+|Vornamen[:\s]+|Prénoms[:\s]+|Nomi[:\s]+|Nombres[:\s]+)([A-Za-z\s]+?)(?:\n|Date|Sex)',
            r'(?:First Name[:\s]+|Prénom[:\s]+)([A-Za-z\s]+?)(?:\n|Date|Sex)',
            r'(?:Vorname[:\s]+)([A-Za-z\s]+?)(?:\n|Geburtsdatum|Geschlecht)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                given_names = match.group(1).strip()
                if len(given_names) > 1:
                    return given_names
        return None
    
    def _extract_date_of_birth(self, text: str) -> Optional[str]:
        """Extract date of birth"""
        patterns = [
            r'(?:Date of Birth[:\s]+|Geburtsdatum[:\s]+|Date de naissance[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'(?:Born[:\s]+|Né[:\s]+|Geboren[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'(\d{1,2}[./-]\d{1,2}[./-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _extract_place_of_birth(self, text: str) -> Optional[str]:
        """Extract place of birth"""
        patterns = [
            r'(?:Place of Birth[:\s]+|Geburtsort[:\s]+|Lieu de naissance[:\s]+)([A-Za-z\s,.-]+?)(?:\n|Sex|Nationality)',
            r'(?:Born in[:\s]+|Né à[:\s]+|Geboren in[:\s]+)([A-Za-z\s,.-]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                if len(place) > 2:
                    return place
        return None
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality"""
        # First try to detect from country indicators
        country_code = self._detect_country(text)
        if country_code:
            nationality_map = {
                'DEU': 'German', 'FRA': 'French', 'ITA': 'Italian', 'ESP': 'Spanish',
                'NLD': 'Dutch', 'BEL': 'Belgian', 'AUT': 'Austrian', 'PRT': 'Portuguese',
                'GRC': 'Greek', 'IRL': 'Irish', 'FIN': 'Finnish', 'SWE': 'Swedish',
                'DNK': 'Danish', 'POL': 'Polish', 'CZE': 'Czech', 'HUN': 'Hungarian'
            }
            return nationality_map.get(country_code, country_code)
        
        # Fallback to text patterns
        patterns = [
            r'(?:Nationality[:\s]+|Nationalité[:\s]+|Staatsangehörigkeit[:\s]+)([A-Za-z]+)',
            r'\b(German|French|Italian|Spanish|Dutch|Belgian|Austrian|Portuguese|Greek|Irish|Finnish|Swedish|Danish|Polish|Czech|Hungarian)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_sex(self, text: str) -> Optional[str]:
        """Extract sex/gender"""
        patterns = [
            r'(?:Sex[:\s]+|Geschlecht[:\s]+|Sexe[:\s]+)(M|F|Male|Female|Männlich|Weiblich|Masculin|Féminin)',
            r'\b(M|F|Male|Female|Männlich|Weiblich|Masculin|Féminin)\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sex = match.group(1).upper()
                if sex in ['M', 'MALE', 'MÄNNLICH', 'MASCULIN']:
                    return 'M'
                elif sex in ['F', 'FEMALE', 'WEIBLICH', 'FÉMININ']:
                    return 'F'
        return None
    
    def _extract_date_of_issue(self, text: str) -> Optional[str]:
        """Extract date of issue"""
        patterns = [
            r'(?:Date of Issue[:\s]+|Ausstellungsdatum[:\s]+|Date de délivrance[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'(?:Issued[:\s]+|Délivré[:\s]+|Ausgestellt[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _extract_date_of_expiry(self, text: str) -> Optional[str]:
        """Extract date of expiry"""
        patterns = [
            r'(?:Date of Expiry[:\s]+|Gültig bis[:\s]+|Valable jusqu\'au[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'(?:Expires[:\s]+|Expire[:\s]+|Ablauf[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})',
            r'(?:Valid until[:\s]+|Valide jusqu\'au[:\s]+)(\d{1,2}[./-]\d{1,2}[./-]\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._normalize_date(match.group(1))
        return None
    
    def _extract_issuing_authority(self, text: str) -> Optional[str]:
        """Extract issuing authority"""
        patterns = [
            r'(?:Issuing Authority[:\s]+|Ausstellende Behörde[:\s]+|Autorité de délivrance[:\s]+)([A-Za-z\s,.-]+?)(?:\n|$)',
            r'(?:Issued by[:\s]+|Délivré par[:\s]+|Ausgestellt von[:\s]+)([A-Za-z\s,.-]+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                authority = match.group(1).strip()
                if len(authority) > 3:
                    return authority
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to DD/MM/YYYY format"""
        if not date_str:
            return date_str
        
        # Try different date patterns
        patterns = [
            r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})',  # DD/MM/YYYY or MM/DD/YYYY
            r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})'   # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                part1, part2, part3 = match.groups()
                
                # Handle YYYY/MM/DD format
                if len(part1) == 4:  # Year first
                    year, month, day = part1, part2, part3
                else:
                    # Assume DD/MM/YYYY format for EU documents
                    day, month, year = part1, part2, part3
                
                # Ensure proper formatting
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
        
        return date_str
    
    def get_display_name(self) -> str:
        """Get display name for this document type"""
        return "EU ID Card"
    
    def get_country_code(self) -> str:
        """Get ISO country code"""
        return "EU"
    
    def _get_ocr_configs(self) -> List[str]:
        """Get OCR configurations optimized for EU ID cards"""
        return [
            '--psm 6 --oem 3 -l eng',
            '--psm 4 --oem 3 -l eng',
            '--psm 3 --oem 3 -l eng+deu+fra+ita+spa',
            '--psm 8 --oem 3 -l eng',
            '--psm 6 --oem 3 -l deu+fra+ita+spa'
        ]
    
    def _calculate_confidence(self, info: Dict[str, Any]) -> float:
        """Calculate processing confidence for EU ID card"""
        confidence = 0.0
        
        # ID number
        if info.get('document_number'):
            confidence += 0.3
        
        # Country detection
        if info.get('country_code'):
            confidence += 0.2
        
        # Name fields
        if info.get('surname'):
            confidence += 0.15
        
        if info.get('given_names'):
            confidence += 0.1
        
        # Date of birth
        if info.get('date_of_birth'):
            confidence += 0.1
        
        # Nationality
        if info.get('nationality'):
            confidence += 0.1
        
        # Sex
        if info.get('sex'):
            confidence += 0.05
        
        return min(confidence, 1.0)
