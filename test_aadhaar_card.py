#!/usr/bin/env python3
"""
Test script for Aadhaar card OCR processing
"""

import requests
import base64
import json
import os
import io
from PIL import Image, ImageDraw, ImageFont

def create_aadhaar_test_image():
    """Create a test Aadhaar card image based on the provided attachment data"""
    
    # Create image based on the attachment information
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        number_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        hindi_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
        hindi_font = ImageFont.load_default()
    
    # Add tricolor header (approximation)
    draw.rectangle([(0, 0), (800, 20)], fill='#FF9933')  # Saffron
    draw.rectangle([(0, 20), (800, 40)], fill='white')    # White
    draw.rectangle([(0, 40), (800, 60)], fill='#138808')  # Green
    
    # Government of India header
    draw.text((50, 80), "भारत सरकार", fill='black', font=text_font)
    draw.text((50, 100), "Government of India", fill='black', font=title_font)
    
    # Based on the visible information in the attachment:
    # Name: Ved Thampi
    # DOB: 05/09/2000
    # Male
    # Aadhaar number: 9704 7285 0296
    
    # Aadhaar number (as visible in the attachment)
    draw.text((50, 140), "आधार संख्या / Aadhaar Number:", fill='black', font=text_font)
    draw.text((50, 160), "9704 7285 0296", fill='red', font=number_font)
    
    # Name
    draw.text((50, 200), "नाम / Name:", fill='black', font=text_font)
    draw.text((200, 200), "Ved Thampi", fill='black', font=text_font)
    
    # Date of Birth
    draw.text((50, 230), "जन्म तिथि / Date of Birth:", fill='black', font=text_font)
    draw.text((250, 230), "05/09/2000", fill='black', font=text_font)
    
    # Gender
    draw.text((50, 260), "लिंग / Gender:", fill='black', font=text_font)
    draw.text((170, 260), "पुरुष / Male", fill='black', font=text_font)
    
    # Address (simplified)
    draw.text((50, 290), "पता / Address:", fill='black', font=text_font)
    draw.text((150, 290), "India", fill='black', font=text_font)
    
    # Bottom text in Hindi and English
    draw.text((50, 420), "मेरा आधार, मेरी पहचान", fill='#FF9933', font=text_font)
    draw.text((50, 450), "My Aadhaar, My Identity", fill='#FF9933', font=text_font)
    
    return img

