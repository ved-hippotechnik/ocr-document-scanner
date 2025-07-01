#!/usr/bin/env python3
"""
Test V2 Enhanced API endpoints
"""

import requests
import base64
import json
from pathlib import Path

def test_v2_api():
    """Test the v2 enhanced API endpoints"""
    base_url = "http://localhost:5002"
    
    print("🧪 Testing V2 Enhanced API Endpoints")
    print("=" * 45)
    
    # Test v2 health endpoint
    print("🔍 Testing V2 Health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v2/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ V2 Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Components: {list(data['components'].keys())}")
        else:
            print(f"❌ V2 Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ V2 Health check error: {str(e)}")
    
    # Test v2 scan with base64 encoded image
    print("\n🔍 Testing V2 Scan endpoint...")
    try:
        image_path = Path("test-images/sample_passport.jpg")
        if image_path.exists():
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prepare JSON payload
            payload = {
                "image": image_data,
                "document_type": "passport",
                "options": {
                    "enable_quality_check": True,
                    "confidence_threshold": 0.6
                }
            }
            
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{base_url}/api/v2/scan", 
                                   json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ V2 Scan successful")
                print(f"   Document Type: {data.get('document_type', 'Unknown')}")
                print(f"   Confidence: {data.get('confidence', 'N/A')}")
                print(f"   Quality Score: {data.get('quality_score', 'N/A')}")
                print(f"   Processor: {data.get('processor_used', 'N/A')}")
                
                # Show some extracted data
                extracted = data.get('extracted_info', {})
                if extracted:
                    print("   Extracted Data (sample):")
                    for key, value in list(extracted.items())[:3]:
                        if value and len(str(value)) < 50:
                            print(f"     {key}: {value}")
            else:
                print(f"❌ V2 Scan failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print("⚠️ Sample image not found")
    except Exception as e:
        print(f"❌ V2 Scan error: {str(e)}")
    
    # Test v2 classify endpoint
    print("\n🔍 Testing V2 Classify endpoint...")
    try:
        image_path = Path("test-images/sample_passport.jpg")
        if image_path.exists():
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {"image": image_data}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{base_url}/api/v2/classify", 
                                   json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ V2 Classify successful")
                print(f"   Predicted Type: {data.get('predicted_type', 'Unknown')}")
                print(f"   Confidence: {data.get('confidence', 'N/A')}")
                predictions = data.get('predictions', [])
                if predictions:
                    print("   Top Predictions:")
                    for pred in predictions[:3]:
                        print(f"     {pred.get('document_type', 'Unknown')}: {pred.get('confidence', 0):.2f}")
            else:
                print(f"❌ V2 Classify failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print("⚠️ Sample image not found")
    except Exception as e:
        print(f"❌ V2 Classify error: {str(e)}")
    
    # Test v2 quality endpoint
    print("\n🔍 Testing V2 Quality endpoint...")
    try:
        image_path = Path("test-images/sample_passport.jpg")
        if image_path.exists():
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {"image": image_data}
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{base_url}/api/v2/quality", 
                                   json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ V2 Quality assessment successful")
                print(f"   Quality Score: {data.get('quality_score', 'N/A')}")
                issues = data.get('issues', [])
                if issues:
                    print("   Quality Issues:")
                    for issue in issues:
                        print(f"     - {issue}")
                metrics = data.get('metrics', {})
                if metrics:
                    print("   Quality Metrics:")
                    for key, value in metrics.items():
                        print(f"     {key}: {value}")
            else:
                print(f"❌ V2 Quality assessment failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print("⚠️ Sample image not found")
    except Exception as e:
        print(f"❌ V2 Quality assessment error: {str(e)}")
    
    print("\n✅ V2 API Testing Complete!")

if __name__ == "__main__":
    test_v2_api()
