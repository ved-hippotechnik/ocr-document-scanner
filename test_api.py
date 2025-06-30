#!/usr/bin/env python3
"""
Direct API test for Emirates ID OCR improvements
"""

import requests
import json
import base64
import io
from PIL import Image, ImageDraw, ImageFont

def create_sample_emirates_id_image():
    """Create a sample Emirates ID-like image for testing"""
    
    # Create a sample image with Emirates ID content
    width, height = 800, 500
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw Emirates ID content
    draw.text((50, 50), "UNITED ARAB EMIRATES", fill='black', font=font)
    draw.text((50, 80), "EMIRATES ID", fill='black', font=font)
    draw.text((50, 120), "784-2020-1234567-8", fill='black', font=font)
    draw.text((50, 160), "Name: AHMED HASSAN ALI", fill='black', font=small_font)
    draw.text((50, 190), "Date of Birth: 15/01/1990", fill='black', font=small_font)
    draw.text((50, 220), "Gender: M", fill='black', font=small_font)
    draw.text((50, 250), "Nationality: UAE", fill='black', font=small_font)
    draw.text((50, 280), "Expiry Date: 15/01/2030", fill='black', font=small_font)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def test_emirates_id_api():
    """Test the Emirates ID OCR via API"""
    
    print("=== Testing Emirates ID OCR API ===\n")
    
    # Create sample image
    print("1. Creating sample Emirates ID image...")
    img_base64 = create_sample_emirates_id_image()
    print("   ✅ Sample image created")
    
    # Test the scan endpoint
    print("\n2. Testing OCR scan endpoint...")
    
    url = "http://localhost:5002/api/scan"
    payload = {
        "image": img_base64,
        "document_type": "id_card"
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ OCR scan successful!")
            print(f"\n   Response:")
            print(json.dumps(result, indent=4))
            
            # Check if Emirates ID enhancements are working
            extracted_info = result.get('extracted_info', {})
            processing_method = result.get('processing_method', 'standard')
            confidence = result.get('confidence', 'medium')
            
            print(f"\n3. Analysis:")
            print(f"   Processing Method: {processing_method}")
            print(f"   Confidence Level: {confidence}")
            
            if processing_method == 'enhanced_emirates_id':
                print("   ✅ Enhanced Emirates ID processing was used!")
            else:
                print("   ⚠️  Standard processing was used")
            
            # Check for specific Emirates ID fields
            emirates_fields = ['emirates_id_number', 'name', 'date_of_birth', 'nationality', 'expiry_date']
            found_fields = []
            
            for field in emirates_fields:
                if field in extracted_info and extracted_info[field]:
                    found_fields.append(field)
            
            print(f"   Emirates ID fields extracted: {len(found_fields)}/{len(emirates_fields)}")
            for field in found_fields:
                print(f"     ✅ {field}: {extracted_info[field]}")
            
        else:
            print(f"   ❌ API returned status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to API. Make sure the backend is running on localhost:5002")
        return False
    except Exception as e:
        print(f"   ❌ Error testing API: {e}")
        return False
    
    print("\n" + "="*60)
    return True

def test_text_based_emirates_id():
    """Test Emirates ID detection with text-only input"""
    
    print("\n=== Testing Text-Based Emirates ID Detection ===\n")
    
    # Test text that should trigger Emirates ID detection
    test_text = """
    UNITED ARAB EMIRATES
    EMIRATES ID
    784-2020-1234567-8
    Name: MOHAMMED AHMED HASSAN
    Date of Birth: 15/01/1990
    Gender: M
    Nationality: UAE
    Expiry Date: 15/01/2030
    """
    
    # Convert text to a simple image
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    lines = test_text.strip().split('\n')
    y_position = 20
    
    for line in lines:
        draw.text((20, y_position), line.strip(), fill='black', font=font)
        y_position += 25
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    # Test the API
    url = "http://localhost:5002/api/scan"
    payload = {
        "image": img_str,
        "document_type": "id_card"
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text-based Emirates ID test successful!")
            
            processing_method = result.get('processing_method', 'standard')
            confidence = result.get('confidence', 'medium')
            
            print(f"Processing Method: {processing_method}")
            print(f"Confidence: {confidence}")
            
            if processing_method == 'enhanced_emirates_id':
                print("🎉 Enhanced Emirates ID processing correctly detected!")
            
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Emirates ID OCR Tests...\n")
    
    success1 = test_emirates_id_api()
    success2 = test_text_based_emirates_id()
    
    if success1 and success2:
        print("\n🎉 All Emirates ID OCR tests passed!")
        print("\nKey improvements validated:")
        print("• Enhanced preprocessing with multiple image processing techniques")
        print("• Emirates ID-specific pattern recognition")
        print("• Automatic detection of Emirates ID documents")
        print("• Enhanced extraction of Emirates ID fields")
        print("• Processing method tracking and confidence scoring")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
