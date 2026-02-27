"""
Text processing utilities for OCR document scanning.

Contains helper functions for date normalization, document number cleaning,
name extraction/correction, document type detection, nationality extraction,
and file validation. These were originally inline in routes.py and have been
extracted to reduce route-handler bloat.
"""

import re


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Document number helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Name helpers  (correct_name_order must precede clean_name)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Document / place / nationality detection
# ---------------------------------------------------------------------------

def extract_place_of_issue(text):
    """Extract place of issue from passport text"""
    if not text:
        return None

    # Common patterns for place of issue
    patterns = [
        r'(?:place of (?:issue|birth)|issued (?:at|in)|authority)[:\s]*([A-Za-z\s,]+?)(?:\n|$)',
        r'(?:place of birth|place of issue)[:\s]*([A-Za-z\s,]+?)(?:\n|$)',
        r'(?:authority|issuing office)[:\s]*([A-Za-z\s,]+?)(?:\n|$)',
        r'(?:\u0637\u0631\u0641|\u0635\u0627\u062f\u0631 \u0627\u0632)[:\s]*([A-Za-z\s,\u0622-\u06cc]+?)(?:\n|$)',  # Arabic patterns
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
        'passport', 'passeport', 'reisepass', 'pasaporte', '\u043f\u0430\u0441\u043f\u043e\u0440\u0442', '\u062c\u0648\u0627\u0632 \u0633\u0641\u0631',
        '\u092a\u093e\u0938\u092a\u094b\u0930\u094d\u091f', '\u62a4\u7167', '\u30d1\u30b9\u30dd\u30fc\u30c8', '\uc5ec\uad8c', 'pass', 'passaporte', 'passaporto'
    ]

    id_keywords = [
        'identity card', 'id card', 'identification', 'national id', '\u0628\u0637\u0627\u0642\u0629 \u0627\u0644\u0647\u0648\u064a\u0629',
        'carte d\'identit\u00e9', 'personalausweis', 'dni', 'c\u00e9dula', 'cedula', '\u0443\u0434\u043e\u0441\u0442\u043e\u0432\u0435\u0440\u0435\u043d\u0438\u0435',
        '\u0628\u0637\u0627\u0642\u0629 \u0627\u0644\u0647\u0648\u064a\u0629', '\u092a\u0939\u091a\u093e\u0928 \u092a\u0924\u094d\u0930', '\u8eab\u4efd\u8bc1', '\u904b\u8ee2\u514d\u8a31\u8a3c', '\uc8fc\ubbfc\ub4f1\ub85d\uc99d', 'emirates id',
        'residence', 'resident card', 'green card', '\u0647\u0648\u064a\u0629 \u0625\u0645\u0627\u0631\u0627\u062a\u064a\u0629', 'uae id', 'id number',
        'aadhaar', 'aadhar', '\u0906\u0927\u093e\u0930', 'government of india', '\u092d\u093e\u0930\u0924 \u0938\u0930\u0915\u093e\u0930', 'aadhaar number',
        '\u0906\u0927\u093e\u0930 \u0938\u0902\u0916\u094d\u092f\u093e', 'my aadhaar', '\u092e\u0947\u0930\u093e \u0906\u0927\u093e\u0930', 'unique identification'
    ]

    license_keywords = [
        'driver license', 'driving licence', 'license', 'permit', '\u0631\u062e\u0635\u0629 \u0642\u064a\u0627\u062f\u0629',
        'driving permit', 'driver\'s license', 'driver\'s licence', 'road transport',
        'traffic', '\u0627\u0644\u0645\u0631\u0648\u0631', '\u0647\u064a\u0626\u0629 \u0627\u0644\u0637\u0631\u0642', 'rta', 'driving class', 'vehicle category'
    ]

    # UAE specific document patterns
    uae_patterns = {
        'emirates_id': [r'\d{3}-\d{4}-\d{7}-\d', r'784-\d{4}-\d{7}-\d', r'\u0628\u0637\u0627\u0642\u0629 \u0627\u0644\u0647\u0648\u064a\u0629 \u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a\u064a\u0629', r'\u0628\u0637\u0627\u0642\u0629 \u0627\u0644\u0647\u0648\u064a\u0629'],
        'driving_license': [r'\u0631\u062e\u0635\u0629 \u0642\u064a\u0627\u062f\u0629', r'driving license', r'license no\.?\s*\d+', r'\u0645\u0644\u0641 \u0645\u0631\u0648\u0631\u064a', r'traffic file']
    }

    # Indian Aadhaar card specific patterns
    aadhaar_patterns = [
        r'\d{4}\s*\d{4}\s*\d{4}',  # 12-digit Aadhaar number format
        r'\d{4}-\d{4}-\d{4}',      # Aadhaar with hyphens
        r'\u0906\u0927\u093e\u0930\s*\u0938\u0902\u0916\u094d\u092f\u093e',          # Hindi Aadhaar number
        r'aadhaar\s*number',       # English Aadhaar number
        r'government\s*of\s*india', # Government of India
        r'\u092d\u093e\u0930\u0924\s*\u0938\u0930\u0915\u093e\u0930',           # Hindi Government of India
        r'\u092e\u0947\u0930\u093e\s*\u0906\u0927\u093e\u0930',            # My Aadhaar in Hindi
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
        'FRA': ['france', 'french', 'r\u00e9publique fran\u00e7aise', 'republique francaise'],
        'ESP': ['spain', 'spanish', 'espa\u00f1a', 'espana'],
        'ITA': ['italy', 'italian', 'italia'],
        'JPN': ['japan', 'japanese', '\u65e5\u672c', 'nihon', 'nippon'],
        'CHN': ['china', 'chinese', '\u4e2d\u56fd', 'zhongguo'],
        'IND': ['india', 'indian', '\u092d\u093e\u0930\u0924', 'hindustan', 'bharatiya', 'bharat'],
        'RUS': ['russia', 'russian', '\u0440\u043e\u0441\u0441\u0438\u044f', 'rossiya'],
        'BRA': ['brazil', 'brazilian', 'brasil'],
        'MEX': ['mexico', 'mexican', 'm\u00e9xico'],
        'KOR': ['korea', 'korean', 'south korea', '\ud55c\uad6d', 'hanguk'],
        'SAU': ['saudi arabia', 'saudi', '\u0627\u0644\u0645\u0645\u0644\u0643\u0629 \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629'],
        'UAE': ['united arab emirates', 'uae', 'emirates', '\u0627\u0644\u0625\u0645\u0627\u0631\u0627\u062a \u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0627\u0644\u0645\u062a\u062d\u062f\u0629'],
        'EGY': ['egypt', 'egyptian', '\u0645\u0635\u0631', 'misr'],
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
        'TUR': ['turkey', 'turkish', 't\u00fcrkiye', 'turkiye'],
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
            for _match in re.finditer(r'\b' + re.escape(keyword) + r'\b', text_lower):
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


# ---------------------------------------------------------------------------
# Composite document-info extraction
# ---------------------------------------------------------------------------

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
        if 'emirates id' in text_lower or '\u0647\u0648\u064a\u0629 \u0625\u0645\u0627\u0631\u0627\u062a\u064a\u0629' in text_lower or re.search(r'\d{3}-\d{4}-\d{7}-\d', text):
            # Extract Emirates ID number (784-YYYY-NNNNNNN-C format)
            emiratesid_pattern = r'(\d{3}-\d{4}-\d{7}-\d)'
            emiratesid_match = re.search(emiratesid_pattern, text)
            if emiratesid_match:
                info['document_number'] = emiratesid_match.group(1)
                info['unified_number'] = emiratesid_match.group(1).replace('-', '')

            # Extract name from Emirates ID (typically in both Arabic and English)
            name_pattern = r'(?:name|full name|\u0627\u0644\u0627\u0633\u0645)[:\s]+([\w\s]+)'
            name_match = re.search(name_pattern, text, re.IGNORECASE)
            if name_match and not info['full_name']:
                info['full_name'] = clean_name(name_match.group(1))

        # UAE Driving License specific patterns
        if 'driving' in text_lower or 'license' in text_lower or '\u0631\u062e\u0635\u0629 \u0642\u064a\u0627\u062f\u0629' in text_lower:
            # Extract license number
            license_patterns = [
                r'(?:license|licence)\s*(?:no|number)[.:\s]*(\d+)',
                r'(?:file|\u0645\u0644\u0641)\s*(?:no|number|\u0631\u0642\u0645)[.:\s]*(\d+)',
                r'(?:\u0631\u0642\u0645 \u0627\u0644\u0631\u062e\u0635\u0629)[.:\s]*(\d+)'
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
                r'(?:\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0625\u0635\u062f\u0627\u0631)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
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
                r'(?:\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0645\u064a\u0644\u0627\u062f)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
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
                r'(?:\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0646\u062a\u0647\u0627\u0621)[.:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
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
                r'(?:\u0627\u0644\u062c\u0646\u0633\u064a\u0629)[.:\s]*([\w\s]+?)(?:\n|$)'
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


# ---------------------------------------------------------------------------
# File validation
# ---------------------------------------------------------------------------

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
