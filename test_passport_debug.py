#!/usr/bin/env python3
"""
Test script specifically for the passport image to debug the name issue
"""
import requests
import base64
import json
from PIL import Image
import io

def image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as img_file:
        img_data = img_file.read()
        img_str = base64.b64encode(img_data).decode()
        return img_str

def test_passport_ocr():
    """Test the OCR with the actual passport image"""
    print("🧪 Testing Passport OCR with actual image")
    print("=" * 60)
    
    # First, let's save the image to test with
    print("Please save the passport image as 'test_passport.jpg' in the current directory")
    print("Then run this test again.")
    
    # For now, let's test with a simulated passport OCR text that might be extracted
    url = "http://localhost:5002/api/scan"
    
    # Create a simple test image
    img = Image.new('RGB', (800, 500), color='white')
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Test with JSON payload (base64 image)
    payload = {
        'image': img_str
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response received")
            print(f"Document Type: {result.get('document_type')}")
            print(f"Processing Method: {result.get('processing_method')}")
            
            extracted_info = result.get('extracted_info', {})
            full_name = extracted_info.get('full_name', 'NOT FOUND')
            nationality = extracted_info.get('nationality', 'NOT FOUND')
            
            print(f"Full Name: '{full_name}'")
            print(f"Nationality: '{nationality}'")
            
            # Show the extracted text to see what OCR is producing
            extracted_text = result.get('extracted_text', '')
            print(f"\nExtracted Text Preview:")
            print(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_passport_ocr()
