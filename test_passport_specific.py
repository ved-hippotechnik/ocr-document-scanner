#!/usr/bin/env python3
"""
Test the name correction with actual passport OCR text
"""
import sys
import os

# Add the backend directory to the path
sys.path.append('/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend')

def test_passport_name_extraction():
    """Test name extraction from passport OCR text"""
    print("🧪 Testing Passport Name Extraction")
    print("=" * 50)
    
    from app.routes import extract_document_info, correct_name_order
    
    # Simulate the OCR text that would be extracted from the passport image
    passport_ocr_text = """
    REPUBLIC OF INDIA
    Type/प्रकार: P
    Country Code/देश कोड: IND
    Passport No./पासपोर्ट नं.: T6779059
    Surname/उपनाम: THAMPI
    Given Name(s)/दिया गया नाम: VED
    Nationality/राष्ट्रीयता: भारतीय/INDIAN
    Sex/लिंग: M
    Date of Birth/जन्म तिथि: 05/09/2000
    Place of Birth/जन्म स्थान: MUSCAT, OMAN
    Place of Issue/जारी करने का स्थान: DUBAI
    Date of Issue/जारी करने की तिथि: 19/05/2019
    Date of Expiry/समाप्ति की तिथि: 18/05/2029
    P<INDTHAMPI<<VED<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    T6779059<6IND0009058M2905187<<<<<<<<<<<<<<<2
    """
    
    print("Input OCR text contains:")
    print("- Surname: THAMPI")
    print("- Given Name(s): VED")
    print("- MRZ: P<INDTHAMPI<<VED<<<<...")
    print()
    
    # Create mock MRZ data as it would be extracted
    mrz_data = {
        'surname': 'THAMPI',
        'names': 'VED',
        'nationality': 'IND',
        'number': 'T6779059',
        'date_of_birth': '2000-09-05',
        'date_of_expiry': '2029-05-18',
        'sex': 'M'
    }
    
    # Test the extraction
    print("🔍 Testing extract_document_info...")
    doc_info = extract_document_info(passport_ocr_text, mrz_data)
    
    print("Extracted Information:")
    for key, value in doc_info.items():
        if value:
            print(f"  {key}: {value}")
    
    full_name = doc_info.get('full_name', 'NOT FOUND')
    print(f"\n📋 Final Full Name: '{full_name}'")
    
    # Test name correction specifically
    print(f"\n🔧 Testing name correction...")
    
    test_names = [
        "THAMPI VED",      # From OCR surname + given name
        "VED THAMPI",      # Correct order
        "Thampi Kved",     # OCR error version
    ]
    
    for test_name in test_names:
        corrected = correct_name_order(test_name)
        print(f"  '{test_name}' → '{corrected}'")
    
    # Check if the issue is in the extraction order
    print(f"\n🔍 Checking MRZ name construction...")
    if mrz_data:
        mrz_full_name = mrz_data.get('names', '') + ' ' + mrz_data.get('surname', '')
        print(f"  MRZ construction: '{mrz_full_name.strip()}'")
        
        # This is likely the issue - MRZ gives us "VED THAMPI" but 
        # the extract_document_info might be reversing it
        
def test_mrz_extraction():
    """Test how MRZ data is being processed"""
    print(f"\n" + "=" * 50)
    print("🔍 Testing MRZ Processing")
    print("=" * 50)
    
    from app.routes import extract_document_info
    
    # Test with different MRZ name orders
    test_cases = [
        {
            'description': 'Standard MRZ (names first, surname second)',
            'mrz_data': {
                'surname': 'THAMPI',
                'names': 'VED',
                'nationality': 'IND'
            }
        },
        {
            'description': 'Reversed MRZ (what if OCR reads it wrong)',
            'mrz_data': {
                'surname': 'VED', 
                'names': 'THAMPI',
                'nationality': 'IND'
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['description']}:")
        print(f"  Input: surname='{case['mrz_data']['surname']}', names='{case['mrz_data']['names']}'")
        
        doc_info = extract_document_info("", case['mrz_data'])
        full_name = doc_info.get('full_name', 'NOT FOUND')
        print(f"  Result: '{full_name}'")

if __name__ == "__main__":
    test_passport_name_extraction()
    test_mrz_extraction()
