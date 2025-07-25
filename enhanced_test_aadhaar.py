#!/usr/bin/env python3
"""
Enhanced Aadhaar Card OCR Testing Suite
Comprehensive testing and evaluation for Aadhaar card recognition
"""

import requests
import base64
import json
import os
import io
import time
import re
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple

# Configuration
API_BASE_URL = "http://localhost:5001"
API_TIMEOUT = 60
TEMP_IMAGE_PATH = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test_aadhaar_temp.png'

class AadhaarTestResult:
    """Class to store and manage test results"""
    def __init__(self):
        self.test_name = ""
        self.success = False
        self.response_data = None
        self.error_message = ""
        self.processing_time = 0.0
        self.validations_passed = 0
        self.total_validations = 0
        self.quality_score = 0.0
        
    def set_success(self, response_data: dict, processing_time: float):
        self.success = True
        self.response_data = response_data
        self.processing_time = processing_time
        
    def set_failure(self, error_message: str):
        self.success = False
        self.error_message = error_message
        
    def add_validation_results(self, passed: int, total: int):
        self.validations_passed = passed
        self.total_validations = total

def create_enhanced_aadhaar_test_image() -> Image.Image:
    """Create a more realistic Aadhaar card test image"""
    
    # Create larger, higher resolution image
    img = Image.new('RGB', (1200, 750), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load system fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
        text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 22)
        number_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
        hindi_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
        small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
        hindi_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add tricolor header with proper proportions
    draw.rectangle([(0, 0), (1200, 25)], fill='#FF9933')  # Saffron
    draw.rectangle([(0, 25), (1200, 50)], fill='white')    # White
    draw.rectangle([(0, 50), (1200, 75)], fill='#138808')  # Green
    
    # Government of India header - more prominent
    draw.text((80, 90), "भारत सरकार", fill='black', font=text_font)
    draw.text((80, 120), "Government of India", fill='black', font=title_font)
    draw.text((80, 155), "Unique Identification Authority of India", fill='blue', font=text_font)
    
    # Aadhaar logo placeholder
    draw.rectangle([(80, 180), (150, 220)], outline='#FF9933', width=2)
    draw.text((85, 190), "UIDAI", fill='#FF9933', font=small_font)
    
    # Main content area with better spacing
    y_pos = 250
    
    # Aadhaar number (most prominent)
    draw.text((80, y_pos), "आधार संख्या / Aadhaar Number:", fill='black', font=text_font)
    draw.text((80, y_pos + 35), "9704 7285 0296", fill='red', font=number_font)
    
    y_pos += 100
    
    # Name section
    draw.text((80, y_pos), "नाम / Name:", fill='black', font=text_font)
    draw.text((280, y_pos), "Ved Thampi", fill='black', font=text_font)
    
    y_pos += 50
    
    # Date of Birth
    draw.text((80, y_pos), "जन्म तिथि / Date of Birth:", fill='black', font=text_font)
    draw.text((350, y_pos), "05/09/2000", fill='black', font=text_font)
    
    y_pos += 50
    
    # Gender
    draw.text((80, y_pos), "लिंग / Gender:", fill='black', font=text_font)
    draw.text((220, y_pos), "पुरुष / Male", fill='black', font=text_font)
    
    y_pos += 50
    
    # Father's name
    draw.text((80, y_pos), "पिता का नाम / Father's Name:", fill='black', font=text_font)
    draw.text((380, y_pos), "Rajesh Thampi", fill='black', font=text_font)
    
    y_pos += 70
    
    # Address
    draw.text((80, y_pos), "पता / Address:", fill='black', font=text_font)
    draw.text((80, y_pos + 35), "123 Main Street, Trivandrum,", fill='black', font=text_font)
    draw.text((80, y_pos + 65), "Kerala - 695001, India", fill='black', font=text_font)
    
    # Add QR code placeholder (right side)
    draw.rectangle([(850, 250), (1050, 450)], outline='black', width=2)
    draw.text((900, 350), "QR Code", fill='black', font=small_font)
    
    # Photo placeholder
    draw.rectangle([(850, 470), (1050, 620)], outline='black', width=2)
    draw.text((920, 540), "Photo", fill='black', font=small_font)
    
    # Bottom signature area
    draw.text((80, 650), "मेरा आधार, मेरी पहचान", fill='#FF9933', font=text_font)
    draw.text((80, 680), "My Aadhaar, My Identity", fill='#FF9933', font=text_font)
    
    # Add subtle border
    draw.rectangle([(10, 10), (1190, 740)], outline='#CCCCCC', width=3)
    
    return img

