#!/usr/bin/env python3
"""
Create a test image that simulates OCR errors leading to "Thampi Kved"
"""
import requests
import json
from PIL import Image, ImageDraw, ImageFont
import io
import base64

def create_problematic_passport():
    """Create a passport image that would produce OCR errors"""
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 18)
        font_large = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 22)
    except:
        font = ImageFont.load_default()
        font_large = ImageFont.load_default()
    
    # Create passport text that might be misread by OCR
    passport_texts = [
        "REPUBLIC OF INDIA",
        "Type: P",
        "Country Code: IND",
        "Passport No.: T6779059",
        "",
        "Surname:",
        "THAMPI",  # This might be read correctly
        "",
        "Given Name(s):",
        "KVED",   # This simulates OCR misreading "VED" as "KVED"
        "",
        "Nationality: INDIAN",
        "Sex: M",
        "Date of Birth: 05/09/2000",
        "",
        "Place of Birth: MUSCAT, OMAN",
        "Date of Issue: 19/05/2019",
        "Date of Expiry: 18/05/2029",
        "",
        # MRZ that might also be misread
        "P<INDTHAMPI<<KVED<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "T6779059<6IND0009058M2905187<<<<<<<<<<<<<<<2"
    ]
    
    y_pos = 20
    for text in passport_texts:
        if text in ["REPUBLIC OF INDIA"]:
            draw.text((50, y_pos), text, fill='black', font=font_large)
        else:
            draw.text((50, y_pos), text, fill='black', font=font)
        y_pos += 20
    
    return img

def image_to_base64(img):
    """Convert PIL image to base64 string"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def test_problematic_passport():
    """Test the passport that would produce 'Thampi Kved'"""
    print("🧪 Testing Passport with OCR Errors (KVED instead of VED)")
    print("=" * 65)
    
    # Create the problematic image
    passport_img = create_problematic_passport()
    img_b64 = image_to_base64(passport_img)
    
    # Test with the API
    url = "http://localhost:5002/api/scan"
    
    try:
        # Using multipart form data (files)
        buffered = io.BytesIO()
        passport_img.save(buffered, format="PNG")
        buffered.seek(0)
        
        files = {'image': ('test_passport.png', buffered, 'image/png')}
        response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ OCR Processing Completed")
            print(f"📄 Document Type: {result.get('document_type')}")
            print(f"🔧 Processing Method: {result.get('processing_method')}")
            print(f"📊 Confidence: {result.get('confidence')}")
            
            extracted_info = result.get('extracted_info', {})
            full_name = extracted_info.get('full_name', 'NOT FOUND')
            nationality = extracted_info.get('nationality', 'NOT FOUND')
            
            print(f"\n🎯 KEY RESULTS:")
            print(f"   Full Name: '{full_name}'")
            print(f"   Nationality: '{nationality}'")
            
            # Check if the fix worked
            print(f"\n🔍 VALIDATION:")
            if 'VED' in full_name.upper() and not 'KVED' in full_name.upper():
                print("   ✅ OCR error correction: KVED → VED")
            else:
                print("   ❌ OCR error correction failed")
                
            if full_name.upper().startswith('VED'):
                print("   ✅ Name order: VED is first")
            else:
                print("   ❌ Name order: VED is not first")
                
            if nationality == 'IND':
                print("   ✅ Nationality: INDIAN → IND")
            else:
                print("   ❌ Nationality extraction failed")
            
            # Show raw OCR text to see what was extracted
            extracted_text = result.get('extracted_text', '')
            print(f"\n📄 Raw OCR Text (first 300 chars):")
            print(extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text)
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_problematic_passport()
