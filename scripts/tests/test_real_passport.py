#!/usr/bin/env python3
"""
Test the actual passport image processing
"""
import requests
import base64
import json
import sys

def test_with_api_upload():
    """Test by uploading the image via the API"""
    print("🧪 Testing Passport with API Upload")
    print("=" * 50)
    
    url = "http://localhost:5002/api/scan"
    
    # You'll need to save the passport image as 'passport_test.jpg'
    image_path = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/passport_test.jpg'
    
    try:
        # Read the image file
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(url, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ OCR Processing Completed")
            print(f"Document Type: {result.get('document_type')}")
            print(f"Processing Method: {result.get('processing_method')}")
            print(f"Confidence: {result.get('confidence')}")
            
            extracted_info = result.get('extracted_info', {})
            print(f"\n📋 Extracted Information:")
            
            for key, value in extracted_info.items():
                if value and key != 'mrz_data':
                    print(f"  {key}: {value}")
            
            # Focus on the name
            full_name = extracted_info.get('full_name', 'NOT FOUND')
            print(f"\n🎯 FULL NAME RESULT: '{full_name}'")
            
            # Check if it contains the problematic "Thampi Kved"
            if 'Thampi Kved' in full_name or 'THAMPI KVED' in full_name:
                print("❌ Found the problematic name!")
                print("   This suggests OCR is reading it incorrectly")
            elif full_name.startswith('VED') or full_name.startswith('Ved'):
                print("✅ Name order is correct!")
            else:
                print("⚠️  Unexpected name format")
            
            # Show extracted text to see what OCR actually read
            extracted_text = result.get('extracted_text', '')
            print(f"\n📄 OCR Text Preview (first 800 chars):")
            print(extracted_text[:800] + "..." if len(extracted_text) > 800 else extracted_text)
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except FileNotFoundError:
        print(f"❌ Image file not found at: {image_path}")
        print("Please save the passport image as 'passport_test.jpg' in the project directory")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_with_api_upload()
