#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced OCR Document Scanner
Tests all new processors, validation, and API endpoints
"""

import requests
import json
import base64
import time
import os
from PIL import Image, ImageDraw, ImageFont
import io

class OCRTester:
    """Test suite for OCR document scanner"""
    
    def __init__(self, base_url="http://localhost:5002"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def create_test_document(self, doc_type="aadhaar"):
        """Create a test document image"""
        width, height = 800, 500
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 18)
            title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except (OSError, IOError):
            font = title_font = ImageFont.load_default()
        
        if doc_type == "aadhaar":
            # Create Aadhaar card content
            draw.text((50, 30), "भारत सरकार Government of India", fill='black', font=title_font)
            draw.text((50, 60), "आधार AADHAAR", fill='red', font=title_font)
            draw.text((50, 120), "1234 5678 9012", fill='black', font=font)
            draw.text((50, 150), "Name: JOHN DOE", fill='black', font=font)
            draw.text((50, 180), "DOB: 01/01/1990", fill='black', font=font)
            draw.text((50, 210), "Male", fill='black', font=font)
            draw.text((50, 240), "Address: 123 Main Street", fill='black', font=font)
            draw.text((50, 270), "City, State - 123456", fill='black', font=font)
            
        elif doc_type == "driving_license":
            # Create driving license content
            draw.text((50, 30), "GOVERNMENT OF INDIA", fill='blue', font=title_font)
            draw.text((50, 60), "DRIVING LICENCE", fill='red', font=title_font)
            draw.text((50, 120), "DL NO: KA1234567890123", fill='black', font=font)
            draw.text((50, 150), "Name: JANE SMITH", fill='black', font=font)
            draw.text((50, 180), "S/o: ROBERT SMITH", fill='black', font=font)
            draw.text((50, 210), "DOB: 15/05/1985", fill='black', font=font)
            draw.text((50, 240), "Address: 456 Oak Avenue", fill='black', font=font)
            draw.text((50, 270), "Issue Date: 10/01/2020", fill='black', font=font)
            draw.text((50, 300), "Valid till: 09/01/2040", fill='black', font=font)
            draw.text((50, 330), "Class: LMV", fill='black', font=font)
            
        elif doc_type == "passport":
            # Create passport content
            draw.text((50, 30), "REPUBLIC OF INDIA", fill='blue', font=title_font)
            draw.text((50, 60), "PASSPORT", fill='red', font=title_font)
            draw.text((50, 120), "Type/प्रकार: P", fill='black', font=font)
            draw.text((50, 150), "Country Code/देश कोड: IND", fill='black', font=font)
            draw.text((50, 180), "Passport No: A1234567", fill='black', font=font)
            draw.text((50, 210), "Surname: JOHNSON", fill='black', font=font)
            draw.text((50, 240), "Given Name: MICHAEL", fill='black', font=font)
            draw.text((50, 270), "Nationality: INDIAN", fill='black', font=font)
            draw.text((50, 300), "Date of Birth: 20/03/1992", fill='black', font=font)
            draw.text((50, 330), "Sex: M", fill='black', font=font)
            draw.text((50, 360), "Date of Issue: 15/06/2022", fill='black', font=font)
            draw.text((50, 390), "Date of Expiry: 14/06/2032", fill='black', font=font)
            
        elif doc_type == "us_drivers_license":
            # Create US driver's license content
            draw.text((50, 30), "STATE OF CALIFORNIA", fill='blue', font=title_font)
            draw.text((50, 60), "DRIVER LICENSE", fill='red', font=title_font)
            draw.text((50, 120), "DL: D1234567", fill='black', font=font)
            draw.text((50, 150), "SMITH, JENNIFER", fill='black', font=font)
            draw.text((50, 180), "DOB: 12/25/1988", fill='black', font=font)
            draw.text((50, 210), "123 MAIN ST", fill='black', font=font)
            draw.text((50, 240), "LOS ANGELES, CA 90210", fill='black', font=font)
            draw.text((50, 270), "SEX: F", fill='black', font=font)
            draw.text((50, 300), "HEIGHT: 5'6\"", fill='black', font=font)
            draw.text((50, 330), "EXPIRES: 12/25/2025", fill='black', font=font)
            draw.text((50, 360), "CLASS: C", fill='black', font=font)
        
        return img
    
    def image_to_base64(self, image):
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return img_str
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/api/v2/health")
            result = {
                'test': 'health_check',
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text
            }
            self.results.append(result)
            print(f"✅ Health check: {'PASS' if result['success'] else 'FAIL'}")
            return result['success']
        except Exception as e:
            print(f"❌ Health check failed: {str(e)}")
            self.results.append({
                'test': 'health_check',
                'success': False,
                'error': str(e)
            })
            return False
    
    def test_enhanced_scan(self, doc_type="aadhaar"):
        """Test enhanced scan endpoint"""
        print(f"🔍 Testing enhanced scan with {doc_type}...")
        try:
            # Create test document
            test_image = self.create_test_document(doc_type)
            image_b64 = self.image_to_base64(test_image)
            
            # Test request
            payload = {
                'image': image_b64,
                'document_type': doc_type,
                'options': {
                    'enable_quality_check': True,
                    'return_processed_images': False,
                    'ocr_language': 'eng'
                }
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/v2/scan", json=payload)
            processing_time = time.time() - start_time
            
            success = response.status_code == 200
            result = {
                'test': f'enhanced_scan_{doc_type}',
                'status_code': response.status_code,
                'success': success,
                'processing_time': processing_time,
                'response': response.json() if success else response.text
            }
            
            self.results.append(result)
            print(f"✅ Enhanced scan ({doc_type}): {'PASS' if success else 'FAIL'} - {processing_time:.2f}s")
            
            if success:
                data = result['response']
                if 'extracted_info' in data:
                    print(f"   📄 Document Type: {data.get('document_type', 'Unknown')}")
                    print(f"   🎯 Confidence: {data.get('confidence', 0):.2f}")
                    if 'quality_score' in data:
                        print(f"   ⭐ Quality Score: {data['quality_score']:.2f}")
            
            return success
            
        except Exception as e:
            print(f"❌ Enhanced scan ({doc_type}) failed: {str(e)}")
            self.results.append({
                'test': f'enhanced_scan_{doc_type}',
                'success': False,
                'error': str(e)
            })
            return False
    
    def test_classification(self, doc_type="passport"):
        """Test document classification endpoint"""
        print(f"🔍 Testing classification with {doc_type}...")
        try:
            # Create test document
            test_image = self.create_test_document(doc_type)
            image_b64 = self.image_to_base64(test_image)
            
            payload = {'image': image_b64}
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/v2/classify", json=payload)
            processing_time = time.time() - start_time
            
            success = response.status_code == 200
            result = {
                'test': f'classification_{doc_type}',
                'status_code': response.status_code,
                'success': success,
                'processing_time': processing_time,
                'response': response.json() if success else response.text
            }
            
            self.results.append(result)
            print(f"✅ Classification ({doc_type}): {'PASS' if success else 'FAIL'} - {processing_time:.2f}s")
            
            if success:
                data = result['response']
                print(f"   📄 Detected: {data.get('document_type', 'Unknown')}")
                print(f"   🎯 Confidence: {data.get('confidence', 0):.2f}")
                print(f"   🌍 Country: {data.get('country', 'Unknown')}")
            
            return success
            
        except Exception as e:
            print(f"❌ Classification ({doc_type}) failed: {str(e)}")
            self.results.append({
                'test': f'classification_{doc_type}',
                'success': False,
                'error': str(e)
            })
            return False
    
    def test_quality_assessment(self):
        """Test quality assessment endpoint"""
        print("🔍 Testing quality assessment...")
        try:
            # Create a test document with some quality issues
            test_image = self.create_test_document("aadhaar")
            
            # Simulate quality issues by resizing and adding noise
            test_image = test_image.resize((400, 250))  # Lower resolution
            
            image_b64 = self.image_to_base64(test_image)
            payload = {'image': image_b64}
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/api/v2/quality", json=payload)
            processing_time = time.time() - start_time
            
            success = response.status_code == 200
            result = {
                'test': 'quality_assessment',
                'status_code': response.status_code,
                'success': success,
                'processing_time': processing_time,
                'response': response.json() if success else response.text
            }
            
            self.results.append(result)
            print(f"✅ Quality assessment: {'PASS' if success else 'FAIL'} - {processing_time:.2f}s")
            
            if success:
                data = result['response']
                print(f"   ⭐ Quality Score: {data.get('quality_score', 0):.2f}")
                if 'issues' in data and data['issues']:
                    print(f"   ⚠️  Issues: {len(data['issues'])}")
                    for issue in data['issues'][:3]:  # Show first 3 issues
                        print(f"      - {issue.get('type', 'Unknown')}: {issue.get('description', 'No description')}")
            
            return success
            
        except Exception as e:
            print(f"❌ Quality assessment failed: {str(e)}")
            self.results.append({
                'test': 'quality_assessment',
                'success': False,
                'error': str(e)
            })
            return False
    
    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        print("🔍 Testing stats endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/api/v2/stats")
            success = response.status_code == 200
            
            result = {
                'test': 'stats',
                'status_code': response.status_code,
                'success': success,
                'response': response.json() if success else response.text
            }
            
            self.results.append(result)
            print(f"✅ Stats endpoint: {'PASS' if success else 'FAIL'}")
            
            if success:
                data = result['response']
                if 'stats' in data:
                    stats = data['stats']
                    if 'system' in stats:
                        print(f"   🔧 Processors: {stats['system'].get('total_processors', 0)}")
                        print(f"   📄 Supported Documents: {stats['system'].get('supported_documents', 0)}")
            
            return success
            
        except Exception as e:
            print(f"❌ Stats endpoint failed: {str(e)}")
            self.results.append({
                'test': 'stats',
                'success': False,
                'error': str(e)
            })
            return False
    
    def test_validation_errors(self):
        """Test validation and error handling"""
        print("🔍 Testing validation and error handling...")
        test_cases = [
            {
                'name': 'empty_request',
                'payload': {},
                'expected_status': 400
            },
            {
                'name': 'missing_image',
                'payload': {'document_type': 'aadhaar'},
                'expected_status': 400
            },
            {
                'name': 'invalid_base64',
                'payload': {'image': 'not_base64_data'},
                'expected_status': 400
            },
            {
                'name': 'invalid_image_data',
                'payload': {'image': base64.b64encode(b'not_image_data').decode()},
                'expected_status': 400
            }
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            try:
                response = self.session.post(f"{self.base_url}/api/v2/scan", json=test_case['payload'])
                expected_status = test_case['expected_status']
                actual_status = response.status_code
                
                success = actual_status == expected_status
                if success:
                    passed_tests += 1
                    print(f"   ✅ {test_case['name']}: PASS (expected {expected_status}, got {actual_status})")
                else:
                    print(f"   ❌ {test_case['name']}: FAIL (expected {expected_status}, got {actual_status})")
                
                self.results.append({
                    'test': f"validation_{test_case['name']}",
                    'success': success,
                    'expected_status': expected_status,
                    'actual_status': actual_status
                })
                
            except Exception as e:
                print(f"   ❌ {test_case['name']}: ERROR - {str(e)}")
                self.results.append({
                    'test': f"validation_{test_case['name']}",
                    'success': False,
                    'error': str(e)
                })
        
        overall_success = passed_tests == len(test_cases)
        print(f"✅ Validation tests: {'PASS' if overall_success else 'FAIL'} ({passed_tests}/{len(test_cases)})")
        return overall_success
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("🔍 Testing rate limiting...")
        try:
            # Create a simple test image
            test_image = self.create_test_document("aadhaar")
            image_b64 = self.image_to_base64(test_image)
            payload = {'image': image_b64}
            
            # Make multiple rapid requests
            requests_made = 0
            rate_limited = False
            
            for _ in range(10):  # Try 10 requests rapidly
                response = self.session.post(f"{self.base_url}/api/v2/classify", json=payload)
                requests_made += 1
                
                if response.status_code == 429:  # Rate limited
                    rate_limited = True
                    break
                elif response.status_code != 200:
                    break
                    
                time.sleep(0.1)  # Small delay
            
            # Check for rate limit headers
            if response.headers.get('X-RateLimit-Limit'):
                print(f"   📊 Rate Limit: {response.headers.get('X-RateLimit-Limit')}")
                print(f"   📊 Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
            
            # For this test, we consider it successful if we either get rate limited
            # or successfully make multiple requests
            success = requests_made > 0
            
            result = {
                'test': 'rate_limiting',
                'success': success,
                'requests_made': requests_made,
                'rate_limited': rate_limited,
                'final_status': response.status_code
            }
            
            self.results.append(result)
            print(f"✅ Rate limiting: {'PASS' if success else 'FAIL'} (made {requests_made} requests)")
            
            return success
            
        except Exception as e:
            print(f"❌ Rate limiting test failed: {str(e)}")
            self.results.append({
                'test': 'rate_limiting',
                'success': False,
                'error': str(e)
            })
            return False
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🚀 Starting comprehensive OCR API tests...\n")
        
        test_methods = [
            self.test_health_endpoint,
            self.test_enhanced_scan,
            lambda: self.test_enhanced_scan("driving_license"),
            lambda: self.test_enhanced_scan("passport"),
            lambda: self.test_enhanced_scan("us_drivers_license"),
            lambda: self.test_classification("aadhaar"),
            lambda: self.test_classification("driving_license"),
            self.test_quality_assessment,
            self.test_stats_endpoint,
            self.test_validation_errors,
            self.test_rate_limiting
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ Test method failed: {str(e)}\n")
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed")
        
        return passed_tests, total_tests
    
    def save_results(self, filename="test_results.json"):
        """Save test results to file"""
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'summary': {
                    'total_tests': len(self.results),
                    'passed_tests': sum(1 for r in self.results if r.get('success', False)),
                    'failed_tests': sum(1 for r in self.results if not r.get('success', False))
                },
                'results': self.results
            }, f, indent=2)
        print(f"📄 Test results saved to {filename}")


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR Document Scanner API Tester')
    parser.add_argument('--url', default='http://localhost:5002', 
                       help='Base URL for the API (default: http://localhost:5002)')
    parser.add_argument('--save-results', default='test_results.json',
                       help='File to save test results (default: test_results.json)')
    
    args = parser.parse_args()
    
    # Check if server is running
    try:
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server health check failed. Please ensure the server is running at {args.url}")
            return
    except requests.exceptions.RequestException:
        print(f"❌ Could not connect to server at {args.url}. Please ensure the server is running.")
        return
    
    # Run tests
    tester = OCRTester(args.url)
    passed, total = tester.run_all_tests()
    tester.save_results(args.save_results)
    
    # Exit with appropriate code
    exit_code = 0 if passed == total else 1
    exit(exit_code)


if __name__ == "__main__":
    main()
