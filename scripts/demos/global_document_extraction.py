# Auto-generated global document extraction functions
import re
from datetime import datetime


def normalize_date(date_str):
    """Normalize date format"""
    # Add date normalization logic
    return date_str.strip()


def enhanced_emirates_id_extraction(text_results):
    """Extract specific information from United Arab Emirates Emirates ID"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'ARE',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['784-\\d{4}-\\d{7}-\\d']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_aadhaar_card_extraction(text_results):
    """Extract specific information from India Aadhaar Card"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'IND',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{4}\\s*\\d{4}\\s*\\d{4}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_drivers_license_extraction(text_results):
    """Extract specific information from United States Driver's License"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'USA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z0-9]{8,15}', '[A-Z]\\d{7,12}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_state_id_extraction(text_results):
    """Extract specific information from United States State ID"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'USA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z0-9]{8,15}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_driving_licence_extraction(text_results):
    """Extract specific information from United Kingdom UK Driving Licence"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'GBR',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z]{5}\\d{6}[A-Z]{2}\\d[A-Z]{2}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_drivers_license_extraction(text_results):
    """Extract specific information from Canada Driver's License"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'CAN',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z0-9]{8,15}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_drivers_license_extraction(text_results):
    """Extract specific information from Australia Driver Licence"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'AUS',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{8,10}', '[A-Z]\\d{7,9}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_personalausweis_extraction(text_results):
    """Extract specific information from Germany Personalausweis"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'DEU',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z]\\d{8}', '\\d{9}[A-Z]']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_fuhrerschein_extraction(text_results):
    """Extract specific information from Germany Führerschein"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'DEU',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{11}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_carte_identite_extraction(text_results):
    """Extract specific information from France Carte d'identité"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'FRA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{12}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_dni_extraction(text_results):
    """Extract specific information from Spain DNI"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'ESP',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{8}[A-Z]']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_carta_identita_extraction(text_results):
    """Extract specific information from Italy Carta d'identità"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'ITA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z]{2}\\d{7}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_identiteitskaart_extraction(text_results):
    """Extract specific information from Netherlands Nederlandse identiteitskaart"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'NLD',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[A-Z]{2}[A-Z0-9]{6}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_mynumber_card_extraction(text_results):
    """Extract specific information from Japan My Number Card"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'JPN',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{4}\\s\\d{4}\\s\\d{4}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_resident_card_extraction(text_results):
    """Extract specific information from South Korea Resident Registration Card"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'KOR',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{6}-\\d{7}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_nric_extraction(text_results):
    """Extract specific information from Singapore NRIC"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'SGP',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['[STFG]\\d{7}[A-Z]']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_mykad_extraction(text_results):
    """Extract specific information from Malaysia MyKad"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'MYS',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{6}-\\d{2}-\\d{4}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_thai_id_extraction(text_results):
    """Extract specific information from Thailand Thai National ID Card"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'THA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{1}-\\d{4}-\\d{5}-\\d{2}-\\d{1}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_rg_extraction(text_results):
    """Extract specific information from Brazil RG"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'BRA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{1,2}\\.\\d{3}\\.\\d{3}-\\d{1}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_ine_extraction(text_results):
    """Extract specific information from Mexico INE"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'MEX',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{13}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_dni_extraction(text_results):
    """Extract specific information from Argentina DNI"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'ARG',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{7,8}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_green_id_extraction(text_results):
    """Extract specific information from South Africa Green ID Book"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'ZAF',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{13}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_nin_extraction(text_results):
    """Extract specific information from Nigeria National Identification Number"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'NGA',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{11}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info


def enhanced_national_id_extraction(text_results):
    """Extract specific information from Egypt National ID Card"""
    info = {
        'document_number': None,
        'full_name': None,
        'date_of_birth': None,
        'date_of_expiry': None,
        'nationality': 'EGY',
        'gender': None
    }
    
    combined_text = '\n'.join(text_results)
    
    # Extract document number using patterns
    number_patterns = ['\\d{14}']
    for pattern in number_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            info['document_number'] = match.group(0).strip()
            break
    
    # Extract name (basic pattern)
    name_patterns = [
        r'name[:\s]+([A-Za-z\s]+?)\n',
        r'nom[:\s]+([A-Za-z\s]+?)\n',
        r'nombre[:\s]+([A-Za-z\s]+?)\n'
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2 and name.replace(' ', '').isalpha():
                info['full_name'] = name
                break
    
    # Extract date of birth
    dob_patterns = [
        r'(?:birth|born|naissance|nacimiento)[:\s]*([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})',
        r'([0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4})'
    ]
    
    for pattern in dob_patterns:
        matches = re.findall(pattern, combined_text, re.IGNORECASE)
        for match in matches:
            if re.match(r'[0-9]{1,2}[\s./-][0-9]{1,2}[\s./-][0-9]{2,4}', match):
                info['date_of_birth'] = normalize_date(match)
                break
    
    # Extract gender
    gender_patterns = [
        r'(?:gender|sex|sexe)[:\s]*(male|female|m|f|homme|femme|masculino|femenino)',
        r'\b(male|female|m|f)\b'
    ]
    
    for pattern in gender_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            gender = match.group(1).upper()
            if gender in ['MALE', 'M', 'HOMME', 'MASCULINO']:
                info['gender'] = 'M'
            elif gender in ['FEMALE', 'F', 'FEMME', 'FEMENINO']:
                info['gender'] = 'F'
            break
    
    return info

