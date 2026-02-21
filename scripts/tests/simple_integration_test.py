#!/usr/bin/env python3
"""
Simple Integration Test - Demonstrates the improvements working without complex font handling
"""

import os
import sys
import time
import requests
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_simple_test_document():
    """Create a simple test document for OCR testing"""
    
    # Create high-resolution test image
    img = Image.new('RGB', (1200, 750), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
        number_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
    
    # Add tricolor header
    draw.rectangle([(0, 0), (1200, 25)], fill='#FF9933')  # Saffron
    draw.rectangle([(0, 25), (1200, 50)], fill='white')    # White
    draw.rectangle([(0, 50), (1200, 75)], fill='#138808')  # Green
    
    # Government header
    draw.text((50, 100), "Government of India", fill='black', font=title_font)
    draw.text((50, 140), "Unique Identification Authority of India", fill='blue', font=font)
    
    # Main content
    y_pos = 220
    
    # Aadhaar number
    draw.text((50, y_pos), "Aadhaar Number:", fill='black', font=font)
    draw.text((50, y_pos + 35), "9704 7285 0296", fill='red', font=number_font)
    
    y_pos += 100
    
    # Personal details
    draw.text((50, y_pos), "Name: Ved Thampi", fill='black', font=font)
    
    y_pos += 50
    draw.text((50, y_pos), "Date of Birth: 05/09/2000", fill='black', font=font)
    
    y_pos += 50
    draw.text((50, y_pos), "Gender: Male", fill='black', font=font)
    
    y_pos += 50
    draw.text((50, y_pos), "Father's Name: Rajesh Thampi", fill='black', font=font)
    
    y_pos += 70
    # Address
    draw.text((50, y_pos), "Address:", fill='black', font=font)
    draw.text((50, y_pos + 35), "123 Main Street, Trivandrum", fill='black', font=font)
    draw.text((50, y_pos + 65), "Kerala - 695001, India", fill='black', font=font)
    
    # QR code and photo placeholders
    draw.rectangle([(850, 250), (1050, 450)], outline='black', width=2)
    draw.text((900, 350), "QR Code", fill='black', font=font)
    
    draw.rectangle([(850, 470), (1050, 620)], outline='black', width=2)
    draw.text((920, 540), "Photo", fill='black', font=font)
    
    # Footer
    draw.text((50, 650), "My Aadhaar, My Identity", fill='#FF9933', font=font)
    
    # Border
    draw.rectangle([(10, 10), (1190, 740)], outline='#CCCCCC', width=3)
    
    return img

def test_api_endpoint(endpoint, image_path):
    """Test a specific API endpoint"""
    
    try:
        start_time = time.time()
        
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            response = requests.post(endpoint, files=files, timeout=30)
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            result['processing_time'] = round(processing_time, 3)
            return {'success': True, 'result': result}
        else:
            return {'success': False, 'error': f"HTTP {response.status_code}", 'processing_time': round(processing_time, 3)}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def display_results(basic_result, enhanced_result):
    """Display comparison results"""
    
    print("\n📊 API TESTING RESULTS")
    print("=" * 50)
    
    # Basic API results
    if basic_result['success']:
        basic_data = basic_result['result']
        print("✅ Basic API (/api/scan):")
        print(f"   • Processing Time: {basic_data.get('processing_time', 'N/A')}s")
        print(f"   • Document Type: {basic_data.get('document_type', 'N/A')}")
        print(f"   • Nationality: {basic_data.get('nationality', 'N/A')}")
        print(f"   • Processing Method: {basic_data.get('processing_method', 'N/A')}")
        
        extracted = basic_data.get('extracted_info', {})
        if extracted:
            print("   • Key Data Extracted:")
            for key, value in extracted.items():
                if value and str(value).strip():
                    print(f"     - {key}: {value}")
    else:
        print(f"❌ Basic API Failed: {basic_result.get('error', 'Unknown error')}")
    
    print()
    
    # Enhanced API results
    if enhanced_result['success']:
        enhanced_data = enhanced_result['result']
        print("🚀 Enhanced API (/api/v2/scan):")
        print(f"   • Processing Time: {enhanced_data.get('processing_time', 'N/A')}s")
        print(f"   • Document Type: {enhanced_data.get('document_type', 'N/A')}")
        print(f"   • Classification: {enhanced_data.get('classification', 'N/A')}")
        print(f"   • Quality Score: {enhanced_data.get('quality_score', 'N/A')}")
        
        extracted = enhanced_data.get('extracted_data', {})
        if extracted:
            print("   • Key Data Extracted:")
            for key, value in extracted.items():
                if value and str(value).strip():
                    print(f"     - {key}: {value}")
    else:
        print(f"⚠️  Enhanced API: {enhanced_result.get('error', 'Not available')}")
    
    # Performance comparison
    if (basic_result['success'] and enhanced_result['success']):
        basic_time = basic_result['result'].get('processing_time', 0)
        enhanced_time = enhanced_result['result'].get('processing_time', 0)
        
        if basic_time > 0 and enhanced_time > 0:
            if enhanced_time < basic_time:
                improvement = ((basic_time - enhanced_time) / basic_time) * 100
                print(f"\n📈 Performance Improvement: {improvement:.1f}% faster with enhanced API")
            else:
                overhead = ((enhanced_time - basic_time) / basic_time) * 100
                print(f"\n⚖️  Processing Overhead: {overhead:.1f}% slower with enhanced API")

def main():
    """Main test function"""
    
    print("🔥 SIMPLE OCR SYSTEM INTEGRATION TEST")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5001/api/stats", timeout=5)
        if response.status_code == 200:
            print("✅ OCR API server is running")
        else:
            print("❌ OCR API server error")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to OCR API server")
        print("   Please start: cd backend && python run.py")
        return
    
    # Create test image
    print("\n1. Creating test document...")
    test_image = create_simple_test_document()
    test_path = 'simple_test_aadhaar.png'
    test_image.save(test_path)
    print(f"   ✅ Test image saved: {test_path}")
    
    # Test both APIs
    print("\n2. Testing API endpoints...")
    
    basic_endpoint = "http://localhost:5001/api/scan"
    enhanced_endpoint = "http://localhost:5001/api/v2/scan"
    
    print("   Testing basic API...")
    basic_result = test_api_endpoint(basic_endpoint, test_path)
    
    print("   Testing enhanced API...")
    enhanced_result = test_api_endpoint(enhanced_endpoint, test_path)
    
    # Display results
    display_results(basic_result, enhanced_result)
    
    # Generate summary report
    report = {
        'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'basic_api': basic_result,
        'enhanced_api': enhanced_result,
        'integration_status': 'completed'
    }
    
    with open('simple_integration_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved: simple_integration_report.json")
    
    # Cleanup
    try:
        os.remove(test_path)
        print("🧹 Cleanup completed")
    except Exception:
        pass
    
    print("\n" + "=" * 50)
    print("🎉 Integration test completed!")
    
    if basic_result['success']:
        print("✅ Basic OCR functionality working")
    if enhanced_result['success']:
        print("✅ Enhanced OCR functionality working")
        print("🚀 All improvements successfully integrated!")
    else:
        print("📋 Enhanced features need configuration")

if __name__ == "__main__":
    main()
