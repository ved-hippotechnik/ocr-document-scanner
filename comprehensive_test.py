#!/usr/bin/env python3
"""
Comprehensive Emirates ID OCR System Demonstration
"""

import requests
import json
from PIL import Image, ImageDraw, ImageFont
import io
import base64

def create_realistic_emirates_id():
    """Create a realistic Emirates ID for testing"""
    
    # Create image with proper Emirates ID dimensions
    img = Image.new('RGB', (800, 500), color='#f8f8f8')
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        header_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        arabic_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        title_font = header_font = text_font = arabic_font = ImageFont.load_default()
    
    # Draw UAE header
    draw.text((50, 30), "UNITED ARAB EMIRATES", fill='#000080', font=title_font)
    draw.text((50, 60), "دولة الإمارات العربية المتحدة", fill='#000080', font=arabic_font)
    
    # Draw Emirates ID title
    draw.text((50, 100), "EMIRATES ID", fill='#8B0000', font=header_font)
    draw.text((50, 125), "بطاقة الهوية الإماراتية", fill='#8B0000', font=arabic_font)
    
    # ID Number
    draw.text((50, 170), "ID Number:", fill='black', font=text_font)
    draw.text((150, 170), "784-2023-5432189-7", fill='#000080', font=header_font)
    
    # Personal Information
    y_pos = 210
    info_pairs = [
        ("Name:", "SARA MOHAMMED AL MANSOURI", "الاسم:", "سارة محمد المنصوري"),
        ("Date of Birth:", "10/03/1995", "تاريخ الميلاد:", "١٠/٠٣/١٩٩٥"),
        ("Gender:", "F", "الجنس:", "أنثى"),
        ("Nationality:", "UAE", "الجنسية:", "إماراتية"),
        ("Expiry Date:", "10/03/2035", "تاريخ الانتهاء:", "١٠/٠٣/٢٠٣٥")
    ]
    
    for eng_label, eng_value, ar_label, ar_value in info_pairs:
        # English
        draw.text((50, y_pos), eng_label, fill='black', font=text_font)
        draw.text((180, y_pos), eng_value, fill='black', font=text_font)
        
        # Arabic
        draw.text((400, y_pos), ar_label, fill='black', font=arabic_font)
        draw.text((500, y_pos), ar_value, fill='black', font=arabic_font)
        
        y_pos += 30
    
    return img

def test_comprehensive_emirates_id():
    """Run comprehensive Emirates ID test"""
    
    print("🇦🇪 COMPREHENSIVE EMIRATES ID OCR TEST")
    print("=" * 60)
    
    # Create test image
    print("1. Creating realistic Emirates ID image...")
    img = create_realistic_emirates_id()
    
    # Save temporarily
    img_path = '/tmp/comprehensive_emirates_test.png'
    img.save(img_path, 'PNG')
    print("   ✅ Emirates ID image created")
    
    # Test API
    print("\n2. Testing OCR API...")
    url = 'http://localhost:5002/api/scan'
    
    try:
        with open(img_path, 'rb') as img_file:
            files = {'image': ('emirates_comprehensive.png', img_file, 'image/png')}
            response = requests.post(url, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ API request successful")
            
            # Display results
            print("\n3. EXTRACTION RESULTS:")
            print("-" * 30)
            
            # Core information
            print(f"📄 Document Type: {result.get('document_type', 'N/A')}")
            print(f"🌍 Nationality: {result.get('nationality', 'N/A')}")
            print(f"⚙️  Processing: {result.get('processing_method', 'standard')}")
            print(f"📊 Confidence: {result.get('confidence', 'medium')}")
            
            # Extracted fields
            extracted = result.get('extracted_info', {})
            print(f"\n📋 EXTRACTED FIELDS:")
            
            field_emojis = {
                'document_number': '🆔',
                'full_name': '👤',
                'date_of_birth': '🎂',
                'gender': '⚧️',
                'nationality': '🌍',
                'date_of_expiry': '📅',
                'unified_number': '🔢'
            }
            
            for field, emoji in field_emojis.items():
                value = extracted.get(field, 'N/A')
                print(f"   {emoji} {field.replace('_', ' ').title()}: {value}")
            
            # Validation
            print(f"\n✅ VALIDATION RESULTS:")
            
            validations = [
                ("Emirates ID Detection", result.get('processing_method') == 'enhanced_emirates_id'),
                ("ID Card Classification", result.get('document_type') == 'ID Card'),
                ("UAE Nationality (Top)", result.get('nationality') == 'UAE'),
                ("UAE Nationality (Extract)", extracted.get('nationality') == 'UAE'),
                ("High Confidence", result.get('confidence') == 'high'),
                ("Valid ID Format", extracted.get('document_number', '').startswith('784')),
                ("Name Extracted", bool(extracted.get('full_name', '').strip())),
                ("Gender Identified", extracted.get('gender') in ['M', 'F']),
                ("Dates Found", bool(extracted.get('date_of_birth')) and bool(extracted.get('date_of_expiry')))
            ]
            
            passed_count = sum(1 for _, passed in validations if passed)
            
            for validation_name, passed in validations:
                status = "✅" if passed else "❌"
                print(f"   {status} {validation_name}")
            
            # Summary
            print(f"\n📈 SUMMARY: {passed_count}/{len(validations)} validations passed")
            
            if passed_count == len(validations):
                print("🎉 PERFECT! Emirates ID OCR system is working flawlessly!")
            elif passed_count >= len(validations) - 2:
                print("✨ EXCELLENT! System is working very well!")
            elif passed_count >= len(validations) // 2:
                print("👍 GOOD! Most features are working correctly!")
            else:
                print("⚠️  NEEDS ATTENTION! Several issues detected!")
            
            # Technical details
            print(f"\n🔧 TECHNICAL DETAILS:")
            print(f"   • Processing Method: {result.get('processing_method', 'N/A')}")
            print(f"   • Text Length: {len(result.get('extracted_text', ''))}")
            print(f"   • Fields Extracted: {len([k for k, v in extracted.items() if v])}")
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    finally:
        # Cleanup
        import os
        if os.path.exists(img_path):
            os.remove(img_path)
    
    print(f"\n🏁 Test completed!")

if __name__ == "__main__":
    test_comprehensive_emirates_id()
