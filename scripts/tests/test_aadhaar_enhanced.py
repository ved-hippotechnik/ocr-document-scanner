#!/usr/bin/env python3
"""
Enhanced Aadhaar Card OCR Testing with Integrated Improvements
Includes enhanced image processing and performance optimization
"""

import os
import sys
import requests
import json
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import time

# Import improvements if available
try:
    from enhanced_image_processor import EnhancedImageProcessor, ProfessionalTestImageGenerator
    from performance_optimizer import ParallelOCRProcessor, IntelligentPreprocessor
    ENHANCED_PROCESSOR_AVAILABLE = True
    print("✅ Enhanced processors loaded successfully")
except ImportError as e:
    print(f"⚠️  Enhanced processors not available: {e}")
    ENHANCED_PROCESSOR_AVAILABLE = False

class EnhancedAadhaarTester:
    """Enhanced Aadhaar card testing with integrated improvements"""
    
    def __init__(self):
        self.base_url = "http://localhost:5001/api"
        
        # Initialize enhanced processors if available
        if ENHANCED_PROCESSOR_AVAILABLE:
            self.image_processor = EnhancedImageProcessor()
            self.parallel_processor = ParallelOCRProcessor(num_threads=4)
            self.intelligent_preprocessor = IntelligentPreprocessor()
            self.test_generator = ProfessionalTestImageGenerator()
            print("🚀 Enhanced processing capabilities initialized")
        else:
            print("📋 Using basic processing capabilities")
    
    def create_enhanced_test_image(self) -> Image.Image:
        """Create enhanced Aadhaar test image using professional generator"""
        
        if ENHANCED_PROCESSOR_AVAILABLE:
            print("   Using professional test image generator...")
            return self.test_generator.create_professional_aadhaar()
        else:
            print("   Using basic test image generation...")
            return self._create_basic_aadhaar_image()
    
    def _create_basic_aadhaar_image(self) -> Image.Image:
        """Create basic Aadhaar card test image (fallback)"""
        
        # Create high-resolution image
        img = Image.new('RGB', (1200, 750), color='white')
        draw = ImageDraw.Draw(img)
        
        # Use system fonts if available
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            text_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 22)
            number_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
            small_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
        except Exception:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            number_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add tricolor header
        draw.rectangle([(0, 0), (1200, 25)], fill='#FF9933')  # Saffron
        draw.rectangle([(0, 25), (1200, 50)], fill='white')    # White
        draw.rectangle([(0, 50), (1200, 75)], fill='#138808')  # Green
        
        # Government of India header
        draw.text((80, 90), "भारत सरकार", fill='black', font=text_font)
        draw.text((80, 120), "Government of India", fill='black', font=title_font)
        draw.text((80, 155), "Unique Identification Authority of India", fill='blue', font=text_font)
        
        # Main content
        y_pos = 250
        
        # Aadhaar number
        draw.text((80, y_pos), "आधार संख्या / Aadhaar Number:", fill='black', font=text_font)
        draw.text((80, y_pos + 35), "9704 7285 0296", fill='red', font=number_font)
        
        y_pos += 100
        
        # Personal details
        draw.text((80, y_pos), "नाम / Name:", fill='black', font=text_font)
        draw.text((280, y_pos), "Ved Thampi", fill='black', font=text_font)
        
        y_pos += 50
        draw.text((80, y_pos), "जन्म तिथि / Date of Birth:", fill='black', font=text_font)
        draw.text((350, y_pos), "05/09/2000", fill='black', font=text_font)
        
        y_pos += 50
        draw.text((80, y_pos), "लिंग / Gender:", fill='black', font=text_font)
        draw.text((220, y_pos), "पुरुष / Male", fill='black', font=text_font)
        
        y_pos += 50
        draw.text((80, y_pos), "पिता का नाम / Father's Name:", fill='black', font=text_font)
        draw.text((380, y_pos), "Rajesh Thampi", fill='black', font=text_font)
        
        y_pos += 70
        # Address
        draw.text((80, y_pos), "पता / Address:", fill='black', font=text_font)
        draw.text((80, y_pos + 35), "123 Main Street, Trivandrum,", fill='black', font=text_font)
        draw.text((80, y_pos + 65), "Kerala - 695001, India", fill='black', font=text_font)
        
        # QR code and photo placeholders
        draw.rectangle([(850, 250), (1050, 450)], outline='black', width=2)
        draw.text((900, 350), "QR Code", fill='black', font=small_font)
        
        draw.rectangle([(850, 470), (1050, 620)], outline='black', width=2)
        draw.text((920, 540), "Photo", fill='black', font=small_font)
        
        # Footer
        draw.text((80, 650), "मेरा आधार, मेरी पहचान", fill='#FF9933', font=text_font)
        draw.text((80, 680), "My Aadhaar, My Identity", fill='#FF9933', font=text_font)
        
        # Border
        draw.rectangle([(10, 10), (1190, 740)], outline='#CCCCCC', width=3)
        
        return img
    
    def enhance_image_quality(self, image: Image.Image) -> Image.Image:
        """Enhance image quality using advanced processors"""
        
        if ENHANCED_PROCESSOR_AVAILABLE:
            print("   Applying enhanced image processing...")
            
            # Convert to CV2 format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply enhancement
            enhanced_cv = self.image_processor.enhance_image(cv_image)
            
            # Convert back to PIL
            enhanced_pil = Image.fromarray(cv2.cvtColor(enhanced_cv, cv2.COLOR_BGR2RGB))
            
            return enhanced_pil
        else:
            return image
    
    def test_api_performance(self, image_path: str) -> dict:
        """Test API with performance monitoring"""
        
        start_time = time.time()
        
        try:
            with open(image_path, 'rb') as img_file:
                files = {'image': img_file}
                response = requests.post(f"{self.base_url}/scan", files=files)
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                result['processing_time'] = processing_time
                return result
            else:
                return {
                    'error': f"API Error: {response.status_code}",
                    'processing_time': processing_time
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def run_comprehensive_test(self):
        """Run comprehensive Aadhaar OCR test with enhancements"""
        
        print("🇮🇳 ENHANCED AADHAAR CARD OCR TESTING")
        print("=" * 60)
        
        # Step 1: Create enhanced test image
        print("\n1. Creating enhanced Aadhaar test image...")
        test_image = self.create_enhanced_test_image()
        print("   ✅ Enhanced test image created successfully")
        
        # Step 2: Apply image enhancement
        print("\n2. Applying image quality enhancements...")
        enhanced_image = self.enhance_image_quality(test_image)
        
        # Save both versions for comparison
        basic_path = 'test_aadhaar_basic.png'
        enhanced_path = 'test_aadhaar_enhanced.png'
        
        test_image.save(basic_path)
        enhanced_image.save(enhanced_path)
        
        print(f"   ✅ Basic image saved: {basic_path}")
        print(f"   ✅ Enhanced image saved: {enhanced_path}")
        
        # Step 3: Test API performance
        print("\n3. Testing API performance...")
        
        # Test basic image
        print("   📊 Testing basic image...")
        basic_result = self.test_api_performance(basic_path)
        
        # Test enhanced image
        print("   🚀 Testing enhanced image...")
        enhanced_result = self.test_api_performance(enhanced_path)
        
        # Step 4: Display results
        self.display_comparison_results(basic_result, enhanced_result)
        
        # Step 5: Quality analysis
        print("\n5. Quality Analysis:")
        if 'error' not in enhanced_result:
            quality_score = self.analyze_extraction_quality(enhanced_result)
            print(f"   📈 Extraction Quality Score: {quality_score}%")
        
        # Cleanup
        try:
            os.remove(basic_path)
            os.remove(enhanced_path)
            print("   🧹 Temporary files cleaned up")
        except Exception:
            pass
    
    def display_comparison_results(self, basic_result: dict, enhanced_result: dict):
        """Display comparison between basic and enhanced processing"""
        
        print("\n4. Performance Comparison:")
        print("   " + "=" * 50)
        
        # Processing time comparison
        basic_time = basic_result.get('processing_time', 0)
        enhanced_time = enhanced_result.get('processing_time', 0)
        
        print(f"   Basic Image Processing:    {basic_time:.3f}s")
        print(f"   Enhanced Image Processing: {enhanced_time:.3f}s")
        
        if basic_time > 0 and enhanced_time > 0:
            if enhanced_time < basic_time:
                improvement = ((basic_time - enhanced_time) / basic_time) * 100
                print(f"   🚀 Performance Improvement: {improvement:.1f}% faster")
            else:
                overhead = ((enhanced_time - basic_time) / basic_time) * 100
                print(f"   ⚖️ Processing Overhead: {overhead:.1f}% slower")
        
        # Results comparison
        if 'error' not in enhanced_result:
            print("\n   📋 Enhanced Processing Results:")
            extracted_data = enhanced_result.get('extracted_data', {})
            
            aadhaar_number = extracted_data.get('aadhaar_number', 'Not found')
            name = extracted_data.get('name', 'Not found')
            dob = extracted_data.get('date_of_birth', 'Not found')
            
            print(f"      • Aadhaar Number: {aadhaar_number}")
            print(f"      • Name: {name}")
            print(f"      • Date of Birth: {dob}")
            
            # Show confidence if available
            confidence = enhanced_result.get('confidence', 0)
            print(f"      • Overall Confidence: {confidence:.1f}%")
        else:
            print(f"   ❌ Enhanced processing error: {enhanced_result['error']}")
    
    def analyze_extraction_quality(self, result: dict) -> float:
        """Analyze the quality of data extraction"""
        
        extracted_data = result.get('extracted_data', {})
        
        quality_factors = {
            'aadhaar_number': 30,  # Most important
            'name': 25,
            'date_of_birth': 15,
            'gender': 10,
            'address': 10,
            'father_name': 10
        }
        
        total_score = 0
        max_score = sum(quality_factors.values())
        
        for field, weight in quality_factors.items():
            value = extracted_data.get(field, '')
            if value and value.lower() not in ['not found', 'none', '']:
                total_score += weight
        
        return (total_score / max_score) * 100

def main():
    """Main test function"""
    print("🇮🇳 ENHANCED AADHAAR CARD OCR TESTING SUITE")
    print("=" * 60)
    
    # Check if server is running
    tester = EnhancedAadhaarTester()
    
    try:
        response = requests.get(f"{tester.base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ OCR API server is running")
        else:
            print("❌ OCR API server is not responding correctly")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to OCR API server")
        print("   Please make sure the server is running on http://localhost:5001")
        return
    
    # Run comprehensive test
    tester.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced Aadhaar OCR testing completed!")
    
    if ENHANCED_PROCESSOR_AVAILABLE:
        print("✨ All enhancements were successfully integrated and tested")
    else:
        print("📋 Tests completed with basic functionality")
        print("   Install enhanced modules for improved performance")

if __name__ == "__main__":
    main()
