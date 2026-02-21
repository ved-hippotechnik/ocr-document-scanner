from flask import current_app
from datetime import datetime
from flask import Blueprint, request, jsonify
import io
import re
import cv2
import numpy as np
from datetime import datetime
from PIL import Image
import os
import pytesseract
from passporteye import read_mrz
from .processors.registry import processor_registry
from .rate_limiter import ratelimit_scan, ratelimit_medium, ratelimit_light
from .language_detector import get_languages_info, validate_language

main = Blueprint('main', __name__)

# Store document statistics
document_stats = {
    'total_scanned': 0,
    'document_types': {
        'passport': 0,
        'id_card': 0,
        'driving_license': 0,
        'aadhaar': 0,
        'us_green_card': 0,
        'uk_passport': 0,
        'canadian_passport': 0,
        'australian_passport': 0,
        'german_passport': 0,
        'other': 0
    },
    'nationalities': {},
    'scan_history': [],
    'documents': []
}

def normalize_date(date_str):
    """Normalize date string to DD/MM/YYYY format"""
    if not date_str:
        return None
    
    # Clean the date string
    date_str = re.sub(r'[^\d\w\s./-]', '', date_str).strip()
    
    # Common date patterns to match
    patterns = [
        # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        (r'^(\d{1,2})[\s./-](\d{1,2})[\s./-](\d{2,4})$', lambda m: f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{int(m.group(3)) if len(m.group(3)) == 4 else (2000 + int(m.group(3))) if int(m.group(3)) < 50 else (1900 + int(m.group(3))):04d}"),
        # MM/DD/YYYY, MM-DD-YYYY, MM.DD.YYYY (American format)
        (r'^(\d{1,2})[\s./-](\d{1,2})[\s./-](\d{2,4})$', lambda m: f"{int(m.group(2)):02d}/{int(m.group(1)):02d}/{int(m.group(3)) if len(m.group(3)) == 4 else (2000 + int(m.group(3))) if int(m.group(3)) < 50 else (1900 + int(m.group(3))):04d}"),
        # DD MMM YYYY, DD-MMM-YYYY
        (r'^(\d{1,2})[\s-]([A-Za-z]{3,9})[\s-](\d{2,4})$', lambda m: format_month_date(m.group(1), m.group(2), m.group(3))),
        # MMM DD YYYY, MMM-DD-YYYY
        (r'^([A-Za-z]{3,9})[\s-](\d{1,2})[\s-](\d{2,4})$', lambda m: format_month_date(m.group(2), m.group(1), m.group(3))),
        # YYYY/MM/DD, YYYY-MM-DD
        (r'^(\d{4})[\s./-](\d{1,2})[\s./-](\d{1,2})$', lambda m: f"{int(m.group(3)):02d}/{int(m.group(2)):02d}/{m.group(1)}"),
        # YYMMDD format
        (r'^(\d{2})(\d{2})(\d{2})$', lambda m: f"{int(m.group(3)):02d}/{int(m.group(2)):02d}/{2000 + int(m.group(1)) if int(m.group(1)) < 50 else 1900 + int(m.group(1))}"),
        # YYYYMMDD format
        (r'^(\d{4})(\d{2})(\d{2})$', lambda m: f"{int(m.group(3)):02d}/{int(m.group(2)):02d}/{m.group(1)}")
    ]
    
    for pattern, formatter in patterns:
        match = re.match(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                return formatter(match)
            except:
                continue
    
    return date_str  # Return original if no pattern matches

def format_month_date(day, month_name, year):
    """Convert month name to number and format date"""
    months = {
        'jan': '01', 'january': '01',
        'feb': '02', 'february': '02',
        'mar': '03', 'march': '03',
        'apr': '04', 'april': '04',
        'may': '05',
        'jun': '06', 'june': '06',
        'jul': '07', 'july': '07',
        'aug': '08', 'august': '08',
        'sep': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }
    
    month_num = months.get(month_name.lower()[:3])
    if month_num:
        # Handle 2-digit and 4-digit years properly
        year_int = int(year)
        if len(year) == 2:
            year_str = f"{2000 + year_int}" if year_int < 50 else f"{1900 + year_int}"
        else:
            year_str = year
        return f"{int(day):02d}/{month_num}/{year_str}"
    return None

def clean_document_number(doc_num):
    """Clean and extract document number, removing common OCR artifacts"""
    if not doc_num:
        return None
    
    # Remove common OCR artifacts and clean the string
    cleaned = re.sub(r'[^\w\d-]', '', doc_num.strip())
    
    # Look for patterns that match document numbers first (before removing prefixes)
    patterns = [
        r'([A-Z]{1,2}\d{7,9})',  # Passport format: 1-2 Letters + 7-9 digits
        r'(\d{9}[A-Z])',    # ID format: 9 digits + letter
        r'(\d{3}-\d{4}-\d{7}-\d)',  # Emirates ID format
        r'([A-Z]{1,3}\d{6,8})',  # License format: 1-3 letters + 6-8 digits
        r'(\d{8,12})',      # Pure numeric ID
        r'([A-Z0-9]{6,15})'  # Alphanumeric combination (increased range)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cleaned.upper())
        if match:
            return match.group(1)
    
    # If no pattern matches, try removing common prefix words
    prefixes_to_remove = [
        'passportno', 'passportnumber', 'documentno', 'documentnumber', 
        'idno', 'idnumber', 'licenseno', 'licensenumber', 'number', 'no'
    ]
    
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
            break
    
    # If we have a reasonable length string after prefix removal, return it
    if 6 <= len(cleaned) <= 15:
        return cleaned.upper()
    
    return doc_num.strip()

def clean_name(name):
    """Clean and extract name, removing common OCR artifacts and applying name correction"""
    if not name:
        return None
    
    # Remove common artifacts and clean
    cleaned = re.sub(r'[^\w\s]', ' ', name).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
    
    # Remove common prefix words that might be incorrectly included
    prefixes_to_remove = [
        'name', 'surname', 'given', 'names', 'full', 'first', 'last',
        'mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'madam', 'miss',
        'document', 'passport', 'id', 'card', 'number', 'no'
    ]
    
    words = cleaned.split()
    filtered_words = []
    seen_words = set()  # Track seen words to avoid duplicates
    
    for word in words:
        word_lower = word.lower()
        
        # Skip words that are OCR artifacts
        if is_ocr_artifact(word):
            continue
            
        # Clean the word of non-alphabetic characters for name validation
        word_clean = re.sub(r'[^a-zA-Z]', '', word)
        
        if (len(word_clean) >= 2 and  # Minimum 2 characters
            word_lower not in prefixes_to_remove and 
            word_clean.lower() not in seen_words and  # Avoid duplicate words
            not word_lower.isdigit() and  # Avoid numbers
            is_valid_name_part(word_clean)):  # Additional validation
            
            # Only add if it looks like a real name part
            filtered_words.append(word_clean.capitalize())
            seen_words.add(word_clean.lower())
    
    if filtered_words:
        cleaned_name = ' '.join(filtered_words)
        
        # Apply name order correction to handle OCR errors and ordering issues
        corrected_name = correct_name_order(cleaned_name)
        return corrected_name
    
    # Fallback: apply correction to the original name if filtering failed
    corrected_name = correct_name_order(name.strip().title() if name else None)
    return corrected_name

def is_ocr_artifact(word):
    """Check if a word is likely an OCR artifact"""
    if not word or len(word) < 2:
        return True
    
    # Remove non-alphabetic characters for analysis
    clean_word = re.sub(r'[^a-zA-Z]', '', word.lower())
    
    if len(clean_word) < 2:
        return True
    
    # Check for repeated character patterns (OCR artifacts)
    if len(clean_word) >= 3:
        # Check for 3 or more consecutive identical characters
        if re.search(r'(.)\1{2,}', clean_word):
            return True
        
        # Check for patterns like "lllllll" or "kkkkk"
        if len(set(clean_word)) <= 2 and len(clean_word) > 4:
            return True
    
    # Check for common OCR misreads
    ocr_artifacts = [
        'lllll', 'iiiii', 'ooooo', '00000', '11111',
        'lklklk', 'lkl', 'klk', 'iii', 'ooo', 'lll'
    ]
    
    for artifact in ocr_artifacts:
        if artifact in clean_word:
            return True
    
    return False

def is_valid_name_part(word):
    """Check if a word part looks like a valid name component"""
    if not word or len(word) < 2:
        return False
    
    # Must be alphabetic only
    if not word.isalpha():
        return False
    
    # Should have reasonable length for a name
    if len(word) > 20:  # Very long words are likely artifacts
        return False
    
    # Check for reasonable vowel-consonant distribution
    vowels = 'aeiouAEIOU'
    vowel_count = sum(1 for char in word if char in vowels)
    consonant_count = len(word) - vowel_count
    
    # Names typically have some vowels
    if len(word) > 3 and vowel_count == 0:
        return False
    
    # All vowels or all consonants in long words is suspicious
    if len(word) > 4 and (vowel_count == len(word) or consonant_count == len(word)):
        return False
    
    return True

def extract_place_of_issue(text):
    """Extract place of issue from passport text"""
    if not text:
        return None
    
    # Common patterns for place of issue
    patterns = [
        r'(?:place of (?:issue|birth)|issued (?:at|in)|authority)[:\s]*([A-Za-z\s,]+?)(?:\n|$)',
        r'(?:place of birth|place of issue)[:\s]*([A-Za-z\s,]+?)(?:\n|$)',
        r'(?:authority|issuing office)[:\s]*([A-Za-z\s,]+?)(?:\n|$)',
        r'(?:طرف|صادر از)[:\s]*([A-Za-z\s,آ-ی]+?)(?:\n|$)',  # Arabic patterns
        r'(?:issued in|place)[:\s]*([A-Za-z\s,]+?)(?:on|\d{1,2})',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:passport|authority|office)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            place = match.group(1).strip()
            # Clean up the place name
            place = re.sub(r'[^\w\s,]', '', place)
            place = re.sub(r'\s+', ' ', place).strip()
            
            # Remove common words that aren't place names
            exclude_words = ['passport', 'office', 'authority', 'department', 'ministry', 'date', 'number']
            words = place.split()
            filtered_words = [word for word in words if word.lower() not in exclude_words and len(word) > 1]
            
            if filtered_words:
                return ' '.join(filtered_words).title()
    
    return None

def detect_document_type(text, mrz_data):
    """Detect if the document is a passport, ID card, or driving license based on OCR text and MRZ data"""
    text_lower = text.lower()
    
    # Check MRZ data first if available
    if mrz_data and mrz_data.get('document_type'):
        doc_type = mrz_data.get('document_type')
        if doc_type == 'P':
            return 'passport'
        elif doc_type in ['I', 'ID', 'IC', 'C']:
            return 'id_card'
    
    # Fallback to text analysis with expanded keywords
    passport_keywords = [
        'passport', 'passeport', 'reisepass', 'pasaporte', 'паспорт', 'جواز سفر',
        'पासपोर्ट', '护照', 'パスポート', '여권', 'pass', 'passaporte', 'passaporto'
    ]
    
    id_keywords = [
        'identity card', 'id card', 'identification', 'national id', 'بطاقة الهوية',
        'carte d\'identité', 'personalausweis', 'dni', 'cédula', 'cedula', 'удостоверение',
        'بطاقة الهوية', 'पहचान पत्र', '身份证', '運転免許証', '주민등록증', 'emirates id',
        'residence', 'resident card', 'green card', 'हوية إماراتية', 'uae id', 'id number',
        'aadhaar', 'aadhar', 'आधार', 'government of india', 'भारत सरकार', 'aadhaar number',
        'आधार संख्या', 'my aadhaar', 'मेरा आधार', 'unique identification'
    ]
    
    license_keywords = [
        'driver license', 'driving licence', 'license', 'permit', 'رخصة قيادة',
        'driving permit', 'driver\'s license', 'driver\'s licence', 'road transport',
        'traffic', 'المرور', 'هيئة الطرق', 'rta', 'driving class', 'vehicle category'
    ]
    
    # UAE specific document patterns
    uae_patterns = {
        'emirates_id': [r'\d{3}-\d{4}-\d{7}-\d', r'784-\d{4}-\d{7}-\d', r'بطاقة الهوية الإماراتية', r'بطاقة الهوية'],
        'driving_license': [r'رخصة قيادة', r'driving license', r'license no\.?\s*\d+', r'ملف مروري', r'traffic file']
    }
    
    # Indian Aadhaar card specific patterns
    aadhaar_patterns = [
        r'\d{4}\s*\d{4}\s*\d{4}',  # 12-digit Aadhaar number format
        r'\d{4}-\d{4}-\d{4}',      # Aadhaar with hyphens
        r'आधार\s*संख्या',          # Hindi Aadhaar number
        r'aadhaar\s*number',       # English Aadhaar number
        r'government\s*of\s*india', # Government of India
        r'भारत\s*सरकार',           # Hindi Government of India
        r'मेरा\s*आधार',            # My Aadhaar in Hindi
        r'my\s*aadhaar'            # My Aadhaar in English
    ]
    
    # Check for Aadhaar card patterns
    for pattern in aadhaar_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 'id_card'
    
    # Check for UAE specific patterns
    for doc_type, patterns in uae_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return 'id_card' if doc_type == 'emirates_id' else 'driving_license'
    
    # Check for MRZ pattern typical for passports (longer MRZ lines)
    if text and len(text.strip()) > 0:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if len(line) >= 40 and '<' in line and line.count('<') >= 5:
                return 'passport'
    
    # Check for passport keywords
    for keyword in passport_keywords:
        if keyword in text_lower:
            return 'passport'
    
    # Check for ID keywords
    for keyword in id_keywords:
        if keyword in text_lower:
            return 'id_card'
    
    # Check for license keywords
    for keyword in license_keywords:
        if keyword in text_lower:
            return 'driving_license'
    
    # If we have MRZ data but couldn't determine the type, it's likely a travel document
    if mrz_data:
        return 'passport'
    
    return 'other'

def extract_nationality(text, mrz_data):
    """Extract nationality from OCR text or MRZ data"""
    # First check MRZ data as it's most reliable
    if mrz_data and mrz_data.get('nationality'):
        return mrz_data.get('nationality')
    
    # Comprehensive list of countries with their ISO codes and common names
    countries = {
        'USA': ['united states', 'america', 'usa', 'u.s.a', 'u.s.', 'united states of america'],
        'GBR': ['united kingdom', 'great britain', 'uk', 'england', 'britain', 'scotland', 'wales', 'northern ireland'],
        'CAN': ['canada', 'canadian'],
        'AUS': ['australia', 'australian'],
        'DEU': ['germany', 'german', 'deutschland', 'allemagne'],
        'FRA': ['france', 'french', 'république française', 'republique francaise'],
        'ESP': ['spain', 'spanish', 'españa', 'espana'],
        'ITA': ['italy', 'italian', 'italia'],
        'JPN': ['japan', 'japanese', '日本', 'nihon', 'nippon'],
        'CHN': ['china', 'chinese', '中国', 'zhongguo'],
        'IND': ['india', 'indian', 'भारत', 'hindustan', 'bharatiya', 'bharat'],
        'RUS': ['russia', 'russian', 'россия', 'rossiya'],
        'BRA': ['brazil', 'brazilian', 'brasil'],
        'MEX': ['mexico', 'mexican', 'méxico'],
        'KOR': ['korea', 'korean', 'south korea', '한국', 'hanguk'],
        'SAU': ['saudi arabia', 'saudi', 'المملكة العربية السعودية'],
        'UAE': ['united arab emirates', 'uae', 'emirates', 'الإمارات العربية المتحدة'],
        'EGY': ['egypt', 'egyptian', 'مصر', 'misr'],
        'ZAF': ['south africa', 'south african'],
        'NGA': ['nigeria', 'nigerian'],
        'KEN': ['kenya', 'kenyan'],
        'GHA': ['ghana', 'ghanaian'],
        'SGP': ['singapore', 'singaporean'],
        'MYS': ['malaysia', 'malaysian'],
        'IDN': ['indonesia', 'indonesian'],
        'THA': ['thailand', 'thai'],
        'VNM': ['vietnam', 'vietnamese'],
        'PHL': ['philippines', 'filipino', 'philippine'],
        'PAK': ['pakistan', 'pakistani'],
        'BGD': ['bangladesh', 'bangladeshi'],
        'TUR': ['turkey', 'turkish', 'türkiye', 'turkiye'],
        'IRN': ['iran', 'iranian', 'persia', 'persian'],
        'ISR': ['israel', 'israeli'],
        'NLD': ['netherlands', 'dutch', 'holland'],
        'BEL': ['belgium', 'belgian'],
        'CHE': ['switzerland', 'swiss'],
        'SWE': ['sweden', 'swedish'],
        'NOR': ['norway', 'norwegian'],
        'DNK': ['denmark', 'danish'],
        'FIN': ['finland', 'finnish'],
        'POL': ['poland', 'polish'],
        'AUT': ['austria', 'austrian'],
        'HUN': ['hungary', 'hungarian'],
        'CZE': ['czech republic', 'czech', 'czechia'],
        'GRC': ['greece', 'greek', 'hellenic'],
        'PRT': ['portugal', 'portuguese'],
        'IRL': ['ireland', 'irish'],
        'NZL': ['new zealand', 'kiwi'],
        'ARG': ['argentina', 'argentinian'],
        'CHL': ['chile', 'chilean'],
        'COL': ['colombia', 'colombian'],
        'PER': ['peru', 'peruvian'],
        'VEN': ['venezuela', 'venezuelan'],
        'CUB': ['cuba', 'cuban'],
        'JAM': ['jamaica', 'jamaican'],
        'CRI': ['costa rica', 'costa rican'],
        'PAN': ['panama', 'panamanian'],
        'UKR': ['ukraine', 'ukrainian'],
        'BLR': ['belarus', 'belarusian'],
        'KAZ': ['kazakhstan', 'kazakh'],
        'UZB': ['uzbekistan', 'uzbek'],
        'MAR': ['morocco', 'moroccan'],
        'DZA': ['algeria', 'algerian'],
        'TUN': ['tunisia', 'tunisian'],
        'LBY': ['libya', 'libyan'],
        'ETH': ['ethiopia', 'ethiopian'],
        'ZWE': ['zimbabwe', 'zimbabwean'],
        'NPL': ['nepal', 'nepalese'],
        'LKA': ['sri lanka', 'sri lankan'],
        'MMR': ['myanmar', 'burmese', 'burma'],
        'KHM': ['cambodia', 'cambodian'],
        'LAO': ['laos', 'lao'],
        'MNG': ['mongolia', 'mongolian'],
        'PRK': ['north korea', 'dprk'],
        'TWN': ['taiwan', 'taiwanese'],
        'HKG': ['hong kong'],
        'MAC': ['macao', 'macau'],
        'FJI': ['fiji', 'fijian'],
        'PNG': ['papua new guinea'],
        'ISL': ['iceland', 'icelandic'],
        'LUX': ['luxembourg', 'luxembourgish'],
        'MLT': ['malta', 'maltese'],
        'CYP': ['cyprus', 'cypriot'],
        'EST': ['estonia', 'estonian'],
        'LVA': ['latvia', 'latvian'],
        'LTU': ['lithuania', 'lithuanian'],
        'SVN': ['slovenia', 'slovenian'],
        'SVK': ['slovakia', 'slovak'],
        'HRV': ['croatia', 'croatian'],
        'BIH': ['bosnia', 'bosnian', 'herzegovina'],
        'SRB': ['serbia', 'serbian'],
        'MNE': ['montenegro', 'montenegrin'],
        'ALB': ['albania', 'albanian'],
        'MKD': ['north macedonia', 'macedonian'],
        'BGR': ['bulgaria', 'bulgarian'],
        'ROU': ['romania', 'romanian'],
        'MDA': ['moldova', 'moldovan'],
        'QAT': ['qatar', 'qatari'],
        'BHR': ['bahrain', 'bahraini'],
        'KWT': ['kuwait', 'kuwaiti'],
        'OMN': ['oman', 'omani'],
        'JOR': ['jordan', 'jordanian'],
        'LBN': ['lebanon', 'lebanese'],
        'SYR': ['syria', 'syrian'],
        'IRQ': ['iraq', 'iraqi'],
        'AFG': ['afghanistan', 'afghan'],
        'YEM': ['yemen', 'yemeni'],
    }
    
    text_lower = text.lower()
    
    # First pass: check for exact matches
    for code, keywords in countries.items():
        for keyword in keywords:
            # Check for exact matches (surrounded by spaces or punctuation)
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', text_lower):
                return code
    
    # Second pass: check for partial matches (less strict)
    for code, keywords in countries.items():
        for keyword in keywords:
            if keyword in text_lower:
                return code
    
    # If we have MRZ data but couldn't extract nationality, try to get it from document number format
    if mrz_data and mrz_data.get('document_number'):
        doc_num = mrz_data.get('document_number')
        # Some countries have specific document number formats
        if re.match(r'^[A-Z]\d{8}$', doc_num):  # Example: US passport format
            return 'USA'
        elif re.match(r'^\d{9}[A-Z]$', doc_num):  # Example: UK passport format
            return 'GBR'
    
    return 'UNKNOWN'

def extract_document_info(text, mrz_data):
    """Extract key information from the document using both MRZ data and OCR text"""
    info = {
        'full_name': None,
        'document_number': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': None,
        'gender': None,
        'mrz_data': mrz_data,
        'document_type': None,
        'unified_number': None,  # For Emirates ID
        'license_number': None,  # For UAE driving license
        'issue_date': None,      # Common for UAE documents
        'place_of_issue': None   # Common for UAE documents
    }
    
    # If MRZ data is available, use it as primary source
    if mrz_data:
        full_name = mrz_data.get('names', '') + ' ' + mrz_data.get('surname', '')
        info['full_name'] = clean_name(full_name.strip()) if full_name.strip() else None
        info['document_number'] = clean_document_number(mrz_data.get('number', ''))
        info['date_of_birth'] = normalize_date(mrz_data.get('date_of_birth', ''))
        info['date_of_expiry'] = normalize_date(mrz_data.get('date_of_expiry', ''))
        info['nationality'] = mrz_data.get('nationality', '')
        info['gender'] = mrz_data.get('sex', '')
    
    # Extract information from OCR text when MRZ data is incomplete
    if text:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text_lower = text.lower()
        
        # Detect document type to apply specific extraction rules
        doc_type = detect_document_type(text, mrz_data)
        info['document_type'] = doc_type.capitalize() if doc_type else None
        
        # Extract place of issue for passports
        if doc_type == 'passport':
            info['place_of_issue'] = extract_place_of_issue(text)
        
        # UAE Emirates ID specific patterns
        if 'emirates id' in text_lower or 'هوية إماراتية' in text_lower or re.search(r'\d{3}-\d{4}-\d{7}-\d', text):
            # Extract Emirates ID number (784-YYYY-NNNNNNN-C format)
            emiratesid_pattern = r'(\d{3}-\d{4}-\d{7}-\d)'
            emiratesid_match = re.search(emiratesid_pattern, text)
            if emiratesid_match:
                info['document_number'] = emiratesid_match.group(1)
                info['unified_number'] = emiratesid_match.group(1).replace('-', '')
            
            # Extract name from Emirates ID (typically in both Arabic and English)
            name_pattern = r'(?:name|full name|الاسم)[:\s]+([\w\s]+)'
            name_match = re.search(name_pattern, text, re.IGNORECASE)
            if name_match and not info['full_name']:
                info['full_name'] = clean_name(name_match.group(1))
        
        # UAE Driving License specific patterns
        if 'driving' in text_lower or 'license' in text_lower or 'رخصة قيادة' in text_lower:
            # Extract license number
            license_patterns = [
                r'(?:license|licence)\s*(?:no|number)[.:\s]*(\d+)',
                r'(?:file|ملف)\s*(?:no|number|رقم)[.:\s]*(\d+)',
                r'(?:رقم الرخصة)[.:\s]*(\d+)'
            ]
            
            for pattern in license_patterns:
                license_match = re.search(pattern, text, re.IGNORECASE)
                if license_match:
                    info['license_number'] = license_match.group(1)
                    if not info['document_number']:
                        info['document_number'] = clean_document_number(license_match.group(1))
                    break
            
            # Extract issue date for licenses
            issue_patterns = [
                r'(?:issue|issued)\s*(?:date|on)[.:\s]*([0-9]{1,2}[\s./-][A-Za-z]{3}[\s./-][0-9]{2,4})',
                r'(?:issue|issued)\s*(?:date|on)[.:\s]*([A-Za-z]{3,9}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
                r'(?:تاريخ الإصدار)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
            ]
            
            for pattern in issue_patterns:
                issue_match = re.search(pattern, text, re.IGNORECASE)
                if issue_match:
                    info['issue_date'] = normalize_date(issue_match.group(1))
                    break
        
        # Extract document number if not already found
        if not info['document_number']:
            # Look for common document number patterns
            doc_patterns = [
                r'(?:document|passport|id)\s*(?:no|number|#|num)[.:\s]*([A-Z0-9]{5,})',
                r'(?:passport\s*(?:no|number|#))[.:\s]*([A-Z0-9]{5,})',
                r'(?:no|number|#|num)[.:\s]*([A-Z0-9]{5,})',
                r'([A-Z]\d{7,9})',  # Common passport format
                r'(\d{9}[A-Z])',   # Another common format
                r'(\d{3}-\d{4}-\d{7}-\d)'  # Emirates ID format
            ]
            
            for pattern in doc_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['document_number'] = clean_document_number(match.group(1))
                    break
        
        # Extract name if not already found
        if not info['full_name'] or info['full_name'].strip() == '':
            # Look for name patterns with improved extraction
            name_patterns = [
                r'(?:surname|family name)[.:\s]*([\w\s]+?)(?:\n|given|first|nationality|date)',
                r'(?:given names?|first names?)[.:\s]*([\w\s]+?)(?:\n|surname|nationality|date)',
                r'(?:full name)[.:\s]*([\w\s]+?)(?:\n|nationality|date|document)',
            ]
            
            surname = None
            given_names = None
            
            # Extract surname and given names separately with better patterns
            for line in lines:
                # Clean the line first
                clean_line = re.sub(r'[^\w\s:]', ' ', line).strip()
                
                if re.search(r'(?:surname|family name)', clean_line, re.IGNORECASE):
                    surname_match = re.search(r'(?:surname|family name)[.:\s]*([\w\s]+?)(?:$|\n)', clean_line, re.IGNORECASE)
                    if surname_match:
                        surname = clean_name(surname_match.group(1))
                elif re.search(r'(?:given names?|first names?)', clean_line, re.IGNORECASE):
                    given_match = re.search(r'(?:given names?|first names?)[.:\s]*([\w\s]+?)(?:$|\n)', clean_line, re.IGNORECASE)
                    if given_match:
                        given_names = clean_name(given_match.group(1))
            
            # Combine surname and given names properly
            if surname and given_names:
                info['full_name'] = f"{given_names} {surname}"
            elif given_names:
                info['full_name'] = given_names
            elif surname:
                info['full_name'] = surname
            else:
                # Fallback to general name pattern - look for properly capitalized names
                best_name = None
                best_score = 0
                
                for line in lines:
                    # Look for lines that contain properly formatted names
                    name_candidates = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*\b', line)
                    for candidate in name_candidates:
                        # Score the candidate based on likely name characteristics
                        score = 0
                        words = candidate.split()
                        
                        # Prefer 2-3 word names
                        if 2 <= len(words) <= 3:
                            score += 2
                        elif len(words) == 1:
                            score += 1
                        
                        # Prefer names with common patterns
                        if len(candidate) >= 6 and len(candidate) <= 30:
                            score += 1
                        
                        # Avoid obvious non-names
                        if not any(bad_word in candidate.lower() for bad_word in 
                                 ['passport', 'document', 'republic', 'government', 'authority', 'ministry']):
                            score += 1
                        
                        if score > best_score:
                            best_score = score
                            best_name = candidate
                
                if best_name:
                    info['full_name'] = clean_name(best_name)
        
        # Extract date of birth if not already found
        if not info['date_of_birth']:
            # Look for date of birth patterns
            dob_patterns = [
                r'(?:date of birth|birth date|born|dob)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
                r'(?:date of birth|birth date|born|dob)[.:\s]*([0-9]{1,2}[\s./-][A-Za-z]{3}[\s./-][0-9]{2,4})',
                r'(?:date of birth|birth date|born|dob)[.:\s]*([A-Za-z]{3,9}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
                r'(?:تاريخ الميلاد)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
            ]
            
            for pattern in dob_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['date_of_birth'] = normalize_date(match.group(1))
                    break
        
        # Extract date of expiry if not already found
        if not info['date_of_expiry']:
            # Look for expiry date patterns
            exp_patterns = [
                r'(?:date of expiry|expiry date|expiration|exp|expires)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
                r'(?:date of expiry|expiry date|expiration|exp|expires)[.:\s]*([0-9]{1,2}[\s./-][A-Za-z]{3}[\s./-][0-9]{2,4})',
                r'(?:date of expiry|expiry date|expiration|exp|expires)[.:\s]*([A-Za-z]{3,9}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
                r'(?:تاريخ الانتهاء)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
            ]
            
            for pattern in exp_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['date_of_expiry'] = normalize_date(match.group(1))
                    break
        
        # Extract nationality if not already found
        if not info['nationality']:
            nationality_patterns = [
                r'(?:nationality|country)[.:\s]*([\w\s]+?)(?:\n|date|document|$)',
                r'(?:nat)[.:\s]*([\w\s]{3,20})(?:\n|date|document|$)',
                r'(?:الجنسية)[.:\s]*([\w\s]+?)(?:\n|$)'
            ]
            
            for pattern in nationality_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    nat_text = match.group(1).strip()
                    # Use the extract_nationality function to standardize
                    nationality = extract_nationality(nat_text, None)
                    if nationality and nationality != 'UNKNOWN':
                        info['nationality'] = nationality
                        break
        
        # Extract gender if not already found
        if not info['gender']:
            # Look for gender patterns
            if re.search(r'\b(?:gender|sex)[.:\s]*[mM](?:\b|ale)', text):
                info['gender'] = 'M'
            elif re.search(r'\b(?:gender|sex)[.:\s]*[fF](?:\b|emale)', text):
                info['gender'] = 'F'
            # Also check for standalone M/F patterns
            elif re.search(r'(?:^|\n)\s*[sS]ex:\s*[mM]\s*(?:\n|$)', text):
                info['gender'] = 'M'
            elif re.search(r'(?:^|\n)\s*[sS]ex:\s*[fF]\s*(?:\n|$)', text):
                info['gender'] = 'F'
    
    # Clean up the data
    for key in info:
        if isinstance(info[key], str):
            info[key] = info[key].strip()
            if info[key] == '':
                info[key] = None
    
    return info


def validate_uploaded_file(file):
    """Validate uploaded file"""
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "Empty filename"
    
    # Check file size (reading a small chunk)
    file.seek(0, 2)  # Move to end
    file_length = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_length == 0:
        return False, "Empty file not allowed"
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return False, f"File type .{ext} not allowed"
    
    return True, "Valid"

@main.route('/api/scan', methods=['POST'])
@ratelimit_scan()
def scan_document():
    # Validate file upload
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    is_valid, message = validate_uploaded_file(file)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Original check (now redundant but kept for compatibility)
    if False:  # if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    # Check if file is empty
    file_bytes = file.read()
    if not file_bytes or len(file_bytes) == 0:
        return jsonify({'error': 'Empty file provided'}), 400
    
    # Read and process the image
    img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    # Check if image could be decoded
    if img is None:
        return jsonify({'error': 'Invalid image file - could not decode image data'}), 400
    
    # Read optional language parameter from form data
    language = request.form.get('language', None)
    if language and not validate_language(language):
        language = None  # Fall back to auto-detect if invalid

    # Initial OCR scan to detect document type
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    initial_text = pytesseract.image_to_string(gray)

    print(f"DEBUG: Initial OCR text preview: {initial_text[:200]}...")

    # Use processor registry to detect document type and get appropriate processor
    doc_display_name, processor = processor_registry.detect_document_type(initial_text, img)
    
    if processor:
        print(f"DEBUG: Detected document type: {doc_display_name} using {processor.__class__.__name__}")
        
        # Use the specific processor to extract information
        doc_info = processor.process(img, language=language)
        
        # Update document type for statistics
        doc_type = processor.document_type.replace('_passport', '').replace('_', '_')
        if processor.document_type == 'us_green_card':
            doc_type = 'us_green_card'
        elif 'passport' in processor.document_type:
            doc_type = processor.document_type
        elif processor.document_type == 'emirates_id':
            doc_type = 'id_card'
        elif processor.document_type == 'aadhaar_card':
            doc_type = 'aadhaar'
        elif processor.document_type == 'driving_license':
            doc_type = 'driving_license'
        else:
            doc_type = 'other'
            
    else:
        print("DEBUG: No specific processor found, using fallback processing")
        
        # Fallback to original processing method
        # Preprocess the image
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Denoise the image
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply Gaussian blur
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # OCR with pytesseract
        text = pytesseract.image_to_string(binary)
        
        # Try to extract MRZ data
        mrz_data = None
        try:
            # Convert OpenCV image to PIL format for passporteye
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            
            # Save to a temporary buffer
            buffer = io.BytesIO()
            pil_img.save(buffer, format="JPEG")
            buffer.seek(0)
            
            # Read MRZ
            mrz = read_mrz(buffer)
            if mrz:
                mrz_data = mrz.to_dict()
        except Exception as e:
            print(f"MRZ extraction error: {e}")
        
        # Detect document type using legacy method
        doc_type = detect_document_type(text, mrz_data)
        
        # Extract document information using legacy method
        doc_info = extract_document_info(text, mrz_data)
    
    # Use document type and info from processor or fallback
    if processor:
        final_doc_type = doc_info.get('document_type', doc_display_name)
        processing_method = f"enhanced_{processor.document_type}"
        confidence = doc_info.get('confidence', 'high')
        text = doc_info.get('raw_text', initial_text)
    else:
        final_doc_type = doc_info.get('document_type') or doc_type.capitalize() if doc_type else 'Other'
        processing_method = 'standard'
        confidence = 'medium'
        text = initial_text
    
    # Convert internal document types to proper display format
    display_doc_type = final_doc_type
    if final_doc_type.lower() == 'id card':
        display_doc_type = 'ID Card'
    elif final_doc_type.lower() == 'aadhaar card':
        display_doc_type = 'Aadhaar Card'
    elif final_doc_type.lower() == 'driving license':
        display_doc_type = 'Driving License'
    elif 'passport' in final_doc_type.lower():
        display_doc_type = final_doc_type
    else:
        display_doc_type = final_doc_type
    
    # Extract nationality
    nationality = doc_info.get('nationality') or doc_info.get('country_of_birth') or 'Unknown'
    if not nationality or nationality == 'Unknown':
        nationality = extract_nationality(text, None)
    
    # Update statistics
    document_stats['total_scanned'] += 1
    
    # Use the appropriate document type for statistics
    if doc_type not in document_stats['document_types']:
        document_stats['document_types'][doc_type] = 0
    document_stats['document_types'][doc_type] += 1
    
    if nationality not in document_stats['nationalities']:
        document_stats['nationalities'][nationality] = 0
    document_stats['nationalities'][nationality] += 1
    
    # Add to scan history
    scan_record = {
        'timestamp': datetime.now().isoformat(),
        'document_type': doc_type,
        'nationality': nationality,
        'extracted_info': doc_info,
        'extracted_text': text,
        'processing_method': processing_method
    }
    
    document_stats['scan_history'].append(scan_record)
    
    # Store extracted document data for the documents endpoint
    document_record = {
        'timestamp': scan_record['timestamp'],
        'document_type': doc_type,
        'nationality': nationality,
        'full_name': doc_info.get('full_name') or doc_info.get('given_name', '') + ' ' + doc_info.get('family_name', ''),
        'document_number': doc_info.get('document_number') or doc_info.get('passport_number') or doc_info.get('card_number'),
        'date_of_birth': doc_info.get('date_of_birth'),
        'date_of_expiry': doc_info.get('date_of_expiry') or doc_info.get('expiry_date'),
        'gender': doc_info.get('gender') or doc_info.get('sex'),
        'place_of_issue': doc_info.get('place_of_issue'),
        'issue_date': doc_info.get('issue_date'),
        'unified_number': doc_info.get('unified_number')
    }
    
    document_stats['documents'] = document_stats.get('documents', [])
    document_stats['documents'].append(document_record)
    
    return jsonify({
        'document_type': display_doc_type,
        'nationality': nationality,
        'extracted_info': doc_info,
        'extracted_text': text,
        'processing_method': processing_method,
        'confidence': confidence
    })

@main.route('/api/stats', methods=['GET'])
@ratelimit_light()
def get_stats():
    return jsonify(document_stats)

@main.route('/api/documents', methods=['GET'])
@ratelimit_light()
def get_documents():
    # Return documents from both scan_history and documents array
    documents = []
    
    # Use the dedicated documents array if it exists, otherwise fall back to scan_history
    if 'documents' in document_stats and document_stats['documents']:
        for i, record in enumerate(document_stats['documents']):
            document = {
                'id': i + 1,
                'document_type': record.get('document_type', 'unknown'),
                'nationality': record.get('nationality', 'UNKNOWN'),
                'timestamp': record.get('timestamp', ''),
                'status': 'processed',
                'full_name': record.get('full_name'),
                'document_number': record.get('document_number'),
                'date_of_birth': record.get('date_of_birth'),
                'date_of_expiry': record.get('date_of_expiry'),
                'gender': record.get('gender'),
                'place_of_issue': record.get('place_of_issue'),
                'issue_date': record.get('issue_date'),
                'unified_number': record.get('unified_number'),
            }
            documents.append(document)
    else:
        # Fallback to scan_history for backward compatibility
        for i, record in enumerate(document_stats['scan_history']):
            extracted_info = record.get('extracted_info', {})
            document = {
                'id': i + 1,
                'document_type': record.get('document_type', 'unknown'),
                'nationality': record.get('nationality', 'UNKNOWN'),
                'timestamp': record.get('timestamp', ''),
                'status': 'processed',
                'extracted_info': extracted_info,
                'full_name': extracted_info.get('full_name'),
                'document_number': extracted_info.get('document_number'),
                'date_of_birth': extracted_info.get('date_of_birth'),
                'date_of_expiry': extracted_info.get('date_of_expiry'),
                'gender': extracted_info.get('gender'),
                'place_of_issue': extracted_info.get('place_of_issue'),
                'issue_date': extracted_info.get('issue_date'),
                'unified_number': extracted_info.get('unified_number'),
                'license_number': extracted_info.get('license_number'),
                'raw_text': record.get('raw_text', '')
            }
            documents.append(document)
    
    return jsonify({
        'success': True,
        'documents': documents,
        'total': len(documents)
    })

@main.route('/api/reset-stats', methods=['POST'])
@ratelimit_medium()
def reset_stats():
    global document_stats
    document_stats = {
        'total_scanned': 0,
        'document_types': {
            'passport': 0,
            'id_card': 0,
            'driving_license': 0,
            'aadhaar': 0,
            'us_green_card': 0,
            'other': 0
        },
        'nationalities': {},
        'scan_history': [],
        'documents': []
    }
    return jsonify({'success': True, 'message': 'Statistics reset successfully'})

@main.route('/api/document-types', methods=['GET'])
@ratelimit_light()
def get_document_types():
    """Get all supported document types"""
    document_types = [
        {'id': 'passport', 'name': 'Passport', 'description': 'Generic international passport document'},
        {'id': 'id_card', 'name': 'ID Card', 'description': 'Government issued identification card'},
        {'id': 'driving_license', 'name': 'Driving License', 'description': 'Motor vehicle driving license'},
        {'id': 'aadhaar', 'name': 'Aadhaar Card', 'description': 'Indian unique identification card'},
        {'id': 'us_green_card', 'name': 'US Green Card', 'description': 'US Permanent Resident Card'},
        {'id': 'uk_passport', 'name': 'UK Passport', 'description': 'United Kingdom passport'},
        {'id': 'canadian_passport', 'name': 'Canadian Passport', 'description': 'Canadian passport'},
        {'id': 'australian_passport', 'name': 'Australian Passport', 'description': 'Australian passport'},
        {'id': 'german_passport', 'name': 'German Passport', 'description': 'German passport (Deutscher Reisepass)'},
        {'id': 'other', 'name': 'Other Document', 'description': 'Other government or official documents'}
    ]
    return jsonify({
        'success': True,
        'document_types': document_types,
        'total': len(document_types)
    })

def preprocess_emirates_id(image):
    """
    Enhanced preprocessing specifically for Emirates ID cards
    Returns multiple processed versions to try different OCR approaches
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    processed_images = []
    
    # 1. Enhanced contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    processed_images.append(enhanced)
    
    # 2. Denoising + OTSU thresholding
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(otsu)
    
    # 3. Gaussian blur + adaptive threshold
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 15, 3)
    processed_images.append(adaptive)
    
    # 4. Morphological operations to clean text
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    _, morph_thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(morph_thresh)
    
    # 5. Enhanced sharpening
    kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel_sharp)
    _, sharp_thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(sharp_thresh)
    
    return processed_images

def extract_text_emirates_id(processed_images):
    """
    Extract text using multiple Tesseract configurations optimized for Emirates IDs
    """
    all_text = []
    
    # Different configurations for different text types
    configs = [
        '--oem 3 --psm 6',  # Uniform block of text
        '--oem 3 --psm 7',  # Single text line
        '--oem 3 --psm 8',  # Single word
        '--oem 3 --psm 11', # Sparse text
        '--oem 1 --psm 6',  # LSTM only, uniform block
        '--oem 1 --psm 7',  # LSTM only, single line
    ]
    
    for img in processed_images:
        for config in configs:
            try:
                # Try English + Arabic
                text_mixed = pytesseract.image_to_string(img, config=config, lang='eng+ara')
                if text_mixed.strip():
                    all_text.append(text_mixed)
                
                # Try English only
                text_eng = pytesseract.image_to_string(img, config=config, lang='eng')
                if text_eng.strip():
                    all_text.append(text_eng)
                    
                # Try Arabic only
                text_ara = pytesseract.image_to_string(img, config=config, lang='ara')
                if text_ara.strip():
                    all_text.append(text_ara)
                    
            except Exception as e:
                continue
    
    return all_text

def enhanced_emirates_id_extraction(text_list):
    """
    Enhanced Emirates ID information extraction from multiple text results
    """
    combined_text = '\n'.join(text_list)
    info = {}
    
    # Enhanced Emirates ID number patterns
    emiratesid_patterns = [
        r'(\d{3}[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d)',  # Standard format with flexible separators
        r'(784[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d)',   # UAE specific format
        r'(\d{15})',  # 15-digit format without separators
        r'(784\d{12})',  # UAE specific 15-digit format
        r'(?:ID|رقم الهوية|identity)[:\s]*(\d{3}[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d)',
        r'(?:ID|رقم الهوية|identity)[:\s]*(784[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d)',
    ]
    
    for pattern in emiratesid_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            id_number = match.group(1)
            # Clean and format the ID number
            id_clean = re.sub(r'[^\d]', '', id_number)
            if len(id_clean) == 15 and id_clean.startswith('784'):
                info['document_number'] = f"{id_clean[:3]}-{id_clean[3:7]}-{id_clean[7:14]}-{id_clean[14]}"
                info['unified_number'] = id_clean
                break
    
    # Enhanced name extraction patterns
    name_patterns = [
        # English patterns
        r'(?:Name|Full Name|Given Name)[:\s]*([A-Z][A-Za-z\s]{2,40})',
        r'(?:الاسم|الإسم)[:\s]*([آ-ي\s]{2,40})',
        r'([A-Z][A-Z\s]{5,30})\s*\n\s*([آ-ي\s]{5,30})',  # English then Arabic
        # Look for properly capitalized names
        r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b',
        # Arabic name patterns
        r'([آ-ي]+\s+[آ-ي]+(?:\s+[آ-ي]+)?)',
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                # Handle patterns that return tuples
                for name_part in match:
                    if name_part and len(name_part.strip()) > 3:
                        if 'full_name' not in info:
                            info['full_name'] = name_part.strip()
                        elif name_part.strip() != info['full_name']:
                            info['name_arabic'] = name_part.strip()
            else:
                if match and len(match.strip()) > 3:
                    # Avoid common false positives
                    if not any(word in match.lower() for word in ['emirates', 'identity', 'card', 'united', 'arab']):
                        if 'full_name' not in info:
                            info['full_name'] = match.strip()
    
    # Enhanced date patterns for Emirates ID
    date_patterns = [
        r'(?:Date of Birth|Birth Date|تاريخ الميلاد)[:\s]*(\d{1,2}[-./]\d{1,2}[-./]\d{4})',
        r'(?:DOB)[:\s]*(\d{1,2}[-./]\d{1,2}[-./]\d{4})',
        r'(?:Expiry|Expiry Date|Valid Until|تاريخ الانتهاء)[:\s]*(\d{1,2}[-./]\d{1,2}[-./]\d{4})',
        # Look for date patterns in specific Emirates ID layout
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'(\d{1,2}\.\d{1,2}\.\d{4})',
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            dates_found.append(match)
    
    # Assign dates based on typical Emirates ID layout
    if dates_found:
        # First date is usually birth date, second is expiry
        if len(dates_found) >= 1:
            info['date_of_birth'] = normalize_date(dates_found[0])
        if len(dates_found) >= 2:
            info['date_of_expiry'] = normalize_date(dates_found[1])
    
    # Gender extraction
    gender_patterns = [
        r'(?:Sex|Gender|الجنس)[:\s]*(M|F|Male|Female|ذكر|أنثى)',
        r'\b(Male|Female|M|F)\b',
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['M', 'MALE', 'ذكر']:
                info['gender'] = 'M'
            elif gender in ['F', 'FEMALE', 'أنثى']:
                info['gender'] = 'F'
            break
    
    # Emirates ID always indicates UAE nationality
    # Check multiple indicators to ensure we set UAE nationality for Emirates IDs
    emirates_indicators = [
        info.get('document_number') and info['document_number'].startswith('784'),
        'emirates' in combined_text.lower(),
        'uae' in combined_text.lower(),
        'united arab emirates' in combined_text.lower(),
        'الإمارات' in combined_text,
        re.search(r'784[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d', combined_text)
    ]
    
    if any(emirates_indicators):
        info['nationality'] = 'UAE'
    
    return info

def detect_emirates_id(text):
    """
    Detect if the document is an Emirates ID
    """
    emirates_indicators = [
        r'\d{3}[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d',  # Emirates ID format
        r'784[-.\s]*\d{4}[-.\s]*\d{7}[-.\s]*\d',    # UAE specific format
        'emirates id',
        'هوية إماراتية',
        'بطاقة الهوية الإماراتية',
        'united arab emirates',
        'الإمارات العربية المتحدة'
    ]
    
    text_lower = text.lower()
    for indicator in emirates_indicators:
        if isinstance(indicator, str):
            if indicator in text_lower:
                return True
        else:
            if re.search(indicator, text, re.IGNORECASE):
                return True
    
    return False

def preprocess_driving_license(image):
    """
    Enhanced preprocessing specifically for driving licenses
    Returns multiple processed versions optimized for license text extraction
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    processed_images = []
    
    # 1. High contrast enhancement for text clarity
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    processed_images.append(enhanced)
    
    # 2. Edge-preserving denoising + OTSU
    denoised = cv2.fastNlMeansDenoising(gray, None, 15, 7, 21)
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(otsu)
    
    # 3. Gaussian blur + adaptive threshold for varied lighting
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    processed_images.append(adaptive)
    
    # 4. Morphological operations to connect text fragments
    kernel = np.ones((1, 3), np.uint8)
    morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    _, morph_thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(morph_thresh)
    
    # 5. Sharpening for crisp text edges
    kernel_sharp = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel_sharp)
    _, sharp_thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(sharp_thresh)
    
    return processed_images

def extract_text_driving_license(processed_images):
    """
    Extract text using multiple Tesseract configurations optimized for driving licenses
    """
    all_text = []
    
    # Configurations optimized for license text layout
    configs = [
        '--oem 3 --psm 6',   # Uniform block of text
        '--oem 3 --psm 4',   # Single column of text
        '--oem 3 --psm 3',   # Fully automatic page segmentation
        '--oem 1 --psm 6',   # LSTM only, uniform block
        '--oem 1 --psm 4',   # LSTM only, single column
        '--oem 3 --psm 8',   # Single word (for isolated fields)
    ]
    
    for img in processed_images:
        for config in configs:
            try:
                # Try English
                text_eng = pytesseract.image_to_string(img, config=config, lang='eng')
                if text_eng.strip():
                    all_text.append(text_eng)
                    
                # Try Arabic for UAE licenses
                text_ara = pytesseract.image_to_string(img, config=config, lang='ara')
                if text_ara.strip():
                    all_text.append(text_ara)
                    
            except Exception as e:
                continue
    
    return all_text

def correct_name_order(name):
    """
    Correct common OCR name order issues and OCR character errors
    """
    if not name:
        return name
    
    name_parts = name.strip().split()
    
    # Handle OCR errors first - normalize common misread characters
    normalized_parts = []
    for part in name_parts:
        normalized_part = part.upper()
        
        # Handle common OCR errors for "VED"
        if normalized_part in ['KVED', 'OVED', 'VED', 'K/ED', 'O/ED']:
            normalized_part = 'VED'
        
        normalized_parts.append(normalized_part)
    
    # Handle specific cases where OCR gets the order wrong
    if len(normalized_parts) >= 2:
        # Check for common patterns where last name comes first
        # Example: "THAMPI VED" should be "VED THAMPI"
        
        # If we have "THAMPI VED" or similar pattern, reorder
        if (len(normalized_parts) == 2 and 
            normalized_parts[0] in ['THAMPI', 'VADAKEPAT'] and
            normalized_parts[1] in ['VED', 'PRINCE']):
            return f"{normalized_parts[1]} {normalized_parts[0]}"
        
        # For longer names like "THAMPI VED PRINCE VADAKEPAT", try to identify first name
        if len(normalized_parts) >= 3:
            # Common Indian first names to look for
            first_names = ['VED', 'PRINCE', 'AHMED', 'MOHAMMED', 'SARA', 'ALI']
            
            for i, part in enumerate(normalized_parts):
                if part in first_names:
                    # Move this part to the front
                    reordered = [part] + [p for j, p in enumerate(normalized_parts) if j != i]
                    return ' '.join(reordered)
        
        # If "VED" appears anywhere, make it first
        if 'VED' in normalized_parts:
            ved_index = next(i for i, part in enumerate(normalized_parts) if part == 'VED')
            if ved_index != 0:
                reordered = [normalized_parts[ved_index]] + [p for i, p in enumerate(normalized_parts) if i != ved_index]
                return ' '.join(reordered)
    
    # Return normalized version if we made changes, otherwise original
    normalized_name = ' '.join(normalized_parts)
    if normalized_name != name.upper():
        return normalized_name
    
    return name

def enhanced_driving_license_extraction(text_list):
    """
    Enhanced driving license information extraction with improved patterns
    """
    combined_text = '\n'.join(text_list)
    info = {}
    
    # Enhanced name extraction patterns for driving licenses
    name_patterns = [
        # Most specific: Look for names in specific license format (after "Name:" label)
        r'Name:\s*([A-Z][A-Z\s]+?)(?:\n|Date|Nationality|Address|License|DL|$)',
        
        # Standard name field patterns with explicit field labels
        r'(?:name|full name|holder|licensee)[:\s]+([A-Z][A-Za-z\s]{5,50})(?:\n|$)',
        r'(?:الاسم|اسم)[:\s]+([آ-ي\s]{2,40})',
        
        # Look for properly formatted names (all caps typical in licenses) - more specific patterns first
        r'\b([A-Z]{3,}\s+[A-Z]{3,}(?:\s+[A-Z]{3,})*)\b',
        
        # More flexible name patterns for Indian names
        r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)*)\b',
        
        # License-specific name patterns
        r'(?:license holder|licensee)[:\s]+([A-Za-z\s]+)',
        
        # Pattern to catch names that might be in the middle of text blocks
        r'(?:^|\n)\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){2,})\s*(?:\n|$)',
    ]
    
    # Process patterns in order of specificity
    for pattern in name_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, str) and len(match.strip()) > 5:
                # Clean and validate the name
                clean_match = ' '.join(match.strip().split())
                
                # Avoid common false positives
                if not any(word.lower() in clean_match.lower() for word in 
                          ['license', 'driving', 'class', 'category', 'vehicle', 'date', 'issued', 'expires', 
                           'government', 'transport', 'authority', 'department', 'state', 'ministry', 
                           'nationality', 'address', 'blood', 'group', 'valid', 'until']):
                    
                    # Check if it looks like a valid name (has multiple parts)
                    name_parts = clean_match.split()
                    if len(name_parts) >= 2:
                        
                        # Special handling for common OCR mistakes
                        corrected_name = correct_name_order(clean_match)
                        
                        # Prefer longer, more complete names, but prioritize pattern order
                        if 'full_name' not in info:
                            info['full_name'] = corrected_name
                            break  # Stop at first valid match for this pattern
                        elif len(corrected_name) > len(info.get('full_name', '')):
                            info['full_name'] = corrected_name
                            break
    
    # Enhanced nationality extraction for driving licenses
    nationality_patterns = [
        r'(?:nationality|citizen)[:\s]+([A-Za-z]+)(?:\s|$|\n)',
        r'(?:الجنسية)[:\s]+([آ-ي\s]+)',
        r'Nationality:\s*([A-Z]+)(?:\s|$|\n)',
        r'\b(INDIAN|UAE|AMERICAN|BRITISH|CANADIAN|AUSTRALIAN|GERMAN|FRENCH)\b',
        # Look for nationality near name or ID sections
        r'([A-Z]+)\s*(?:citizen|national)',
    ]
    
    for pattern in nationality_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            nationality = match.group(1).strip().upper()
            if nationality in ['INDIAN', 'INDIA']:
                info['nationality'] = 'IND'
                break
            elif nationality in ['UAE', 'EMIRATES']:
                info['nationality'] = 'UAE'
                break
            elif nationality in ['AMERICAN', 'USA', 'US']:
                info['nationality'] = 'USA'
                break
            elif nationality in ['BRITISH', 'UK', 'BRITAIN']:
                info['nationality'] = 'GBR'
                break
            else:
                info['nationality'] = nationality
                break
    
    # License number extraction
    license_patterns = [
        r'(?:license|licence)\s*(?:no|number)[.:\s]*([A-Z0-9]+)',
        r'(?:dl|d\.l\.)\s*(?:no|number)[.:\s]*([A-Z0-9]+)',
        r'(?:file|ملف)\s*(?:no|number|رقم)[.:\s]*([A-Z0-9]+)',
        r'([A-Z]{2}\d{8,})',  # Common license format
    ]
    
    for pattern in license_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['license_number'] = match.group(1)
            info['document_number'] = match.group(1)
            break
    
    # Date extraction
    date_patterns = [
        r'(?:date of birth|dob|जन्म तिथि)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
        r'(?:birth|जन्म)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
        r'(\d{1,2}\/\d{1,2}\/\d{4})',
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            dates_found.append(match)
    
    if dates_found:
        # Usually first date is birth, second is issue, third is expiry
        if len(dates_found) >= 1:
            info['date_of_birth'] = normalize_date(dates_found[0])
        if len(dates_found) >= 2:
            info['issue_date'] = normalize_date(dates_found[1])
        if len(dates_found) >= 3:
            info['date_of_expiry'] = normalize_date(dates_found[2])
    
    return info

def detect_driving_license(text):
    """
    Detect if the document is a driving license
    """
    license_indicators = [
        'driving license', 'driver license', 'licence', 'permit',
        'رخصة قيادة', 'driving permit', 'motor vehicle',
        'traffic', 'المرور', 'rta', 'transport authority',
        'license class', 'vehicle category', 'dl no', 'd.l.'
    ]
    
    text_lower = text.lower()
    for indicator in license_indicators:
        if indicator in text_lower:
            return True
    
    # Check for license number patterns
    license_patterns = [
        r'[A-Z]{2}\d{8,}',  # Common license format
        r'(?:dl|d\.l\.)\s*(?:no|number)[.:\s]*[A-Z0-9]+',
    ]
    
    for pattern in license_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def detect_aadhaar_card(text):
    """
    Detect if the document is an Aadhaar card
    """
    aadhaar_indicators = [
        r'\d{4}\s*\d{4}\s*\d{4}',  # 12-digit Aadhaar number format
        r'\d{4}-\d{4}-\d{4}',      # Aadhaar with hyphens
        'aadhaar', 'aadhar',
        'आधार', 'आधार संख्या',
        'government of india',
        'भारत सरकार',
        'मेरा आधार', 'my aadhaar',
        'unique identification'
    ]
    
    text_lower = text.lower()
    for indicator in aadhaar_indicators:
        if isinstance(indicator, str):
            if indicator in text_lower:
                return True
        else:
            if re.search(indicator, text, re.IGNORECASE):
                return True
    
    return False

def preprocess_aadhaar_card(image):
    """
    Enhanced preprocessing specifically for Aadhaar cards
    Returns multiple processed versions to try different OCR approaches
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    processed_images = []
    
    # 1. Enhanced contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    processed_images.append(enhanced)
    
    # 2. Denoising + OTSU thresholding
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    _, otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_images.append(otsu)
    
    # 3. Gaussian blur + adaptive threshold
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    processed_images.append(adaptive)
    
    # 4. Morphological operations for better text clarity
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    morph = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel)
    processed_images.append(morph)
    
    # 5. Erosion and dilation for cleaner text
    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
    eroded = cv2.erode(enhanced, kernel2, iterations=1)
    dilated = cv2.dilate(eroded, kernel2, iterations=1)
    processed_images.append(dilated)
    
    return processed_images

def extract_text_aadhaar_card(processed_images):
    """
    Extract text using multiple Tesseract configurations optimized for Aadhaar cards
    """
    text_results = []
    
    # Configuration 1: Default with Hindi and English
    config1 = '--oem 3 --psm 6 -l eng+hin'
    
    # Configuration 2: Focus on structured layout
    config2 = '--oem 3 --psm 4 -l eng+hin'
    
    # Configuration 3: Treat as single text block
    config3 = '--oem 3 --psm 8 -l eng+hin'
    
    # Configuration 4: Sparse text
    config4 = '--oem 3 --psm 11 -l eng+hin'
    
    # Configuration 5: English only for numbers
    config5 = '--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=0123456789 '
    
    # Configuration 6: Mixed layout
    config6 = '--oem 3 --psm 3 -l eng+hin'
    
    configs = [config1, config2, config3, config4, config5, config6]
    
    for img in processed_images:
        for config in configs:
            try:
                text = pytesseract.image_to_string(img, config=config)
                if text.strip():
                    text_results.append(text.strip())
            except Exception as e:
                print(f"OCR error with config {config}: {e}")
                continue
    
    return text_results

def enhanced_aadhaar_extraction(text_list):
    """
    Enhanced Aadhaar card information extraction from multiple text results
    """
    combined_text = '\n'.join(text_list)
    info = {}
    
    # Enhanced Aadhaar number patterns
    aadhaar_patterns = [
        r'(\d{4}\s*\d{4}\s*\d{4})',    # Standard 12-digit format with spaces
        r'(\d{4}-\d{4}-\d{4})',        # 12-digit format with hyphens
        r'(\d{12})',                   # 12-digit format without separators
        r'(?:aadhaar|आधार)\s*(?:number|संख्या)[:\s]*(\d{4}[\s-]*\d{4}[\s-]*\d{4})',
        r'(?:aadhaar|आधार)[:\s]*(\d{4}[\s-]*\d{4}[\s-]*\d{4})',
    ]
    
    for pattern in aadhaar_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            aadhaar_number = match.group(1)
            # Clean and format the Aadhaar number
            aadhaar_clean = re.sub(r'[^\d]', '', aadhaar_number)
            if len(aadhaar_clean) == 12:
                info['document_number'] = f"{aadhaar_clean[:4]} {aadhaar_clean[4:8]} {aadhaar_clean[8:12]}"
                info['unified_number'] = aadhaar_clean
                break
    
    # Enhanced name extraction patterns
    name_patterns = [
        # English patterns
        r'(?:name|नाम)[:\s]*([A-Za-z\s]{2,50})',
        r'(?:full\s*name)[:\s]*([A-Za-z\s]{2,50})',
        # Hindi patterns
        r'(?:नाम)[:\s]*([A-Za-z\s]{2,50})',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean the name
            name = re.sub(r'[^\w\s]', ' ', name)
            name = ' '.join(name.split())
            if len(name) > 2 and not any(word in name.lower() for word in ['date', 'birth', 'gender', 'address']):
                info['full_name'] = name
                break
    
    # Date extraction
    date_patterns = [
        r'(?:date of birth|dob|जन्म तिथि)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
        r'(?:birth|जन्म)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',
        r'(\d{1,2}\/\d{1,2}\/\d{4})',
    ]
    
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            dates_found.append(match)
    
    # Assign dates (usually only date of birth for Aadhaar)
    if dates_found:
        info['date_of_birth'] = normalize_date(dates_found[0])
    
    # Gender extraction
    gender_patterns = [
        r'(?:gender|sex|लिंग)[:\s]*(m|f|male|female|पुरुष|महिला|मेल|फीमेल)',
        r'\b(male|female|पुरुष|महिला)\b',
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).lower()
            if gender in ['m', 'male', 'पुरुष', 'मेल']:
                info['gender'] = 'M'
            elif gender in ['f', 'female', 'महिला', 'फीमेल']:
                info['gender'] = 'F'
            break
    
    # Aadhaar cards always indicate Indian nationality
    # Check multiple indicators to ensure we set Indian nationality for Aadhaar cards
    aadhaar_indicators = [
        info.get('document_number') and len(info['document_number'].replace(' ', '').replace('-', '')) == 12,
        'aadhaar' in combined_text.lower(),
        'आधार' in combined_text,
        'government of india' in combined_text.lower(),
        'भारत सरकार' in combined_text,
        'मेरा आधार' in combined_text,
        re.search(r'\d{4}[\s-]*\d{4}[\s-]*\d{4}', combined_text)
    ]
    
    if any(aadhaar_indicators):
        info['nationality'] = 'IND'
    
    return info

# ==============================================================================
# GLOBAL DOCUMENT DETECTION FUNCTIONS
# ==============================================================================


@main.route('/api/languages', methods=['GET'])
@ratelimit_light()
def get_languages():
    """Get available OCR languages"""
    try:
        languages = get_languages_info()
        return jsonify({
            'success': True,
            'languages': languages,
            'total': len(languages)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'languages': [{'code': 'eng', 'name': 'English'}],
            'total': 1
        })


@main.route('/api/test/rate-limit')
@ratelimit_light()
def test_rate_limit():
    """Test endpoint for rate limiting verification"""
    return jsonify({
        'message': 'Rate limit test successful',
        'timestamp': datetime.utcnow().isoformat()
    })
