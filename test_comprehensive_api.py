#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Enhanced OCR Document Scanner
Tests all new endpoints, database integration, and async processing
"""

import requests
import json
import time
import base64
import os
import sys
from datetime import datetime

class EnhancedOCRTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.session_id = f"test-session-{int(time.time())}"
        
    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results with color coding"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status} {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'response_data': response_data,
            'timestamp': timestamp
        })
    
    def create_test_image_data(self):
        """Create a simple test image for processing"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a document-like image
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add document content
            sample_text = [
                "SAMPLE DOCUMENT",
                "Full Name: John Michael Doe",
                "Document ID: 123456789",
                "Date of Birth: 15/01/1990",
                "Issue Date: 30/06/2025",
                "Expiry Date: 30/06/2030",
                "This is a test document for OCR processing"
            ]
            
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            y_position = 80
            for line in sample_text:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 60
            
            # Add a simple border
            draw.rectangle([(10, 10), (790, 590)], outline='black', width=2)
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            return img_data
            
        except ImportError:
            print("⚠️ PIL not available, using minimal test image")
            # Minimal base64 JPEG (1x1 pixel)
            return "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
    
    def test_service_health(self):
        """Test basic service health and connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            self.log_test(
                "Service Health Check",
                success,
                f"HTTP {response.status_code} - {data}",
                data
            )
            return success
        except requests.exceptions.RequestException as e:
            self.log_test("Service Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_processors_list(self):
        """Test available processors endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/processors", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            processor_count = data.get('total_processors', 0) if data else 0
            supported_docs = data.get('supported_documents', []) if data else []
            
            self.log_test(
                "Processors List",
                success,
                f"HTTP {response.status_code} - {processor_count} processors, {len(supported_docs)} document types",
                data
            )
            return success
        except Exception as e:
            self.log_test("Processors List", False, f"Error: {str(e)}")
            return False
    
    def test_v2_stats(self):
        """Test V2 statistics endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v2/stats", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            self.log_test(
                "V2 Stats Endpoint",
                success,
                f"HTTP {response.status_code}",
                data
            )
            return success
        except Exception as e:
            self.log_test("V2 Stats Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_analytics_dashboard(self):
        """Test analytics dashboard endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/analytics?days=7", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else None
            
            if success and data:
                total_scans = data.get('summary', {}).get('total_scans', 0)
                success_rate = data.get('summary', {}).get('success_rate', 0)
                message = f"HTTP {response.status_code} - {total_scans} scans, {success_rate:.1f}% success rate"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Analytics Dashboard", success, message, data)
            return success
        except Exception as e:
            self.log_test("Analytics Dashboard", False, f"Error: {str(e)}")
            return False
    
    def test_document_processing(self):
        """Test enhanced document processing"""
        try:
            image_data = self.create_test_image_data()
            
            payload = {
                "image_data": image_data,
                "document_type": "passport",
                "confidence_threshold": 0.5
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Session-ID': self.session_id
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v2/scan",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            success = response.status_code in [200, 202]
            data = response.json() if response.content else None
            
            if success and data:
                doc_type = data.get('document_type', 'unknown')
                confidence = data.get('confidence', 0)
                processing_time = data.get('processing_time', 0)
                message = f"HTTP {response.status_code} - {doc_type} detected, {confidence:.2f} confidence, {processing_time}s"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Document Processing", success, message, data)
            return success, data
            
        except Exception as e:
            self.log_test("Document Processing", False, f"Error: {str(e)}")
            return False, None
    
    def test_async_processing(self):
        """Test asynchronous document processing"""
        try:
            image_data = self.create_test_image_data()
            
            payload = {
                "image_data": image_data,
                "document_type": "emirates_id",
                "options": {
                    "session_id": f"{self.session_id}-async"
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-Session-ID': f"{self.session_id}-async"
            }
            
            # Start async task
            response = self.session.post(
                f"{self.base_url}/api/v2/async/scan",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 202:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    # Wait and check status
                    time.sleep(3)
                    status_response = self.session.get(
                        f"{self.base_url}/api/v2/async/status/{task_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        task_state = status_data.get('state', 'UNKNOWN')
                        progress = status_data.get('progress', 0)
                        
                        self.log_test(
                            "Async Processing",
                            True,
                            f"Task {task_id} created, State: {task_state}, Progress: {progress}%",
                            {'task_data': data, 'status_data': status_data}
                        )
                        return True
                    else:
                        self.log_test("Async Processing", False, f"Status check failed: HTTP {status_response.status_code}")
                        return False
                else:
                    self.log_test("Async Processing", False, "No task_id returned")
                    return False
            else:
                self.log_test("Async Processing", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Async Processing", False, f"Error: {str(e)}")
            return False
    
    def test_quality_assessment(self):
        """Test image quality assessment"""
        try:
            image_data = self.create_test_image_data()
            
            payload = {
                "image_data": image_data
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v2/quality",
                json=payload,
                timeout=15
            )
            
            success = response.status_code == 200
            data = response.json() if response.content else None
            
            if success and data:
                quality_score = data.get('quality_score', 0)
                issues = data.get('issues', [])
                message = f"HTTP {response.status_code} - Quality: {quality_score:.2f}, Issues: {len(issues)}"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Quality Assessment", success, message, data)
            return success
            
        except Exception as e:
            self.log_test("Quality Assessment", False, f"Error: {str(e)}")
            return False
    
    def test_batch_processing(self):
        """Test batch document processing"""
        try:
            image_data = self.create_test_image_data()
            
            # Create a small batch
            batch_data = [
                {
                    "image_data": image_data,
                    "document_type": "passport",
                    "filename": "test_doc_1.jpg"
                },
                {
                    "image_data": image_data,
                    "document_type": "emirates_id",
                    "filename": "test_doc_2.jpg"
                }
            ]
            
            payload = {
                "documents": batch_data
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v2/async/batch",
                json=payload,
                timeout=15
            )
            
            success = response.status_code == 202
            data = response.json() if response.content else None
            
            if success and data:
                batch_id = data.get('batch_id')
                total_docs = data.get('total_documents', 0)
                message = f"HTTP {response.status_code} - Batch {batch_id} created with {total_docs} documents"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Batch Processing", success, message, data)
            return success
            
        except Exception as e:
            self.log_test("Batch Processing", False, f"Error: {str(e)}")
            return False
    
    def test_scan_history(self):
        """Test scan history retrieval"""
        try:
            response = self.session.get(
                f"{self.base_url}/analytics/scan-history?per_page=10&page=1",
                timeout=10
            )
            
            success = response.status_code == 200
            data = response.json() if response.content else None
            
            if success and data:
                scans = data.get('scans', [])
                pagination = data.get('pagination', {})
                total = pagination.get('total', 0)
                message = f"HTTP {response.status_code} - {len(scans)} scans returned, {total} total"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Scan History", success, message, data)
            return success
            
        except Exception as e:
            self.log_test("Scan History", False, f"Error: {str(e)}")
            return False
    
    def test_document_statistics(self):
        """Test document type statistics"""
        try:
            response = self.session.get(f"{self.base_url}/analytics/document-stats", timeout=10)
            
            success = response.status_code == 200
            data = response.json() if response.content else None
            
            if success and data:
                doc_types = data.get('document_types', [])
                message = f"HTTP {response.status_code} - {len(doc_types)} document types tracked"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_test("Document Statistics", success, message, data)
            return success
            
        except Exception as e:
            self.log_test("Document Statistics", False, f"Error: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🧪 Enhanced OCR Document Scanner - Comprehensive API Test Suite")
        print("=" * 70)
        print(f"Test Session ID: {self.session_id}")
        print(f"Target URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Phase 1: Basic Connectivity
        print("📡 Phase 1: Basic Connectivity & Health Checks")
        print("-" * 50)
        health_ok = self.test_service_health()
        if not health_ok:
            print("\n❌ Service is not responding. Deployment may have failed.")
            return False
        
        processors_ok = self.test_processors_list()
        stats_ok = self.test_v2_stats()
        
        # Phase 2: Core Functionality
        print("\n⚙️ Phase 2: Core Processing & Quality Assessment")
        print("-" * 50)
        processing_ok, _ = self.test_document_processing()
        quality_ok = self.test_quality_assessment()
        
        # Phase 3: Advanced Features
        print("\n🚀 Phase 3: Advanced Features (Async, Batch)")
        print("-" * 50)
        async_ok = self.test_async_processing()
        batch_ok = self.test_batch_processing()
        
        # Phase 4: Analytics & Database
        print("\n📊 Phase 4: Analytics & Database Integration")
        print("-" * 50)
        analytics_ok = self.test_analytics_dashboard()
        history_ok = self.test_scan_history()
        stats_db_ok = self.test_document_statistics()
        
        # Test Summary
        print("\n📋 Test Results Summary")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests Run: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests Details:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        # Critical services check
        critical_services = [health_ok, processors_ok, processing_ok]
        critical_passed = sum(critical_services)
        
        if critical_passed == len(critical_services):
            print(f"\n🎉 All critical services are operational!")
        else:
            print(f"\n⚠️ Some critical services failed - deployment needs attention")
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return failed_tests == 0
    
    def save_detailed_report(self, filename="comprehensive_test_report.json"):
        """Save detailed test report to file"""
        report = {
            'test_session': {
                'session_id': self.session_id,
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['success']),
                'failed': sum(1 for r in self.test_results if not r['success']),
                'success_rate': (sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100) if self.test_results else 0
            },
            'test_results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Detailed test report saved to: {filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive OCR API Testing Suite')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL for the API (default: http://localhost:5000)')
    parser.add_argument('--report', default='comprehensive_test_report.json', help='Output file for detailed test report')
    parser.add_argument('--timeout', type=int, default=60, help='Global timeout for tests in seconds')
    
    args = parser.parse_args()
    
    # Set requests timeout
    import socket
    socket.setdefaulttimeout(args.timeout)
    
    tester = EnhancedOCRTester(args.url)
    
    try:
        success = tester.run_comprehensive_tests()
        tester.save_detailed_report(args.report)
        
        if success:
            print("\n🎉 All tests passed! Deployment is successful and ready for production.")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed. Please check the deployment.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite encountered an error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