def test_aadhaar_api():
    """Test the Aadhaar card OCR via API"""
    
    print("🇮🇳 TESTING AADHAAR CARD OCR")
    print("=" * 60)
    
    # Create test image
    print("1. Creating Aadhaar card test image...")
    img = create_aadhaar_test_image()
    print("   ✅ Test image created")
    
    # Save temporarily for testing
    temp_path = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test_aadhaar_temp.png'
    img.save(temp_path, 'PNG')
    
    # Test the OCR API
    print("\n2. Testing OCR API...")
    url = "http://localhost:5002/api/scan"
    
    try:
        with open(temp_path, 'rb') as img_file:
            files = {'image': ('aadhaar_test.png', img_file, 'image/png')}
            response = requests.post(url, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ OCR processing successful!")
            
            # Display results
            display_aadhaar_results(result)
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

def display_aadhaar_results(result):
    """Display the Aadhaar OCR results in a formatted way"""
    
    print("\n3. AADHAAR OCR RESULTS:")
    print("-" * 50)
    
    # Basic information
    print(f"📄 Document Type: {result.get('document_type', 'N/A')}")
    print(f"🌍 Nationality: {result.get('nationality', 'N/A')}")
    print(f"⚙️  Processing Method: {result.get('processing_method', 'standard')}")
    print(f"📊 Confidence: {result.get('confidence', 'medium')}")
    
    # Check processing method
    processing_method = result.get('processing_method', 'standard')
    if 'enhanced' in processing_method:
        print("🎉 Enhanced processing was used!")
    else:
        print("ℹ️  Standard processing was used")
    
    # Extracted information
    extracted_info = result.get('extracted_info', {})
    
    if extracted_info:
        print(f"\n📋 EXTRACTED INFORMATION:")
        
        # Key fields for Aadhaar
        key_fields = [
            ('full_name', '👤 Full Name'),
            ('document_number', '🆔 Aadhaar Number'),
            ('date_of_birth', '🎂 Date of Birth'),
            ('gender', '⚧️ Gender'),
            ('nationality', '🌍 Nationality'),
            ('place_of_birth', '📍 Place of Birth')
        ]
        
        for field_key, field_label in key_fields:
            value = extracted_info.get(field_key, 'N/A')
            if value and value != 'N/A':
                print(f"   {field_label}: {value}")
        
        # Show other extracted fields
        other_fields = {k: v for k, v in extracted_info.items() 
                       if k not in [field[0] for field in key_fields] and v and k != 'mrz_data'}
        
        if other_fields:
            print(f"\n📝 OTHER EXTRACTED FIELDS:")
            for key, value in other_fields.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Validation checklist for Aadhaar
    print(f"\n✅ AADHAAR VALIDATION CHECKLIST:")
    
    validations = [
        ("Aadhaar Card Detection", result.get('document_type') in ['ID Card', 'Aadhaar Card']),
        ("Indian Nationality", result.get('nationality') in ['IND', 'INDIA', 'Indian']),
        ("Aadhaar Number Found", bool(extracted_info.get('document_number', '').replace(' ', '').replace('-', '').isdigit() and len(extracted_info.get('document_number', '').replace(' ', '').replace('-', '')) == 12) if extracted_info.get('document_number') else False),
        ("Name Extracted", bool(extracted_info.get('full_name', '').strip()) if extracted_info else False),
        ("Date of Birth Found", bool(extracted_info.get('date_of_birth')) if extracted_info else False),
        ("Gender Identified", extracted_info.get('gender') in ['M', 'F', 'Male', 'Female'] if extracted_info else False)
    ]
    
    passed = sum(1 for _, check in validations if check)
    
    for validation_name, check in validations:
        status = "✅" if check else "❌"
        print(f"   {status} {validation_name}")
    
    print(f"\n📊 SUMMARY: {passed}/{len(validations)} validations passed")
    
    if passed >= len(validations) - 1:
        print("🎉 EXCELLENT! Aadhaar card processing is working very well!")
    elif passed >= len(validations) // 2:
        print("👍 GOOD! Most features are working correctly!")
    else:
        print("⚠️  Some issues detected. The system may need Aadhaar-specific adjustments.")
    
    # Show raw extracted text for debugging
    raw_text = result.get('extracted_text', '')
    if raw_text:
        print(f"\n🔍 RAW EXTRACTED TEXT (first 300 chars):")
        print(f"   {raw_text[:300]}{'...' if len(raw_text) > 300 else ''}")

def test_real_aadhaar_image():
    """Test with a real Aadhaar image if available"""
    
    print("\n" + "=" * 60)
    print("TESTING WITH REAL AADHAAR IMAGE")
    print("=" * 60)
    
    # Check for saved Aadhaar image
    possible_paths = [
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/aadhaar-card.jpg',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/aadhaar-card.png',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-aadhaar.jpg',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-aadhaar.png'
    ]
    
    real_image_path = None
    for path in possible_paths:
        if os.path.exists(path):
            real_image_path = path
            break
    
    if real_image_path:
        print(f"📸 Found real Aadhaar image: {real_image_path}")
        
        # Test with real image
        url = "http://localhost:5002/api/scan"
        
        try:
            with open(real_image_path, 'rb') as img_file:
                files = {'image': ('real_aadhaar.jpg', img_file, 'image/jpeg')}
                response = requests.post(url, files=files, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Real image processing successful!")
                display_aadhaar_results(result)
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error processing real image: {e}")
    else:
        print("📸 No real Aadhaar image found. To test with your image:")
        print("   1. Save your Aadhaar image as 'aadhaar-card.jpg' in this directory")
        print("   2. Run this script again")

def main():
    """Main test function"""
    print("🇮🇳 AADHAAR CARD OCR TESTING SUITE")
    print("=" * 60)
    
    print("\nThis test will:")
    print("• Create a simulated Aadhaar card based on the provided image")
    print("• Test OCR extraction capabilities")
    print("• Validate Aadhaar-specific fields")
    print("• Check for real Aadhaar image processing")
    
    # Test with simulated image
    test_aadhaar_api()
    
    # Test with real image if available
    test_real_aadhaar_image()
    
    print("\n" + "=" * 60)
    print("🏁 AADHAAR TESTING COMPLETED")
    print("=" * 60)
    
    print("\n💡 RECOMMENDATIONS:")
    print("• The system can process Aadhaar cards using general ID card detection")
    print("• For better accuracy, consider adding Aadhaar-specific preprocessing")
    print("• The 12-digit Aadhaar number format can be enhanced with validation")
    print("• Hindi text recognition could be improved with specialized models")

if __name__ == "__main__":
    main()
