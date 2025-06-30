#!/usr/bin/env python3
"""
Test script to verify name correction functionality
"""
import sys
import os

# Add the backend directory to the path
sys.path.append('/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend')

from app.routes import correct_name_order, enhanced_driving_license_extraction

def test_name_corrections():
    """Test various name correction scenarios"""
    
    print("🧪 Testing Name Correction Logic...")
    print("=" * 50)
    
    test_cases = [
        # Original case that was working
        "VED THAMPI PRINCE VADAKEPAT THAMPI",
        
        # Problematic cases mentioned
        "THAMPI VED",
        "Thampi Kved",  # OCR error case
        "THAMPI KVED",  # OCR error case uppercase
        "Kved Thampi",  # Reverse order
        "VADAKEPAT PRINCE",
        
        # Edge cases
        "VED",  # Single name
        "PRINCE VADAKEPAT THAMPI VED",  # VED at end
        "THAMPI VED PRINCE",  # VED in middle
        
        # Other common Indian names
        "MOHAMMED AHMED",
        "AHMED MOHAMMED",
        "SARA ALI",
        "ALI SARA",
    ]
    
    for i, test_name in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_name}'")
        result = correct_name_order(test_name)
        print(f"   Result: '{result}'")
        
        if test_name != result:
            print(f"   ✅ Corrected")
        else:
            print(f"   ➡️  No change needed")

def test_ocr_extraction():
    """Test the full OCR extraction with problematic text"""
    
    print("\n\n🔍 Testing OCR Extraction with Problematic Text...")
    print("=" * 60)
    
    # Simulate OCR text that might contain the problematic name
    test_texts = [
        """
        GOVERNMENT OF INDIA
        DRIVING LICENCE
        Name: THAMPI VED
        Nationality: INDIAN
        DL No: KA123456
        """,
        
        """
        GOVERNMENT OF INDIA
        DRIVING LICENCE
        Name: Thampi Kved
        Nationality: INDIAN  
        DL No: KA123456
        """,
        
        """
        GOVERNMENT OF INDIA
        DRIVING LICENCE
        Name: KVED THAMPI
        Nationality: INDIAN
        DL No: KA123456
        """
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Testing OCR text:")
        print(f"   Input: {text.strip()}")
        
        result = enhanced_driving_license_extraction([text])
        extracted_name = result.get('full_name', 'NOT FOUND')
        
        print(f"   Extracted Name: '{extracted_name}'")

if __name__ == "__main__":
    test_name_corrections()
    test_ocr_extraction()
    print("\n✅ Name correction tests completed!")
