#!/usr/bin/env python3
"""
Enhanced Test script for Aadhaar card OCR processing with integrated improvements
Provides comprehensive testing and validation for Aadhaar card recognition
"""

import requests
import base64
import json
import os
import io
import time
import re
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple

# Import enhanced processors
try:
    from enhanced_image_processor import EnhancedImageProcessor, ProfessionalTestImageGenerator
    ENHANCED_PROCESSOR_AVAILABLE = True
except ImportError:
    ENHANCED_PROCESSOR_AVAILABLE = False
    print("⚠️  Enhanced image processor not available - using basic processing")

try:
    from performance_optimizer import PerformanceOptimizer
    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZER_AVAILABLE = False
    print("⚠️  Performance optimizer not available - using standard processing")

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

class EnhancedAadhaarTester:
    """Enhanced Aadhaar card testing with comprehensive validation"""
    
    def __init__(self):
        self.test_results: List[AadhaarTestResult] = []
        
    def create_enhanced_aadhaar_test_image(self) -> Image.Image:
        """Create a more realistic Aadhaar card test image using enhanced processor if available"""
        
        if ENHANCED_PROCESSOR_AVAILABLE:
            # Use professional test image generator
            generator = ProfessionalTestImageGenerator()
            return generator.create_professional_aadhaar()
        else:
            # Fall back to basic image generation
            return self._create_basic_aadhaar_image()
    
    def _create_basic_aadhaar_image(self) -> Image.Image:
        """Create basic Aadhaar card test image (fallback)"""
        
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
        except Exception:
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

def create_aadhaar_test_image():
    """Create a test Aadhaar card image"""
    processor = AadhaarProcessor()
    return processor.create_enhanced_aadhaar_test_image()