def test_api_connectivity():
    """Test basic API connectivity and endpoints"""
    print("🌐 TESTING API CONNECTIVITY")
    print("=" * 50)
    
    # Test main scan endpoint
    print("1. Testing main scan endpoint...")
    try:
        # Simple connectivity test
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        print("   ✅ API server is reachable")
    except Exception as e:
        print(f"   ❌ Cannot reach API server: {e}")
        return False
    
    # Test document types endpoint
    print("2. Testing document types endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/document-types", timeout=10)
        if response.status_code == 200:
            doc_types = response.json()
            print(f"   ✅ Found {len(doc_types)} supported document types")
            if "Aadhaar Card" in doc_types or "aadhaar" in doc_types:
                print("   ✅ Aadhaar Card is supported")
            else:
                print("   ⚠️  Aadhaar Card may not be explicitly supported")
        else:
            print(f"   ❌ Document types endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting document types: {e}")
    
    return True

def test_aadhaar_ocr():
    """Test the Aadhaar card OCR processing"""
    
    print("\n🇮🇳 TESTING AADHAAR CARD OCR")
    print("=" * 60)
    
    # Create test image
    print("1. Creating enhanced Aadhaar card test image...")
    start_time = time.time()
    img = create_enhanced_aadhaar_test_image()
    print(f"   ✅ Test image created ({time.time() - start_time:.2f}s)")
    
    # Save temporarily for testing
    img.save(TEMP_IMAGE_PATH, 'PNG')
    
    # Test the OCR API
    print("\n2. Testing OCR processing...")
    url = f"{API_BASE_URL}/api/scan"
    
    result = None
    try:
        start_time = time.time()
        with open(TEMP_IMAGE_PATH, 'rb') as img_file:
            files = {'image': ('aadhaar_test.png', img_file, 'image/png')}
            response = requests.post(url, files=files, timeout=API_TIMEOUT)
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ OCR processing successful! ({processing_time:.2f}s)")
            
            # Display and analyze results
            quality_score, issues = analyze_aadhaar_results(result)
            
            return {
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'quality_score': quality_score,
                'issues': issues
            }
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return {'success': False, 'error': f"API Error {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {'success': False, 'error': str(e)}
    
    finally:
        # Cleanup
        if os.path.exists(TEMP_IMAGE_PATH):
            os.remove(TEMP_IMAGE_PATH)

def analyze_aadhaar_results(result):
    """Analyze and display the Aadhaar OCR results"""
    
    print("\n3. AADHAAR OCR RESULTS ANALYSIS:")
    print("-" * 50)
    
    # Basic information
    print(f"📄 Document Type: {result.get('document_type', 'N/A')}")
    print(f"🌍 Nationality: {result.get('nationality', 'N/A')}")
    print(f"⚙️  Processing Method: {result.get('processing_method', 'standard')}")
    print(f"📊 Confidence: {result.get('confidence', 'medium')}")
    
    # Extracted information
    extracted_info = result.get('extracted_info', {})
    
    if extracted_info:
        print(f"\n📋 EXTRACTED INFORMATION:")
        
        # Key fields for Aadhaar
        key_fields = [
            ('document_number', '🆔 Aadhaar Number'),
            ('full_name', '👤 Full Name'),  
            ('date_of_birth', '🎂 Date of Birth'),
            ('gender', '⚧️ Gender'),
            ('father_name', '👨 Father\'s Name'),
            ('address', '🏠 Address'),
            ('mobile', '📱 Mobile'),
            ('email', '📧 Email')
        ]
        
        for field_key, field_label in key_fields:
            value = extracted_info.get(field_key, 'N/A')
            if value and value != 'N/A':
                print(f"   {field_label}: {value}")
        
        # Show other extracted fields
        other_fields = {k: v for k, v in extracted_info.items() 
                       if k not in [field[0] for field in key_fields] and v and k != 'raw_text'}
        
        if other_fields:
            print(f"\n📝 OTHER EXTRACTED FIELDS:")
            for key, value in other_fields.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Validation checklist for Aadhaar
    print(f"\n✅ AADHAAR VALIDATION CHECKLIST:")
    
    validations = [
        ("Aadhaar Card Detection", result.get('document_type') in ['ID Card', 'Aadhaar Card', 'aadhaar']),
        ("Indian Context", 'india' in str(result).lower() or 'aadhaar' in str(result).lower()),
        ("Aadhaar Number Found", validate_aadhaar_number(extracted_info.get('document_number', ''))),
        ("Name Extracted", bool(extracted_info.get('full_name', '').strip()) if extracted_info else False),
        ("Date of Birth Found", bool(extracted_info.get('date_of_birth')) if extracted_info else False),
        ("Gender Identified", extracted_info.get('gender') in ['Male', 'Female', 'M', 'F', 'पुरुष', 'महिला'] if extracted_info else False)
    ]
    
    passed = sum(1 for _, check in validations if check)
    
    for validation_name, check in validations:
        status = "✅" if check else "❌"
        print(f"   {status} {validation_name}")
    
    print(f"\n📊 VALIDATION SUMMARY: {passed}/{len(validations)} checks passed")
    
    # Quality analysis
    quality_score, issues = evaluate_extraction_quality(extracted_info)
    
    print(f"\n🎯 EXTRACTION QUALITY: {quality_score:.1f}%")
    if issues:
        print("   ⚠️  Issues identified:")
        for issue in issues:
            print(f"      • {issue}")
    
    # Overall assessment
    if passed >= len(validations) - 1 and quality_score >= 80:
        print("\n🎉 EXCELLENT! Aadhaar card processing is working very well!")
    elif passed >= len(validations) // 2 and quality_score >= 60:
        print("\n👍 GOOD! Most features are working correctly with room for improvement!")
    else:
        print("\n⚠️  NEEDS IMPROVEMENT! Several issues detected that should be addressed.")
    
    # Show raw extracted text for debugging
    raw_text = result.get('extracted_text', '')
    if raw_text:
        print(f"\n🔍 RAW EXTRACTED TEXT (first 300 chars):")
        print(f"   {raw_text[:300]}{'...' if len(raw_text) > 300 else ''}")

    return quality_score, issues

def validate_aadhaar_number(aadhaar_num: str) -> bool:
    """Validate Aadhaar number format"""
    if not aadhaar_num:
        return False
    
    # Remove spaces and special characters
    clean_num = re.sub(r'\D', '', aadhaar_num)
    
    # Should be exactly 12 digits
    return len(clean_num) == 12 and clean_num.isdigit()

def evaluate_extraction_quality(extracted_info: dict) -> Tuple[float, List[str]]:
    """Evaluate the quality of field extraction"""
    
    quality_score = 0
    max_score = 0
    issues = []
    
    # Check Aadhaar number format (12 digits)
    aadhaar_num = extracted_info.get('document_number', '')
    if validate_aadhaar_number(aadhaar_num):
        quality_score += 3
    else:
        if aadhaar_num:
            clean_num = re.sub(r'\D', '', aadhaar_num)
            issues.append(f"Aadhaar number has {len(clean_num)} digits instead of 12")
        else:
            issues.append("Aadhaar number not extracted")
    max_score += 3
    
    # Check name extraction
    name = extracted_info.get('full_name', '')
    if name and len(name) > 2:
        quality_score += 2
    else:
        issues.append("Name not extracted or too short")
    max_score += 2
    
    # Check date format
    dob = extracted_info.get('date_of_birth', '')
    if dob:
        # Check if it's a valid date format
        date_patterns = [r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', r'\d{1,2}\s+\w+\s+\d{4}']
        if any(re.match(pattern, dob) for pattern in date_patterns):
            quality_score += 2
        else:
            issues.append(f"Date of birth format unclear: {dob}")
    else:
        issues.append("Date of birth not extracted")
    max_score += 2
    
    # Check gender
    gender = extracted_info.get('gender', '')
    if gender and gender.lower() in ['male', 'female', 'पुरुष', 'महिला', 'm', 'f']:
        quality_score += 1
    else:
        issues.append("Gender not extracted or invalid")
    max_score += 1
    
    # Check father's name
    father_name = extracted_info.get('father_name', '')
    if father_name and len(father_name) > 2:
        quality_score += 1
    else:
        issues.append("Father's name not extracted")
    max_score += 1
    
    # Check address
    address = extracted_info.get('address', '')
    if address and len(address) > 10:
        quality_score += 1
    else:
        issues.append("Address not extracted or too short")
    max_score += 1
    
    # Calculate percentage
    percentage = (quality_score / max_score * 100) if max_score > 0 else 0
    
    return percentage, issues

def test_real_aadhaar_image():
    """Test with a real Aadhaar image if available"""
    
    print("\n" + "=" * 60)
    print("TESTING WITH REAL AADHAAR IMAGE")
    print("=" * 60)
    
    # Check for saved Aadhaar image
    possible_paths = [
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/aadhaar-card.jpg',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/aadhaar-card.png',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-aadhaar.jpg',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-aadhaar.png',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-images/aadhaar.jpg',
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-images/aadhaar.png'
    ]
    
    real_image_path = None
    for path in possible_paths:
        if os.path.exists(path):
            real_image_path = path
            break
    
    if real_image_path:
        print(f"📸 Found real Aadhaar image: {real_image_path}")
        
        # Test with real image
        url = f"{API_BASE_URL}/api/scan"
        
        try:
            start_time = time.time()
            with open(real_image_path, 'rb') as img_file:
                files = {'image': ('real_aadhaar.jpg', img_file, 'image/jpeg')}
                response = requests.post(url, files=files, timeout=API_TIMEOUT)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Real image processing successful! ({processing_time:.2f}s)")
                quality_score, issues = analyze_aadhaar_results(result)
                return {'success': True, 'quality_score': quality_score}
            else:
                print(f"   ❌ API Error: {response.status_code}")
                return {'success': False}
                
        except Exception as e:
            print(f"   ❌ Error processing real image: {e}")
            return {'success': False, 'error': str(e)}
    else:
        print("📸 No real Aadhaar image found.")
        print("   To test with your Aadhaar image:")
        print("   1. Save your Aadhaar image as 'aadhaar-card.jpg' in this directory")
        print("   2. Run this script again")
        return {'success': False, 'reason': 'no_image'}

def generate_comprehensive_report(test_results: Dict):
    """Generate a comprehensive test report"""
    
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE AADHAAR OCR EVALUATION REPORT")
    print("=" * 80)
    
    print(f"\n📅 Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 API Endpoint: {API_BASE_URL}")
    
    # Synthetic image test results
    synthetic_test = test_results.get('synthetic_test', {})
    if synthetic_test.get('success'):
        print(f"\n🎨 SYNTHETIC IMAGE TEST:")
        print(f"   ✅ Status: Passed")
        print(f"   ⏱️  Processing Time: {synthetic_test.get('processing_time', 'N/A'):.2f}s")
        print(f"   🎯 Quality Score: {synthetic_test.get('quality_score', 'N/A'):.1f}%")
        if synthetic_test.get('issues'):
            print(f"   ⚠️  Issues: {len(synthetic_test.get('issues', []))}")
    else:
        print(f"\n🎨 SYNTHETIC IMAGE TEST:")
        print(f"   ❌ Status: Failed")
        print(f"   Error: {synthetic_test.get('error', 'Unknown error')}")
    
    # Real image test results
    real_test = test_results.get('real_test', {})
    if real_test.get('success'):
        print(f"\n📸 REAL IMAGE TEST:")
        print(f"   ✅ Status: Passed")
        print(f"   🎯 Quality Score: {real_test.get('quality_score', 'N/A'):.1f}%")
    elif real_test.get('reason') == 'no_image':
        print(f"\n📸 REAL IMAGE TEST:")
        print(f"   ⏭️  Status: Skipped (No test image provided)")
    else:
        print(f"\n📸 REAL IMAGE TEST:")
        print(f"   ❌ Status: Failed")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    overall_quality = synthetic_test.get('quality_score', 0)
    if overall_quality >= 85:
        print("   🎉 Excellent performance! The system is working very well for Aadhaar cards.")
        print("   • Consider testing with more diverse Aadhaar card samples")
        print("   • Monitor performance with real-world images")
    elif overall_quality >= 70:
        print("   👍 Good performance with room for improvement.")
        print("   • Fine-tune field extraction patterns")
        print("   • Improve OCR preprocessing for better text recognition")
        print("   • Add validation for extracted data formats")
    else:
        print("   ⚠️  Performance needs significant improvement.")
        print("   • Review Aadhaar-specific detection patterns")
        print("   • Enhance OCR preprocessing techniques")
        print("   • Improve field extraction algorithms")
        print("   • Test with higher quality training images")
    
    # Technical improvements
    print(f"\n🔧 TECHNICAL IMPROVEMENTS:")
    print("   • Add Aadhaar number checksum validation")
    print("   • Implement multilingual text recognition (Hindi + English)")
    print("   • Add address parsing and normalization") 
    print("   • Improve date format standardization")
    print("   • Add confidence scoring for individual fields")

def main():
    """Main test execution function"""
    print("🇮🇳 ENHANCED AADHAAR CARD OCR TESTING SUITE")
    print("=" * 70)
    print("\nThis comprehensive test will:")
    print("• Test API connectivity and endpoints")
    print("• Create and test with synthetic Aadhaar card")
    print("• Test with real Aadhaar image (if available)")
    print("• Analyze extraction quality and accuracy")
    print("• Generate comprehensive evaluation report")
    print("• Provide improvement recommendations")
    
    test_results = {}
    
    # Test API connectivity
    if not test_api_connectivity():
        print("\n❌ API connectivity failed. Cannot proceed with tests.")
        return
    
    # Test with synthetic Aadhaar card
    print("\n" + "=" * 60)
    test_results['synthetic_test'] = test_aadhaar_ocr()
    
    # Test with real Aadhaar image
    test_results['real_test'] = test_real_aadhaar_image()
    
    # Generate comprehensive report
    generate_comprehensive_report(test_results)
    
    print("\n" + "=" * 70)
    print("🏁 AADHAAR TESTING COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    main()
