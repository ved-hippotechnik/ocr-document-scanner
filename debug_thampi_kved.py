#!/usr/bin/env python3
"""
Debug script to find where "Thampi Kved" is coming from
"""
import sys
import os
import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Add the backend directory to the path
sys.path.append('/Users/vedthampi/CascadeProjects/ocr-document-scanner/backend')

def create_problematic_license():
    """Create a license that might produce 'Thampi Kved'"""
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 20)
        font_large = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 24)
    except:
        font = ImageFont.load_default()
        font_large = ImageFont.load_default()
    
    # Create text that might be misread as "Thampi Kved"
    license_texts = [
        "GOVERNMENT OF INDIA",
        "DRIVING LICENCE", 
        "",
        "Ministry of Road Transport & Highways",
        "",
        "DL No: KA20210123456",
        "",
        # Various problematic name formats
        "Name: Thampi Kved",  # Direct problematic case
        "Date of Birth: 15/01/1990", 
        "Nationality: INDIAN",
        "",
        "Address: 123 Sample Street, Bangalore",
        "Issue Date: 01/06/2021",
        "Valid Until: 01/06/2041",
        "License Class: LMV"
    ]
    
    y_pos = 30
    for text in license_texts:
        if text.startswith("GOVERNMENT") or text.startswith("DRIVING"):
            draw.text((50, y_pos), text, fill='black', font=font_large)
        else:
            draw.text((50, y_pos), text, fill='black', font=font)
        y_pos += 25
    
    return img

def image_to_base64(img):
    """Convert PIL image to base64 string"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def test_with_api():
    """Test using the actual API"""
    print("🔍 Testing with API endpoint...")
    
    # Create test image
    img = create_problematic_license()
    img_b64 = image_to_base64(img)
    
    # Test with API
    url = "http://localhost:5002/api/scan"
    
    try:
        response = requests.post(url, json={'image': img_b64}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ API Response received")
            print(f"Document Type: {result.get('document_type')}")
            print(f"Processing Method: {result.get('processing_method')}")
            
            extracted_info = result.get('extracted_info', {})
            full_name = extracted_info.get('full_name', 'NOT_FOUND')
            
            print(f"Extracted Name: '{full_name}'")
            
            if 'Thampi' in full_name and 'Kved' in full_name:
                print("❌ PROBLEM FOUND: Still getting 'Thampi Kved'")
                print("Raw extracted text:")
                print(result.get('extracted_text', 'No text available')[:500])
            elif full_name.startswith('VED'):
                print("✅ Name correction working correctly")
            else:
                print(f"❓ Unexpected result: {full_name}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_direct_extraction():
    """Test the extraction functions directly"""
    print("\n🧪 Testing extraction functions directly...")
    
    from app.routes import enhanced_driving_license_extraction, correct_name_order
    
    # Test with the exact problematic text
    test_texts = [
        "Name: Thampi Kved",
        "GOVERNMENT OF INDIA\nDRIVING LICENCE\nName: Thampi Kved\nNationality: INDIAN",
        "Thampi Kved",  # Just the name
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: '{text}'")
        
        # Test extraction
        result = enhanced_driving_license_extraction([text])
        extracted_name = result.get('full_name', 'NOT_FOUND')
        print(f"  Extracted: '{extracted_name}'")
        
        # Test correction directly
        if extracted_name != 'NOT_FOUND':
            corrected = correct_name_order(extracted_name)
            print(f"  Corrected: '{corrected}'")

def main():
    """Run debug tests"""
    print("🐛 Debugging 'Thampi Kved' Issue")
    print("=" * 50)
    
    # Test 1: Direct function calls
    test_direct_extraction()
    
    # Test 2: Full API test
    test_with_api()

if __name__ == "__main__":
    main()
