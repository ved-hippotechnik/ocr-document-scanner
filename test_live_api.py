#!/usr/bin/env python3
"""
Live API Test - Test the running Flask application
"""

import requests
import base64
import json
from pathlib import Path

def test_live_api():
    """Test the live API endpoints"""
    base_url = "http://localhost:5002"
    
    print("🧪 Testing Live OCR Document Scanner API")
    print("=" * 50)
    
    # Test health endpoint
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False
    
    # Test processors endpoint
    print("\n🔍 Testing processors endpoint...")
    try:
        response = requests.get(f"{base_url}/api/processors")
        if response.status_code == 200:
            data = response.json()
            print("✅ Processors endpoint working")
            print(f"   Found {data['total_processors']} processors")
            for proc in data['supported_documents']:
                print(f"   - {proc['display_name']} ({proc['country']})")
        else:
            print(f"❌ Processors endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Processors endpoint error: {str(e)}")
    
    # Test document upload with sample image
    print("\n🔍 Testing document upload...")
    try:
        # Use the sample passport image
        image_path = Path("test-images/sample_passport.jpg")
        if image_path.exists():
            with open(image_path, "rb") as f:
                files = {"image": ("sample_passport.jpg", f, "image/jpeg")}
                response = requests.post(f"{base_url}/api/scan", files=files)
                
            if response.status_code == 200:
                data = response.json()
                print("✅ Document processing successful")
                print(f"   Document Type: {data.get('document_type', 'Unknown')}")
                print(f"   Confidence: {data.get('confidence_score', 'N/A')}")
                print(f"   Processing Time: {data.get('processing_time', 'N/A')}s")
                
                # Print extracted data (first few fields)
                extracted_data = data.get('extracted_data', {})
                if extracted_data:
                    print("   Extracted Data:")
                    for key, value in list(extracted_data.items())[:5]:
                        if value and len(str(value)) < 50:
                            print(f"     {key}: {value}")
                    if len(extracted_data) > 5:
                        print(f"     ... and {len(extracted_data) - 5} more fields")
            else:
                print(f"❌ Document processing failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print("⚠️ Sample image not found, skipping upload test")
    except Exception as e:
        print(f"❌ Document upload error: {str(e)}")
    
    # Test stats endpoint
    print("\n🔍 Testing stats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats endpoint working")
            print(f"   Total Scans: {data.get('total_scanned', 0)}")
            doc_types = data.get('document_types', {})
            if doc_types:
                print("   Document Types:")
                for doc_type, count in doc_types.items():
                    if count > 0:
                        print(f"     {doc_type}: {count}")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats endpoint error: {str(e)}")
    
    print("\n✅ API Testing Complete!")
    return True

if __name__ == "__main__":
    test_live_api()