def test_aadhaar_api():
    """Test the Aadhaar card OCR via API"""
    
    print("🇮🇳 TESTING AADHAAR CARD OCR")
    print("=" * 60)
    
    # Create test image
    print("1. Creating Aadhaar card test image...")
    img = create_aadhaar_test_image()
    print("   ✅ Test image created")
    
    # Save temporarily for testing
    temp_path = '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test_aadhaar_temp.png'
    img.save(temp_path, 'PNG')
    
    # Test the OCR API
    print("\n2. Testing OCR API...")
    url = "http://localhost:5001/api/scan"
    
    try:
        with open(temp_path, 'rb') as img_file:
            files = {'image': ('aadhaar_test.png', img_file, 'image/png')}
            response = requests.post(url, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ OCR processing successful!")
            
            # Display results
            display_aadhaar_results(result)
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

def display_aadhaar_results(result):
    """Display the Aadhaar OCR results in a formatted way"""
    
    print("\n3. AADHAAR OCR RESULTS:")
    print("-" * 50)
    
    # Basic information
    print(f"📄 Document Type: {result.get('document_type', 'N/A')}")
    print(f"🌍 Nationality: {result.get('nationality', 'N/A')}")
    print(f"⚙️  Processing Method: {result.get('processing_method', 'standard')}")
    print(f"📊 Confidence: {result.get('confidence', 'medium')}")
    
    # Check processing method
    processing_method = result.get('processing_method', 'standard')
    if 'enhanced' in processing_method:
        print("🎉 Enhanced processing was used!")
    else:
        print("ℹ️  Standard processing was used")
    
    # Extracted information
    extracted_info = result.get('extracted_info', {})
    
    if extracted_info:
        print(f"\n📋 EXTRACTED INFORMATION:")
        
        # Key fields for Aadhaar
        key_fields = [
            ('full_name', '👤 Full Name'),
            ('document_number', '🆔 Aadhaar Number'),
            ('date_of_birth', '🎂 Date of Birth'),
            ('gender', '⚧️ Gender'),
            ('nationality', '🌍 Nationality'),
            ('place_of_birth', '📍 Place of Birth')
        ]
        
        for field_key, field_label in key_fields:
            value = extracted_info.get(field_key, 'N/A')
            if value and value != 'N/A':
                print(f"   {field_label}: {value}")
        
        # Show other extracted fields
        other_fields = {k: v for k, v in extracted_info.items() 
                       if k not in [field[0] for field in key_fields] and v and k != 'mrz_data'}
        
        if other_fields:
            print(f"\n📝 OTHER EXTRACTED FIELDS:")
            for key, value in other_fields.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Validation checklist for Aadhaar
    print(f"\n✅ AADHAAR VALIDATION CHECKLIST:")
    
    validations = [
        ("Aadhaar Card Detection", result.get('document_type') in ['ID Card', 'Aadhaar Card']),
        ("Indian Nationality", result.get('nationality') in ['IND', 'INDIA', 'Indian']),
        ("Aadhaar Number Found", bool(extracted_info.get('document_number', '').replace(' ', '').replace('-', '').isdigit() and len(extracted_info.get('document_number', '').replace(' ', '').replace('-', '')) == 12) if extracted_info.get('document_number') else False),
        ("Name Extracted", bool(extracted_info.get('full_name', '').strip()) if extracted_info else False),
        ("Date of Birth Found", bool(extracted_info.get('date_of_birth')) if extracted_info else False),
        ("Gender Identified", extracted_info.get('gender') in ['M', 'F', 'Male', 'Female'] if extracted_info else False)
    ]
    
    passed = sum(1 for _, check in validations if check)
    
    for validation_name, check in validations:
        status = "✅" if check else "❌"
        print(f"   {status} {validation_name}")
    
    print(f"\n📊 SUMMARY: {passed}/{len(validations)} validations passed")
    
    if passed >= len(validations) - 1:
        print("🎉 EXCELLENT! Aadhaar card processing is working very well!")
    elif passed >= len(validations) // 2:
        print("👍 GOOD! Most features are working correctly!")
    else:
        print("⚠️  Some issues detected. The system may need Aadhaar-specific adjustments.")
    
    # Show raw extracted text for debugging
    raw_text = result.get('extracted_text', '')
    if raw_text:
        print(f"\n🔍 RAW EXTRACTED TEXT (first 300 chars):")
        print(f"   {raw_text[:300]}{'...' if len(raw_text) > 300 else ''}")

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
        '/Users/vedthampi/CascadeProjects/ocr-document-scanner/test-aadhaar.png'
    ]
    
    real_image_path = None
    for path in possible_paths:
        if os.path.exists(path):
            real_image_path = path
            break
    
    if real_image_path:
        print(f"📸 Found real Aadhaar image: {real_image_path}")
        
        # Test with real image
        url = "http://localhost:5001/api/scan"
        
        try:
            with open(real_image_path, 'rb') as img_file:
                files = {'image': ('real_aadhaar.jpg', img_file, 'image/jpeg')}
                response = requests.post(url, files=files, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Real image processing successful!")
                display_aadhaar_results(result)
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error processing real image: {e}")
    else:
        print("📸 No real Aadhaar image found. To test with your image:")
        print("   1. Save your Aadhaar image as 'aadhaar-card.jpg' in this directory")
        print("   2. Run this script again")

def run_comprehensive_tests():
    """Run comprehensive test suite for all document types"""
    print("\n" + "=" * 80)
    print("🔍 COMPREHENSIVE OCR DOCUMENT SCANNER EVALUATION")
    print("=" * 80)
    
    # Test API availability
    print("\n1. 🌐 Testing API Connection...")
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ API is accessible")
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        return
    
    # Test document types endpoint
    print("\n2. 📋 Testing Document Types Endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/document-types", timeout=10)
        if response.status_code == 200:
            doc_types = response.json()
            print(f"   ✅ Found {len(doc_types)} supported document types:")
            for doc_type in doc_types:
                print(f"      • {doc_type}")
        else:
            print(f"   ❌ Document types endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting document types: {e}")
    
    # Test statistics endpoint
    print("\n3. 📊 Testing Statistics Endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/statistics", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Statistics endpoint working:")
            print(f"      • Total documents processed: {stats.get('total_documents', 'N/A')}")
            print(f"      • Success rate: {stats.get('success_rate', 'N/A')}%")
        else:
            print(f"   ❌ Statistics endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting statistics: {e}")

def evaluate_extraction_quality(result):
    """Evaluate the quality of field extraction"""
    extracted_info = result.get('extracted_info', {})
    
    quality_score = 0
    max_score = 0
    issues = []
    
    # Check Aadhaar number format (12 digits)
    aadhaar_num = extracted_info.get('document_number', '')
    if aadhaar_num:
        clean_num = re.sub(r'\D', '', aadhaar_num)
        if len(clean_num) == 12:
            quality_score += 3
        else:
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
    if gender and gender.lower() in ['male', 'female', 'पुरुष', 'महिला']:
        quality_score += 1
    else:
        issues.append("Gender not extracted or invalid")
    max_score += 1
    
    # Calculate percentage
    percentage = (quality_score / max_score * 100) if max_score > 0 else 0
    
    print(f"\n🎯 EXTRACTION QUALITY ANALYSIS:")
    print(f"   Quality Score: {quality_score}/{max_score} ({percentage:.1f}%)")
    
    if issues:
        print(f"   ⚠️  Issues found:")
        for issue in issues:
            print(f"      • {issue}")
    
    return percentage, issues

# Test with real image if available
real_image_path = os.path.join(os.path.dirname(__file__), "aadhaar-card.jpg")
if os.path.exists(real_image_path):
    print("\n3. Testing with real Aadhaar image...")
    try:
        with open(real_image_path, 'rb') as img_file:
            files = {'image': img_file}
            response = requests.post(url, files=files)
            
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Real image processing successful!")
            display_aadhaar_results(result)
        else:
            print(f"   ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error processing real image: {e}")
else:
    print("📸 No real Aadhaar image found. To test with your image:")
    print("   1. Save your Aadhaar image as 'aadhaar-card.jpg' in this directory")
    print("   2. Run this script again")

def main():
    """Main test function"""
    print("🇮🇳 AADHAAR CARD OCR TESTING SUITE")
    print("=" * 60)
    
    print("\nThis test will:")
    print("• Create a simulated Aadhaar card based on the provided image")
    print("• Test OCR extraction capabilities")
    print("• Validate Aadhaar-specific fields")
    print("• Check for real Aadhaar image processing")
    
    # Test with simulated image
    test_aadhaar_api()
    
    # Test with real image if available
    test_real_aadhaar_image()
    
    print("\n" + "=" * 60)
    print("🏁 AADHAAR TESTING COMPLETED")
    print("=" * 60)
    
    print("\n💡 RECOMMENDATIONS:")
    print("• The system can process Aadhaar cards using general ID card detection")
    print("• For better accuracy, consider adding Aadhaar-specific preprocessing")
    print("• The 12-digit Aadhaar number format can be enhanced with validation")
    print("• Hindi text recognition could be improved with specialized models")

if __name__ == "__main__":
    main()
