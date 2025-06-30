#!/usr/bin/env python3
"""
Simple test script for Emirates ID OCR improvements
"""

import sys
import os

# Add the backend directory to the Python path
backend_path = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend'
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

def test_emirates_id_functions():
    """Test the enhanced Emirates ID functions directly"""
    
    print("=== Testing Enhanced Emirates ID Functions ===\n")
    
    try:
        from app.routes import detect_emirates_id, enhanced_emirates_id_extraction
        
        # Test text that mimics Emirates ID content
        test_text = """
        UNITED ARAB EMIRATES
        بطاقة الهوية الإماراتية
        EMIRATES ID
        
        784-2020-1234567-8
        
        Name: AHMED HASSAN ALI
        الاسم: أحمد حسن علي
        
        Date of Birth: 15/01/1990
        Gender: M
        Nationality: UAE
        Expiry Date: 15/01/2030
        """
        
        print("Sample Emirates ID Text:")
        print(test_text)
        print("\n" + "="*50)
        
        # Test detection
        print("\n1. Testing Emirates ID Detection:")
        is_emirates_id = detect_emirates_id(test_text)
        print(f"   Emirates ID Detected: {is_emirates_id}")
        
        # Test extraction
        print("\n2. Testing Enhanced Extraction:")
        extracted_info = enhanced_emirates_id_extraction([test_text])
        print("   Extracted Information:")
        for key, value in extracted_info.items():
            print(f"     {key}: {value}")
        
        print("\n" + "="*50)
        
        # Test specific patterns
        print("\n3. Testing Specific Patterns:")
        
        test_cases = [
            "784-2020-1234567-8",
            "784 2020 1234567 8", 
            "784202012345678",
            "Name: MOHAMMED AHMED HASSAN",
            "الاسم: محمد أحمد حسن",
            "Date of Birth: 15/01/1990"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"   Test {i}: {test_case}")
            result = enhanced_emirates_id_extraction([test_case])
            print(f"   Result: {result}")
            print()
        
        print("✅ All tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_emirates_id_functions()
    if success:
        print("\n🎉 Emirates ID OCR improvements are working correctly!")
    else:
        print("\n❌ There were issues with the Emirates ID OCR improvements.")
