#!/usr/bin/env python3
"""
Simple Aadhaar card test using the OCR API
"""

import requests
import base64
import json
from PIL import Image, ImageDraw, ImageFont
import io

def create_simple_aadhaar():
    """Create a simple Aadhaar card image for testing"""
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        big_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        big_font = ImageFont.load_default()
    
    # Aadhaar card content based on the attachment
    lines = [
        "भारत सरकार",
        "Government of India", 
        "",
        "Name: Ved Thampi",
        "Date of Birth: 05/09/2000",
        "Gender: Male",
        "",
        "Aadhaar Number: 9704 7285 0296",
        "",
        "मेरा आधार, मेरी पहचान"
    ]
    
    y = 50
    for line in lines:
        if "Aadhaar Number" in line:
            draw.text((50, y), line, fill='red', font=big_font)
        elif line in ["भारत सरकार", "Government of India"]:
            draw.text((50, y), line, fill='blue', font=big_font)
        else:
            draw.text((50, y), line, fill='black', font=font)
        y += 30
    
    return img

def test_aadhaar_ocr():
    """Test Aadhaar card with the OCR API"""
    
    print("🇮🇳 AADHAAR CARD OCR TEST")
    print("=" * 50)
    
    # Create test image
    print("1. Creating Aadhaar test image...")
    img = create_simple_aadhaar()
    
    # Convert to bytes for API
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    print("2. Sending to OCR API...")
    
    # Test the API
    url = "http://localhost:5002/api/scan"
    
    try:
        files = {'image': ('aadhaar_test.png', img_buffer, 'image/png')}
        response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OCR processing successful!")
            
            # Display results
            print(f"\n3. RESULTS:")
            print(f"   📄 Document Type: {result.get('document_type', 'N/A')}")
            print(f"   🌍 Nationality: {result.get('nationality', 'N/A')}")
            print(f"   🔧 Processing Method: {result.get('processing_method', 'standard')}")
            print(f"   📊 Confidence: {result.get('confidence', 'medium')}")
            
            # Extracted info
            extracted = result.get('extracted_info', {})
            if extracted:
                print(f"\n   📋 EXTRACTED FIELDS:")
                for key, value in extracted.items():
                    if value and key != 'mrz_data':
                        print(f"      {key}: {value}")
            
            # Specific Aadhaar validations
            print(f"\n   🎯 AADHAAR VALIDATIONS:")
            
            # Check for Aadhaar number
            doc_num = extracted.get('document_number', '')
            aadhaar_num = ''.join(filter(str.isdigit, doc_num))
            if len(aadhaar_num) == 12:
                print(f"      ✅ 12-digit Aadhaar number found: {doc_num}")
            else:
                print(f"      ❌ Aadhaar number not properly extracted: {doc_num}")
            
            # Check for name
            name = extracted.get('full_name', '')
            if 'ved' in name.lower() and 'thampi' in name.lower():
                print(f"      ✅ Name correctly extracted: {name}")
            else:
                print(f"      ⚠️  Name extraction: {name}")
            
            # Check for date of birth
            dob = extracted.get('date_of_birth', '')
            if '05/09/2000' in dob or '2000' in dob:
                print(f"      ✅ Date of birth found: {dob}")
            else:
                print(f"      ⚠️  Date of birth: {dob}")
            
            # Check for gender
            gender = extracted.get('gender', '')
            if gender in ['M', 'Male']:
                print(f"      ✅ Gender identified: {gender}")
            else:
                print(f"      ⚠️  Gender: {gender}")
            
            # Show raw text for debugging
            raw_text = result.get('extracted_text', '')
            if raw_text:
                print(f"\n   🔍 RAW OCR TEXT:")
                print(f"      {raw_text[:200]}...")
                
                # Check if Aadhaar-specific terms were detected
                aadhaar_indicators = ['aadhaar', 'आधार', '9704', '7285', '0296', 'ved', 'thampi']
                found_indicators = [term for term in aadhaar_indicators if term.lower() in raw_text.lower()]
                print(f"\n   📍 DETECTED TERMS: {', '.join(found_indicators)}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_aadhaar_ocr()
