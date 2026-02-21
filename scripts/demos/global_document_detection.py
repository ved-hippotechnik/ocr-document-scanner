# Auto-generated global document detection functions
import re


def detect_emirates_id(text):
    """Detect Emirates ID from United Arab Emirates"""
    text_lower = text.lower()
    
    # United Arab Emirates Emirates ID patterns
    keywords = ['emirates id', 'بطاقة الهوية', 'federal authority']
    number_patterns = ['784-\\d{4}-\\d{7}-\\d']
    text_indicators = ['uae', 'united arab emirates', 'الإمارات']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_aadhaar_card(text):
    """Detect Aadhaar Card from India"""
    text_lower = text.lower()
    
    # India Aadhaar Card patterns
    keywords = ['aadhaar', 'आधार', 'government of india', 'भारत सरकार']
    number_patterns = ['\\d{4}\\s*\\d{4}\\s*\\d{4}']
    text_indicators = ['india', 'भारत', 'unique identification']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_drivers_license(text):
    """Detect Driver's License from United States"""
    text_lower = text.lower()
    
    # United States Driver's License patterns
    keywords = ['driver license', 'drivers license', 'dl', 'motor vehicle']
    number_patterns = ['[A-Z0-9]{8,15}', '[A-Z]\\d{7,12}']
    text_indicators = ['united states', 'state of', 'department of motor vehicles']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_state_id(text):
    """Detect State ID from United States"""
    text_lower = text.lower()
    
    # United States State ID patterns
    keywords = ['identification card', 'state id', 'identity card']
    number_patterns = ['[A-Z0-9]{8,15}']
    text_indicators = ['state of', 'identification', 'not a driver license']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_driving_licence(text):
    """Detect UK Driving Licence from United Kingdom"""
    text_lower = text.lower()
    
    # United Kingdom UK Driving Licence patterns
    keywords = ['driving licence', 'dvla', 'driver and vehicle licensing agency']
    number_patterns = ['[A-Z]{5}\\d{6}[A-Z]{2}\\d[A-Z]{2}']
    text_indicators = ['united kingdom', 'great britain', 'driving licence']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_drivers_license(text):
    """Detect Driver's License from Canada"""
    text_lower = text.lower()
    
    # Canada Driver's License patterns
    keywords = ["driver's license", 'permis de conduire', 'licence']
    number_patterns = ['[A-Z0-9]{8,15}']
    text_indicators = ['canada', 'province', 'ontario', 'quebec', 'british columbia']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_drivers_license(text):
    """Detect Driver Licence from Australia"""
    text_lower = text.lower()
    
    # Australia Driver Licence patterns
    keywords = ['driver licence', 'drivers licence', 'transport']
    number_patterns = ['\\d{8,10}', '[A-Z]\\d{7,9}']
    text_indicators = ['australia', 'new south wales', 'victoria', 'queensland']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_personalausweis(text):
    """Detect Personalausweis from Germany"""
    text_lower = text.lower()
    
    # Germany Personalausweis patterns
    keywords = ['personalausweis', 'bundesrepublik deutschland', 'ausweis']
    number_patterns = ['[A-Z]\\d{8}', '\\d{9}[A-Z]']
    text_indicators = ['deutschland', 'germany', 'bundesrepublik']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_fuhrerschein(text):
    """Detect Führerschein from Germany"""
    text_lower = text.lower()
    
    # Germany Führerschein patterns
    keywords = ['führerschein', 'fahrerlaubnis', 'driving licence']
    number_patterns = ['\\d{11}']
    text_indicators = ['deutschland', 'führerschein', 'klasse']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_carte_identite(text):
    """Detect Carte d'identité from France"""
    text_lower = text.lower()
    
    # France Carte d'identité patterns
    keywords = ["carte d'identité", 'république française', 'identité']
    number_patterns = ['\\d{12}']
    text_indicators = ['france', 'république française', 'carte nationale']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_dni(text):
    """Detect DNI from Spain"""
    text_lower = text.lower()
    
    # Spain DNI patterns
    keywords = ['documento nacional de identidad', 'dni', 'españa']
    number_patterns = ['\\d{8}[A-Z]']
    text_indicators = ['españa', 'spain', 'reino de españa']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_carta_identita(text):
    """Detect Carta d'identità from Italy"""
    text_lower = text.lower()
    
    # Italy Carta d'identità patterns
    keywords = ["carta d'identità", 'repubblica italiana', 'comune']
    number_patterns = ['[A-Z]{2}\\d{7}']
    text_indicators = ['italia', 'italy', 'repubblica italiana']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_identiteitskaart(text):
    """Detect Nederlandse identiteitskaart from Netherlands"""
    text_lower = text.lower()
    
    # Netherlands Nederlandse identiteitskaart patterns
    keywords = ['identiteitskaart', 'nederland', 'koninkrijk']
    number_patterns = ['[A-Z]{2}[A-Z0-9]{6}']
    text_indicators = ['nederland', 'netherlands', 'koninkrijk']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_mynumber_card(text):
    """Detect My Number Card from Japan"""
    text_lower = text.lower()
    
    # Japan My Number Card patterns
    keywords = ['個人番号カード', 'my number', 'マイナンバー']
    number_patterns = ['\\d{4}\\s\\d{4}\\s\\d{4}']
    text_indicators = ['japan', '日本', '個人番号']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_resident_card(text):
    """Detect Resident Registration Card from South Korea"""
    text_lower = text.lower()
    
    # South Korea Resident Registration Card patterns
    keywords = ['주민등록증', 'resident registration', '대한민국']
    number_patterns = ['\\d{6}-\\d{7}']
    text_indicators = ['korea', '대한민국', '주민등록']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_nric(text):
    """Detect NRIC from Singapore"""
    text_lower = text.lower()
    
    # Singapore NRIC patterns
    keywords = ['nric', 'national registration identity card', 'singapore']
    number_patterns = ['[STFG]\\d{7}[A-Z]']
    text_indicators = ['singapore', 'republic of singapore']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_mykad(text):
    """Detect MyKad from Malaysia"""
    text_lower = text.lower()
    
    # Malaysia MyKad patterns
    keywords = ['mykad', 'malaysia', 'kad pengenalan']
    number_patterns = ['\\d{6}-\\d{2}-\\d{4}']
    text_indicators = ['malaysia', 'kad pengenalan']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_thai_id(text):
    """Detect Thai National ID Card from Thailand"""
    text_lower = text.lower()
    
    # Thailand Thai National ID Card patterns
    keywords = ['บัตรประชาชน', 'national id card', 'thailand']
    number_patterns = ['\\d{1}-\\d{4}-\\d{5}-\\d{2}-\\d{1}']
    text_indicators = ['thailand', 'ประเทศไทย', 'บัตรประชาชน']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_rg(text):
    """Detect RG from Brazil"""
    text_lower = text.lower()
    
    # Brazil RG patterns
    keywords = ['registro geral', 'rg', 'república federativa do brasil']
    number_patterns = ['\\d{1,2}\\.\\d{3}\\.\\d{3}-\\d{1}']
    text_indicators = ['brasil', 'brazil', 'república federativa']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_ine(text):
    """Detect INE from Mexico"""
    text_lower = text.lower()
    
    # Mexico INE patterns
    keywords = ['instituto nacional electoral', 'ine', 'méxico']
    number_patterns = ['\\d{13}']
    text_indicators = ['méxico', 'mexico', 'estados unidos mexicanos']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_dni(text):
    """Detect DNI from Argentina"""
    text_lower = text.lower()
    
    # Argentina DNI patterns
    keywords = ['documento nacional de identidad', 'república argentina']
    number_patterns = ['\\d{7,8}']
    text_indicators = ['argentina', 'república argentina']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_green_id(text):
    """Detect Green ID Book from South Africa"""
    text_lower = text.lower()
    
    # South Africa Green ID Book patterns
    keywords = ['identity document', 'south africa', 'republic']
    number_patterns = ['\\d{13}']
    text_indicators = ['south africa', 'republic of south africa']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_nin(text):
    """Detect National Identification Number from Nigeria"""
    text_lower = text.lower()
    
    # Nigeria National Identification Number patterns
    keywords = ['national identification number', 'nin', 'nigeria']
    number_patterns = ['\\d{11}']
    text_indicators = ['nigeria', 'federal republic of nigeria']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2


def detect_national_id(text):
    """Detect National ID Card from Egypt"""
    text_lower = text.lower()
    
    # Egypt National ID Card patterns
    keywords = ['بطاقة الرقم القومي', 'national id', 'egypt', 'مصر']
    number_patterns = ['\\d{14}']
    text_indicators = ['egypt', 'مصر', 'جمهورية مصر العربية']
    
    # Check for keywords
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    
    # Check for number patterns
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    
    # Check for text indicators
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    # Score-based detection (require at least 2 matches)
    total_score = keyword_matches + number_matches + indicator_matches
    
    return total_score >= 2

