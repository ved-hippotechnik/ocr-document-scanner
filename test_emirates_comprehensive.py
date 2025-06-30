#!/usr/bin/env python3
"""
Test script specifically for the user's Emirates ID image
This creates a test image based on the visible content from the attachment
"""

import requests
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_emirates_id_from_attachment():
    """
    Create a test Emirates ID image based on what's visible in the user's attachment
    The attachment shows a UAE Emirates ID with Arabic and English text
    """
    
    # Create image with Emirates ID dimensions (similar to real card)
    img = Image.new('RGB', (856, 540), color='#f8f8ff')  # Light blue background
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        arabic_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        number_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        title_font = text_font = arabic_font = number_font = ImageFont.load_default()
    
    # Draw UAE header (based on what's visible in the attachment)
    draw.text((50, 30), "UNITED ARAB EMIRATES", fill='navy', font=title_font)
    draw.text((50, 55), "دولة الإمارات العربية المتحدة", fill='navy', font=arabic_font)
    
    # Draw Emirates ID title
    draw.text((50, 90), "EMIRATES ID", fill='darkred', font=title_font)
    draw.text((50, 115), "بطاقة الهوية الإماراتية", fill='darkred', font=arabic_font)
    
    # Add Federal Authority text (visible in attachment)
    draw.text((50, 150), "FEDERAL AUTHORITY FOR IDENTITY", fill='black', font=text_font)
    draw.text((50, 170), "CITIZENSHIP CUSTOMS & PORT SECURITY", fill='black', font=text_font)
    draw.text((50, 190), "الهيئة الاتحادية للهوية والجنسية والجمارك وأمن المنافذ", fill='black', font=arabic_font)
    
    # ID Number (format visible in attachment starts with 784)
    draw.text((50, 230), "ID Number / رقم الهوية", fill='black', font=text_font)
    draw.text((50, 250), "784-2000-1234567-8", fill='navy', font=number_font)
    
    # Personal Information (based on typical Emirates ID layout)
    y_pos = 290
    
    # Name
    draw.text((50, y_pos), "Name / الاسم", fill='black', font=text_font)
    draw.text((200, y_pos), "AHMED HASSAN ALI", fill='black', font=text_font)
    draw.text((400, y_pos), "أحمد حسن علي", fill='black', font=arabic_font)
    y_pos += 25
    
    # Date of Birth
    draw.text((50, y_pos), "Date of Birth / تاريخ الميلاد", fill='black', font=text_font)
    draw.text((200, y_pos), "15/01/1990", fill='black', font=text_font)
    y_pos += 25
    
    # Gender
    draw.text((50, y_pos), "Gender / الجنس", fill='black', font=text_font)
    draw.text((200, y_pos), "M", fill='black', font=text_font)
    draw.text((400, y_pos), "ذكر", fill='black', font=arabic_font)
    y_pos += 25
    
    # Nationality
    draw.text((50, y_pos), "Nationality / الجنسية", fill='black', font=text_font)
    draw.text((200, y_pos), "UAE", fill='black', font=text_font)
    draw.text((400, y_pos), "إماراتي", fill='black', font=arabic_font)
    y_pos += 25
    
    # Expiry Date
    draw.text((50, y_pos), "Expiry Date / تاريخ الانتهاء", fill='black', font=text_font)
    draw.text((200, y_pos), "15/01/2030", fill='black', font=text_font)
    
    return img

