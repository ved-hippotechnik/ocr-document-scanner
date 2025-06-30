#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend')

from app.routes import extract_document_info, normalize_date, clean_document_number, clean_name, extract_place_of_issue

def test_ocr_improvements():
    """Test the improved OCR extraction functions"""
    
    # Sample passport text
    with open('/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-images/sample_passport_text.txt', 'r') as f:
        sample_text = f.read()
    
    print("=== Testing OCR Improvements ===\n")
    print("Sample Text:")
    print(sample_text)
    print("\n" + "="*50 + "\n")
    
    # Test individual functions
    print("Testing normalize_date function:")
    test_dates = [
        "15 JAN 1985",
        "01 JUN 2020", 
        "01/06/2030",
        "15-01-1985",
        "2020.06.01",
        "20200601"
    ]
    
    for date in test_dates:
        normalized = normalize_date(date)
        print(f"  {date} -> {normalized}")
    
    print("\nTesting clean_document_number function:")
    test_doc_nums = [
        "AB1234567",
        "Passport No: AB1234567",
        "Document Number AB1234567",
        "AB1234567USA"
    ]
    
    for doc_num in test_doc_nums:
        cleaned = clean_document_number(doc_num)
        print(f"  '{doc_num}' -> '{cleaned}'")
    
    print("\nTesting clean_name function:")
    test_names = [
        "SMITH",
        "JOHN MICHAEL",
        "Name: JOHN MICHAEL SMITH",
        "mr john smith"
    ]
    
    for name in test_names:
        cleaned = clean_name(name)
        print(f"  '{name}' -> '{cleaned}'")
    
    print("\nTesting extract_place_of_issue function:")
    place = extract_place_of_issue(sample_text)
    print(f"  Extracted place: '{place}'")
    
    print("\n" + "="*50 + "\n")
    print("Testing complete document extraction:")
    
    # Mock MRZ data (simulating what passporteye would return)
    mock_mrz_data = {
        'names': 'JOHN MICHAEL',
        'surname': 'SMITH',
        'number': 'AB1234567',
        'date_of_birth': '850115',
        'date_of_expiry': '300601',
        'nationality': 'USA',
        'sex': 'M',
        'document_type': 'P'
    }
    
    # Test with both MRZ and OCR text
    extracted_info = extract_document_info(sample_text, mock_mrz_data)
    
    print("Extracted Information:")
    for key, value in extracted_info.items():
        if key != 'mrz_data':  # Skip printing raw MRZ data
            print(f"  {key}: {value}")
    
    print("\n" + "="*50 + "\n")
    print("Testing OCR-only extraction (no MRZ data):")
    
    # Test with only OCR text (no MRZ)
    extracted_info_ocr_only = extract_document_info(sample_text, None)
    
    print("Extracted Information (OCR only):")
    for key, value in extracted_info_ocr_only.items():
        if key != 'mrz_data':
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_ocr_improvements()
