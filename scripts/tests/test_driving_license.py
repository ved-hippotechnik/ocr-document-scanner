#!/usr/bin/env python3
"""
Test script for driving license OCR improvements
"""

import requests
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_sample_driving_license_image():
    """Create a sample driving license image for testing"""
    
    # Create a sample image with driving license content
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback if not available
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        title_font = font = small_font = ImageFont.load_default()
    
    # Draw driving license header
    draw.text((50, 30), "GOVERNMENT OF INDIA", fill='#000080', font=title_font)
    draw.text((50, 60), "DRIVING LICENCE", fill='#8B0000', font=title_font)
    draw.text((50, 90), "Ministry of Road Transport & Highways", fill='black', font=small_font)
    
    # License number
    draw.text((50, 130), "DL No: KA20210123456", fill='black', font=font)
    
    # Personal information
    draw.text((50, 170), "Name: VED THAMPI PRINCE VADAKEPAT THAMPI", fill='black', font=font)
    draw.text((50, 200), "Date of Birth: 15/01/1990", fill='black', font=font)
    draw.text((50, 230), "Nationality: INDIAN", fill='black', font=font)
    draw.text((50, 260), "Address: 123 Sample Street, Bangalore", fill='black', font=small_font)
    draw.text((50, 290), "Issue Date: 01/06/2021", fill='black', font=font)
    draw.text((50, 320), "Valid Until: 01/06/2041", fill='black', font=font)
    draw.text((50, 350), "License Class: LMV", fill='black', font=font)
    
    # Save the image
    img_path = '/tmp/sample_driving_license.png'
    img.save(img_path, 'PNG')
    
    return img_path

def test_driving_license_api():
    """Test the driving license OCR via API"""
    
    print("=== Testing Driving License OCR API ===\n")
    
    # Create sample image file
    print("1. Creating sample driving license image...")
    img_path = create_sample_driving_license_image()
    print(f"   ✅ Sample image created at: {img_path}")
    
    # Test the scan endpoint
    print("\n2. Testing OCR scan endpoint...")
    
    url = "http://localhost:5002/api/scan"
    
    try:
        with open(img_path, 'rb') as img_file:
            files = {'image': ('driving_license.png', img_file, 'image/png')}
            response = requests.post(url, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ OCR scan successful!")
            print(f"\n   Response:")
            print(json.dumps(result, indent=4))
            
            # Check if driving license enhancements are working
            extracted_info = result.get('extracted_info', {})
            processing_method = result.get('processing_method', 'standard')
            confidence = result.get('confidence', 'medium')
            
            print(f"\n3. Analysis:")
            print(f"   Document Type: {result.get('document_type', 'N/A')}")
            print(f"   Processing Method: {processing_method}")
            print(f"   Confidence Level: {confidence}")
            print(f"   Nationality: {result.get('nationality', 'N/A')}")
            
            if processing_method == 'enhanced_driving_license':
                print("   🎉 Enhanced driving license processing was used!")
            else:
                print("   ⚠️  Standard processing was used")
            
            # Check for specific driving license fields
            license_fields = ['full_name', 'license_number', 'date_of_birth', 'nationality', 'date_of_expiry']
            found_fields = []
            
            for field in license_fields:
                if field in extracted_info and extracted_info[field]:
                    found_fields.append(field)
            
            print(f"   License fields extracted: {len(found_fields)}/{len(license_fields)}")
            for field in found_fields:
                print(f"     ✅ {field}: {extracted_info[field]}")
            
            # Validation checks
            validations = [
                ("Driving License Detection", processing_method == 'enhanced_driving_license'),
                ("Document Type Correct", result.get('document_type') == 'driving license'),
                ("Name Extracted", bool(extracted_info.get('full_name', '').strip())),
                ("Nationality Extracted", result.get('nationality') == 'IND'),
                ("License Number Found", bool(extracted_info.get('license_number', '').strip())),
                ("High Confidence", confidence == 'high')
            ]
            
            passed_count = sum(1 for _, passed in validations if passed)
            
            print(f"\n📊 VALIDATION RESULTS:")
            for validation_name, passed in validations:
                status = "✅" if passed else "❌"
                print(f"   {status} {validation_name}")
            
            print(f"\n📈 SUMMARY: {passed_count}/{len(validations)} validations passed")
            
            return True
            
        else:
            print(f"   ❌ API returned status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to API. Make sure the backend is running on localhost:5002")
        return False
    except Exception as e:
        print(f"   ❌ Error testing API: {e}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(img_path):
            os.remove(img_path)

def test_driving_license_patterns():
    """Test specific pattern extraction for driving license"""
    
    print("\n=== Testing Driving License Pattern Extraction ===\n")
    
    import sys
    sys.path.insert(0, '/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend')
    
    try:
        from app.routes import enhanced_driving_license_extraction, detect_driving_license
        
        test_cases = [
            {
                'name': 'Indian Driving License Text',
                'text': '''
                GOVERNMENT OF INDIA
                DRIVING LICENCE
                DL No: KA20210123456
                Name: VED THAMPI PRINCE VADAKEPAT THAMPI
                Date of Birth: 15/01/1990
                Nationality: INDIAN
                Issue Date: 01/06/2021
                Valid Until: 01/06/2041
                '''
            },
            {
                'name': 'Name Only',
                'text': 'VED THAMPI PRINCE VADAKEPAT THAMPI'
            },
            {
                'name': 'License Number Pattern',
                'text': 'DL No: KA20210123456'
            },
            {
                'name': 'Nationality Pattern',
                'text': 'Nationality: INDIAN'
            }
        ]
        
        for test_case in test_cases:
            print(f"Test: {test_case['name']}")
            print(f"Input: {test_case['text']}")
            
            # Test detection
            is_license = detect_driving_license(test_case['text'])
            print(f"Detected as license: {is_license}")
            
            # Test extraction
            result = enhanced_driving_license_extraction([test_case['text']])
            print(f"Extracted: {result}")
            print("-" * 50)
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    print("🚗 Starting Driving License OCR Test...\n")
    
    success = test_driving_license_api()
    test_driving_license_patterns()
    
    if success:
        print("\n🎉 Driving license OCR test completed!")
        print("\nKey improvements tested:")
        print("• Enhanced preprocessing for driving license documents")
        print("• Improved name extraction patterns")
        print("• Better nationality detection")
        print("• License number extraction")
        print("• Processing method tracking")
    else:
        print("\n⚠️  Some issues were detected during testing.")