def test_emirates_id_ocr():
    """Test the Emirates ID with the OCR system"""
    
    print("🇦🇪 EMIRATES ID OCR TEST")
    print("=" * 60)
    
    # Create test image based on the attachment
    print("1. Creating Emirates ID test image based on your attachment...")
    img = create_emirates_id_from_attachment()
    
    # Save the test image
    img_path = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test_emirates_attachment.png'
    img.save(img_path, 'PNG')
    print(f"   ✅ Test image created: {img_path}")
    
    # Test with OCR API
    print("\n2. Testing with OCR API...")
    url = "http://localhost:5002/api/scan"
    
    try:
        with open(img_path, 'rb') as img_file:
            files = {'image': ('emirates_id_test.png', img_file, 'image/png')}
            response = requests.post(url, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ OCR processing successful!")
            
            # Display detailed results
            display_detailed_results(result)
            
            # Cleanup
            os.remove(img_path)
            return True
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def display_detailed_results(result):
    """Display comprehensive OCR results"""
    
    print("\n3. DETAILED OCR ANALYSIS:")
    print("=" * 50)
    
    # Core Document Information
    doc_type = result.get('document_type', 'N/A')
    nationality = result.get('nationality', 'N/A')
    processing_method = result.get('processing_method', 'standard')
    confidence = result.get('confidence', 'medium')
    
    print(f"📄 Document Type: {doc_type}")
    print(f"🌍 Top-Level Nationality: {nationality}")
    print(f"⚙️  Processing Method: {processing_method}")
    print(f"📊 Confidence Level: {confidence}")
    
    # Check if Emirates ID processing was triggered
    if processing_method == 'enhanced_emirates_id':
        print("🎉 EXCELLENT! Enhanced Emirates ID processing was used!")
    elif 'emirates' in processing_method.lower():
        print("✅ Emirates ID processing detected")
    else:
        print("⚠️  Standard processing was used")
    
    # Extracted Information Analysis
    extracted_info = result.get('extracted_info', {})
    
    if extracted_info:
        print(f"\n📋 EXTRACTED INFORMATION:")
        print("-" * 30)
        
        # Key Emirates ID fields
        emirates_fields = [
            ('document_number', '🆔 Emirates ID Number'),
            ('unified_number', '🔢 Unified Number'),
            ('full_name', '👤 Full Name'),
            ('date_of_birth', '🎂 Date of Birth'),
            ('gender', '⚧️ Gender'),
            ('nationality', '🌍 Nationality'),
            ('date_of_expiry', '📅 Expiry Date'),
            ('date_of_issue', '📋 Issue Date')
        ]
        
        extracted_count = 0
        for field_key, field_label in emirates_fields:
            value = extracted_info.get(field_key)
            if value and str(value).strip():
                print(f"   {field_label}: {value}")
                extracted_count += 1
            else:
                print(f"   {field_label}: ❌ Not found")
        
        print(f"\n   📊 Extraction Rate: {extracted_count}/{len(emirates_fields)} fields")
        
        # Show any additional fields
        other_fields = {k: v for k, v in extracted_info.items() 
                       if k not in [field[0] for field in emirates_fields] 
                       and v and str(v).strip() and k != 'mrz_data'}
        
        if other_fields:
            print(f"\n📝 ADDITIONAL FIELDS:")
            for key, value in other_fields.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Emirates ID Specific Validations
    print(f"\n✅ EMIRATES ID VALIDATION CHECKLIST:")
    print("-" * 40)
    
    validations = [
        ("Emirates ID Detection", processing_method == 'enhanced_emirates_id'),
        ("Document Type = ID Card", doc_type == 'ID Card'),
        ("UAE Nationality (Top Level)", nationality == 'UAE'),
        ("UAE Nationality (Extracted)", extracted_info.get('nationality') == 'UAE'),
        ("High Confidence Score", confidence == 'high'),
        ("Emirates ID Number Format", check_emirates_id_format(extracted_info.get('document_number'))),
        ("Name Extraction Success", bool(extracted_info.get('full_name', '').strip())),
        ("Date Fields Present", bool(extracted_info.get('date_of_birth')) and bool(extracted_info.get('date_of_expiry'))),
        ("Gender Identified", extracted_info.get('gender') in ['M', 'F'])
    ]
    
    passed_validations = 0
    for validation_name, passed in validations:
        status = "✅" if passed else "❌"
        print(f"   {status} {validation_name}")
        if passed:
            passed_validations += 1
    
    # Overall Assessment
    print(f"\n📈 OVERALL ASSESSMENT:")
    print("-" * 25)
    
    score_percentage = (passed_validations / len(validations)) * 100
    print(f"Score: {passed_validations}/{len(validations)} ({score_percentage:.1f}%)")
    
    if score_percentage >= 90:
        print("🏆 OUTSTANDING! Emirates ID processing is working perfectly!")
    elif score_percentage >= 75:
        print("🎉 EXCELLENT! System is performing very well!")
    elif score_percentage >= 60:
        print("👍 GOOD! Most features are working correctly!")
    elif score_percentage >= 40:
        print("⚠️  FAIR! Some improvements needed!")
    else:
        print("❌ NEEDS ATTENTION! Multiple issues detected!")
    
    # Show raw extracted text for debugging if needed
    raw_text = result.get('extracted_text', '')
    if raw_text:
        print(f"\n🔍 RAW OCR TEXT (first 200 chars):")
        print(f"   {raw_text[:200]}...")

def check_emirates_id_format(id_number):
    """Check if the Emirates ID number follows the correct format"""
    if not id_number:
        return False
    
    # Clean the ID number
    clean_id = ''.join(c for c in str(id_number) if c.isdigit())
    
    # Emirates ID should be 15 digits starting with 784
    return len(clean_id) == 15 and clean_id.startswith('784')

def main():
    """Main test function"""
    
    print("🚀 EMIRATES ID OCR TESTING SYSTEM")
    print("=" * 60)
    print("📝 This test creates an Emirates ID image based on your attachment")
    print("   and tests it with the enhanced OCR system.\n")
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:5002/api/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and accessible")
        else:
            print("❌ Backend responded but with error status")
            return
    except:
        print("❌ Backend is not running! Please start it with:")
        print("   cd backend && python run.py")
        return
    
    # Run the test
    success = test_emirates_id_ocr()
    
    if success:
        print(f"\n🏁 TEST COMPLETED SUCCESSFULLY!")
        print(f"\n💡 NEXT STEPS:")
        print(f"   • To test your actual Emirates ID image:")
        print(f"     1. Save your image as 'my-emirates-id.jpg' in this directory")
        print(f"     2. Use the web interface at http://localhost:3005")
        print(f"     3. Or modify this script to use your image file")
        print(f"\n🌐 WEB INTERFACE:")
        print(f"   Open http://localhost:3005 in your browser to test with the UI")
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"   Please check the error messages above and ensure:")
        print(f"   • Backend is running properly")
        print(f"   • All dependencies are installed")
        print(f"   • OCR engines (Tesseract) are available")

if __name__ == "__main__":
    main()
