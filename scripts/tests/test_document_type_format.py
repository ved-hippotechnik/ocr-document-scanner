#!/usr/bin/env python3
"""
Test script to verify document type formatting (capitalization)
"""

import requests
import json
from PIL import Image, ImageDraw, ImageFont

def create_emirates_id_test():
    """Create a simple Emirates ID test image"""
    
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Emirates ID content
    draw.text((50, 50), "United Arab Emirates", fill='black', font=title_font)
    draw.text((50, 80), "بطاقة الهوية الإماراتية", fill='black', font=font)
    draw.text((50, 120), "Name: Ahmed Ali", fill='black', font=font)
    draw.text((50, 150), "ID Number: 784-1985-1234567-8", fill='black', font=font)
    draw.text((50, 180), "Date of Birth: 15/06/1985", fill='black', font=font)
    draw.text((50, 210), "Nationality: UAE", fill='black', font=font)
    draw.text((50, 240), "Gender: Male", fill='black', font=font)
    
    return img

def create_passport_test():
    """Create a simple passport test image"""
    
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Passport content
    draw.text((50, 50), "PASSPORT", fill='black', font=title_font)
    draw.text((50, 80), "United States of America", fill='black', font=font)
    draw.text((50, 120), "Given Name: John", fill='black', font=font)
    draw.text((50, 150), "Surname: Smith", fill='black', font=font)
    draw.text((50, 180), "Date of Birth: 01/01/1990", fill='black', font=font)
    draw.text((50, 210), "Nationality: USA", fill='black', font=font)
    draw.text((50, 240), "Passport No: 123456789", fill='black', font=font)
    
    # Add MRZ-like pattern
    draw.text((50, 320), "P<USASMITH<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<", fill='black', font=font)
    draw.text((50, 340), "1234567890USA9001014M2501017<<<<<<<<<<<<<<04", fill='black', font=font)
    
    return img

def create_driving_license_test():
    """Create a simple driving license test image"""
    
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # UAE Driving License content
    draw.text((50, 50), "Roads and Transport Authority", fill='black', font=title_font)
    draw.text((50, 80), "رخصة القيادة", fill='black', font=font)
    draw.text((50, 120), "Name: Mohammed Ahmed", fill='black', font=font)
    draw.text((50, 150), "License No: 1234567", fill='black', font=font)
    draw.text((50, 180), "Date of Birth: 20/05/1990", fill='black', font=font)
    draw.text((50, 210), "Nationality: UAE", fill='black', font=font)
    draw.text((50, 240), "Class: Light Motor Vehicle", fill='black', font=font)
    draw.text((50, 270), "Traffic File: TR123456", fill='black', font=font)
    
    return img

def test_document_types():
    """Test various document types and their formatting"""
    
    print("🧪 DOCUMENT TYPE FORMATTING TEST")
    print("=" * 50)
    
    # First, test if backend is accessible
    print("\n🔍 Testing backend connectivity...")
    try:
        response = requests.get("http://localhost:5002/", timeout=5)
        print("   ✅ Backend is accessible")
    except Exception as e:
        print(f"   ❌ Backend connection failed: {e}")
        return
    
    test_cases = [
        ("Emirates ID", create_emirates_id_test()),
        ("Passport", create_passport_test()),
        ("Driving License", create_driving_license_test()),
    ]
    
    for doc_name, img in test_cases:
        print(f"\n📄 Testing {doc_name}...")
        
        # Save test image
        temp_path = f'/Users/vedthampi/CascadeProjects/ocr-document-scanner/temp_{doc_name.lower().replace(" ", "_")}.png'
        img.save(temp_path, 'PNG')
        
        # Test API
        url = "http://localhost:5002/api/scan"
        
        try:
            with open(temp_path, 'rb') as img_file:
                files = {'image': (f'{doc_name}.png', img_file, 'image/png')}
                response = requests.post(url, files=files, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                doc_type = result.get('document_type', 'N/A')
                processing_method = result.get('processing_method', 'N/A')
                confidence = result.get('confidence', 'N/A')
                
                print(f"   ✅ API Response:")
                print(f"      📋 Document Type: '{doc_type}'")
                print(f"      🔧 Processing Method: {processing_method}")
                print(f"      📊 Confidence: {confidence}")
                
                # Check formatting
                if doc_type == doc_type.upper() and ' ' in doc_type:
                    print(f"      ✅ Proper capitalization: {doc_type}")
                elif doc_type == doc_type.capitalize():
                    print(f"      ✅ Standard capitalization: {doc_type}")
                elif doc_type.islower():
                    print(f"      ⚠️  Lowercase format: {doc_type}")
                else:
                    print(f"      ℹ️  Format: {doc_type}")
                    
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Cleanup
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    print(f"\n✅ Document type formatting test completed!")

if __name__ == "__main__":
    test_document_types()
