# Global document detection functions for integration with routes.py

def detect_drivers_license_usa(text):
    """Detect Driver's License from United States"""
    text_lower = text.lower()
    
    keywords = ['driver license', 'drivers license', 'dl', 'motor vehicle', 'dmv']
    number_patterns = [r'[A-Z0-9]{8,15}', r'[A-Z]\d{7,12}']
    text_indicators = ['united states', 'state of', 'department of motor vehicles']
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    total_score = keyword_matches + number_matches + indicator_matches
    return total_score >= 2

def detect_state_id_usa(text):
    """Detect State ID from United States"""
    text_lower = text.lower()
    
    keywords = ['identification card', 'state id', 'identity card', 'id card']
    number_patterns = [r'[A-Z0-9]{8,15}']
    text_indicators = ['state of', 'identification', 'not a driver license']
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    total_score = keyword_matches + number_matches + indicator_matches
    return total_score >= 2

def detect_driving_licence_uk(text):
    """Detect UK Driving Licence from United Kingdom"""
    text_lower = text.lower()
    
    keywords = ['driving licence', 'dvla', 'driver and vehicle licensing agency']
    number_patterns = [r'[A-Z]{5}\d{6}[A-Z]{2}\d[A-Z]{2}']
    text_indicators = ['united kingdom', 'great britain', 'driving licence']
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    total_score = keyword_matches + number_matches + indicator_matches
    return total_score >= 2

def detect_nric_singapore(text):
    """Detect NRIC from Singapore"""
    text_lower = text.lower()
    
    keywords = ['nric', 'national registration identity card', 'singapore']
    number_patterns = [r'[STFG]\d{7}[A-Z]']
    text_indicators = ['singapore', 'republic of singapore']
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    total_score = keyword_matches + number_matches + indicator_matches
    return total_score >= 2

def detect_mynumber_card_japan(text):
    """Detect My Number Card from Japan"""
    text_lower = text.lower()
    
    keywords = ['my number', 'mynumber', 'individual number card']
    number_patterns = [r'\d{4}\s\d{4}\s\d{4}']
    text_indicators = ['japan', 'individual number']
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    total_score = keyword_matches + number_matches + indicator_matches
    return total_score >= 2

def detect_personalausweis_germany(text):
    """Detect Personalausweis from Germany"""
    text_lower = text.lower()
    
    keywords = ['personalausweis', 'bundesrepublik deutschland', 'ausweis']
    number_patterns = [r'[A-Z]\d{8}', r'\d{9}[A-Z]']
    text_indicators = ['deutschland', 'germany', 'bundesrepublik']
    
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    number_matches = sum(1 for pattern in number_patterns 
                        if re.search(pattern, text, re.IGNORECASE))
    indicator_matches = sum(1 for indicator in text_indicators 
                          if indicator.lower() in text_lower)
    
    total_score = keyword_matches + number_matches + indicator_matches
    return total_score >= 2

# Country-to-nationality mapping
COUNTRY_NATIONALITY_MAPPING = {
    'emirates_id': 'UAE',
    'aadhaar_card': 'IND',
    'drivers_license_usa': 'USA',
    'state_id_usa': 'USA',
    'driving_licence_uk': 'GBR',
    'nric_singapore': 'SGP',
    'mynumber_card_japan': 'JPN',
    'personalausweis_germany': 'DEU'
}

# Global document detection functions list
GLOBAL_DETECTION_FUNCTIONS = [
    ('drivers_license_usa', detect_drivers_license_usa),
    ('state_id_usa', detect_state_id_usa),
    ('driving_licence_uk', detect_driving_licence_uk),
    ('nric_singapore', detect_nric_singapore),
    ('mynumber_card_japan', detect_mynumber_card_japan),
    ('personalausweis_germany', detect_personalausweis_germany)
]

def detect_global_document_type(text):
    """Detect document type using global detection functions"""
    # First check existing functions (UAE, India, general driving license)
    if detect_aadhaar_card(text):
        return 'aadhaar_card'
    elif detect_emirates_id(text):
        return 'emirates_id'
    elif detect_driving_license(text):
        return 'driving_license'
    
    # Then check global functions
    for doc_type, detect_func in GLOBAL_DETECTION_FUNCTIONS:
        if detect_func(text):
            return doc_type
    
    return None
