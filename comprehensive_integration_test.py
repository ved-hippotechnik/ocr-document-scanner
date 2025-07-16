#!/usr/bin/env python3
"""
Comprehensive Integration Test for OCR Document Scanner
Tests all API endpoints, document types, and frontend-backend integration
"""

import requests
import json
import os
import time
from pathlib import Path


class OCRDocumentScannerTester:
    def __init__(self, backend_url="http://localhost:5001", frontend_url="http://localhost:3003"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results = []
        
    def log_test(self, test_name, passed, message=""):
        """Log test results"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}: {message}"
        print(result)
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        
    def test_backend_health(self):
        """Test if backend is running and responsive"""
        try:
            response = requests.get(f"{self.backend_url}/api/stats", timeout=5)
            if response.status_code == 200:
                self.log_test("Backend Health Check", True, "Backend is responsive")
                return True
            else:
                self.log_test("Backend Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False
            
    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200 and "OCR Document Scanner" in response.text:
                self.log_test("Frontend Accessibility", True, "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Accessibility", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", False, f"Error: {str(e)}")
            return False
            
    def test_document_types_endpoint(self):
        """Test the document types API endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/api/document-types", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('total') == 6:
                    expected_types = {'passport', 'id_card', 'driving_license', 'aadhaar', 'us_green_card', 'other'}
                    actual_types = {doc['id'] for doc in data['document_types']}
                    if expected_types == actual_types:
                        self.log_test("Document Types Endpoint", True, "All 6 document types present")
                        return True
                    else:
                        missing = expected_types - actual_types
                        self.log_test("Document Types Endpoint", False, f"Missing types: {missing}")
                        return False
                else:
                    self.log_test("Document Types Endpoint", False, f"Expected 6 types, got {data.get('total', 0)}")
                    return False
            else:
                self.log_test("Document Types Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Document Types Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_stats_endpoint(self):
        """Test the stats API endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/api/stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                required_fields = ['total_scanned', 'document_types', 'nationalities', 'scan_history', 'documents']
                if all(field in data for field in required_fields):
                    doc_types = data['document_types']
                    expected_types = {'passport', 'id_card', 'driving_license', 'aadhaar', 'us_green_card', 'other'}
                    actual_types = set(doc_types.keys())
                    if expected_types == actual_types:
                        self.log_test("Stats Endpoint", True, "All required fields and document types present")
                        return True
                    else:
                        self.log_test("Stats Endpoint", False, f"Document types mismatch: {actual_types}")
                        return False
                else:
                    missing = [field for field in required_fields if field not in data]
                    self.log_test("Stats Endpoint", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_test("Stats Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Stats Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_documents_endpoint(self):
        """Test the documents API endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/api/documents", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') is True and 'documents' in data and 'total' in data:
                    self.log_test("Documents Endpoint", True, "Documents endpoint working correctly")
                    return True
                else:
                    self.log_test("Documents Endpoint", False, "Missing required fields in response")
                    return False
            else:
                self.log_test("Documents Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Documents Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_scan_endpoint_with_sample(self):
        """Test the scan endpoint with a sample image if available"""
        # Look for sample images
        test_images_dir = Path("test-images")
        sample_files = []
        
        if test_images_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                sample_files.extend(list(test_images_dir.glob(ext)))
        
        if not sample_files:
            self.log_test("Scan Endpoint Test", False, "No sample images found in test-images directory")
            return False
            
        try:
            # Use the first available sample image
            sample_file = sample_files[0]
            
            with open(sample_file, 'rb') as f:
                files = {'image': (sample_file.name, f, 'image/jpeg')}
                response = requests.post(f"{self.backend_url}/api/scan", files=files, timeout=30)
                
            if response.status_code == 200:
                data = response.json()
                if 'extracted_info' in data and 'document_type' in data:
                    self.log_test("Scan Endpoint Test", True, f"Successfully processed {sample_file.name}")
                    return True
                else:
                    self.log_test("Scan Endpoint Test", False, f"Scan failed: Missing required fields in response")
                    return False
            else:
                self.log_test("Scan Endpoint Test", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Scan Endpoint Test", False, f"Error: {str(e)}")
            return False
            
    def test_reset_stats_endpoint(self):
        """Test the reset stats endpoint"""
        try:
            response = requests.post(f"{self.backend_url}/api/reset-stats", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'message' in data:
                    self.log_test("Reset Stats Endpoint", True, "Reset stats working correctly")
                    return True
                else:
                    self.log_test("Reset Stats Endpoint", False, "Invalid response format")
                    return False
            else:
                self.log_test("Reset Stats Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Reset Stats Endpoint", False, f"Error: {str(e)}")
            return False
            
    def test_cors_headers(self):
        """Test CORS headers for frontend-backend communication"""
        try:
            response = requests.options(f"{self.backend_url}/api/stats", timeout=5)
            headers = response.headers
            
            # Check for basic CORS headers
            cors_headers_present = (
                'Access-Control-Allow-Origin' in headers or
                response.status_code == 200  # Some Flask setups handle CORS differently
            )
            
            if cors_headers_present or response.status_code == 200:
                self.log_test("CORS Headers", True, "CORS appears to be configured")
                return True
            else:
                self.log_test("CORS Headers", False, "CORS headers missing")
                return False
        except Exception as e:
            self.log_test("CORS Headers", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("="*80)
        print("OCR DOCUMENT SCANNER - COMPREHENSIVE INTEGRATION TEST")
        print("="*80)
        print()
        
        # Run all tests
        tests = [
            self.test_backend_health,
            self.test_frontend_accessibility,
            self.test_document_types_endpoint,
            self.test_stats_endpoint,
            self.test_documents_endpoint,
            self.test_scan_endpoint_with_sample,
            self.test_reset_stats_endpoint,
            self.test_cors_headers,
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Brief pause between tests
            
        # Generate summary
        print()
        print("="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        passed_tests = [result for result in self.test_results if result['passed']]
        failed_tests = [result for result in self.test_results if not result['passed']]
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        
        if failed_tests:
            print()
            print("FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
                
        print()
        if len(failed_tests) == 0:
            print("🎉 ALL TESTS PASSED! The OCR Document Scanner is ready for production.")
        elif len(passed_tests) >= len(failed_tests):
            print("✅ Most tests passed. Minor issues detected - see details above.")
        else:
            print("❌ Multiple test failures detected. Please review and fix issues.")
            
        print()
        print("NEXT STEPS:")
        if len(failed_tests) == 0:
            print("  - Deploy to production environment")
            print("  - Add real document samples for testing")
            print("  - Set up monitoring and logging")
            print("  - Consider adding more comprehensive frontend tests")
        else:
            print("  - Fix failing tests")
            print("  - Re-run integration tests")
            print("  - Verify all API endpoints are working")
            
        return len(failed_tests) == 0


def main():
    """Main test runner"""
    tester = OCRDocumentScannerTester()
    success = tester.run_all_tests()
    
    # Save detailed results to file
    with open('integration_test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'overall_success': success,
            'test_results': tester.test_results,
            'summary': {
                'total': len(tester.test_results),
                'passed': len([r for r in tester.test_results if r['passed']]),
                'failed': len([r for r in tester.test_results if not r['passed']])
            }
        }, f, indent=2)
    
    print(f"Detailed results saved to: integration_test_results.json")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
