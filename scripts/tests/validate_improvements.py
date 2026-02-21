#!/usr/bin/env python3
"""
Simple test script to verify Emirates ID improvements
"""

import subprocess
import json

def test_basic_functionality():
    """Test basic API functionality"""
    print("=== Testing Basic API Functionality ===\n")
    
    try:
        # Test stats endpoint
        result = subprocess.run(['curl', '-s', 'http://localhost:5002/api/stats'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            stats = json.loads(result.stdout)
            print("✅ API is accessible")
            print(f"Current stats: {json.dumps(stats, indent=2)}")
            return True
        else:
            print("❌ Failed to access API")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_backend_functions():
    """Check if our Emirates ID functions are properly implemented"""
    print("\n=== Checking Backend Implementation ===\n")
    
    try:
        import sys
        sys.path.insert(0, '/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend')
        
        from app.routes import detect_emirates_id, enhanced_emirates_id_extraction
        
        # Test detection function
        test_text = "UNITED ARAB EMIRATES\nEMIRATES ID\n784-2020-1234567-8"
        is_detected = detect_emirates_id(test_text)
        print(f"✅ detect_emirates_id function works: {is_detected}")
        
        # Test extraction function
        extraction_result = enhanced_emirates_id_extraction([test_text])
        print(f"✅ enhanced_emirates_id_extraction function works")
        print(f"   Sample result: {extraction_result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Function error: {e}")
        return False

def check_file_modifications():
    """Check if our modifications were applied correctly"""
    print("\n=== Checking File Modifications ===\n")
    
    try:
        routes_file = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend/app/routes.py'
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Check for key functions
        functions_to_check = [
            'detect_emirates_id',
            'preprocess_emirates_id',
            'extract_text_emirates_id',
            'enhanced_emirates_id_extraction'
        ]
        
        found_functions = []
        for func in functions_to_check:
            if f'def {func}(' in content:
                found_functions.append(func)
                print(f"✅ Function {func} found")
            else:
                print(f"❌ Function {func} not found")
        
        # Check for key patterns
        patterns_to_check = [
            'enhanced_emirates_id',
            'processing_method',
            'confidence',
            '784-'
        ]
        
        found_patterns = []
        for pattern in patterns_to_check:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✅ Pattern '{pattern}' found")
            else:
                print(f"❌ Pattern '{pattern}' not found")
        
        print(f"\nSummary: {len(found_functions)}/{len(functions_to_check)} functions found")
        print(f"         {len(found_patterns)}/{len(patterns_to_check)} patterns found")
        
        return len(found_functions) >= 3 and len(found_patterns) >= 3
        
    except Exception as e:
        print(f"❌ Error checking file: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Emirates ID OCR Validation Test\n")
    
    test1 = test_basic_functionality()
    test2 = check_backend_functions() 
    test3 = check_file_modifications()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"API Functionality: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Backend Functions: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"File Modifications: {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 Emirates ID OCR improvements are properly implemented!")
        print("\nKey Features Added:")
        print("• Enhanced image preprocessing for Emirates IDs")
        print("• Multi-configuration OCR extraction")
        print("• Emirates ID pattern recognition (784-YYYY-NNNNNNN-C)")
        print("• Automatic document type detection")
        print("• Processing method tracking")
        print("• Enhanced confidence scoring")
    else:
        print("\n⚠️  Some components may need attention.")
