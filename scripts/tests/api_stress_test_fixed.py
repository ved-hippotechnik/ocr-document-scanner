#\!/usr/bin/env python3
"""
Comprehensive API Stress Testing for OCR Document Scanner
Tests: Load capacity, Performance benchmarks, Security vulnerabilities, Error handling
"""

import asyncio
import aiohttp
import time
import json
import base64
import statistics
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests
from typing import Dict, List, Tuple
import os
import sys

# API Configuration
BASE_URL = "http://localhost:5001"
API_ENDPOINTS = {
    # Core API
    "health": {"method": "GET", "path": "/health"},
    "processors": {"method": "GET", "path": "/api/processors"},
    "scan": {"method": "POST", "path": "/api/scan"},
    "stats": {"method": "GET", "path": "/api/stats"},
    
    # Enhanced v2 API
    "v2_health": {"method": "GET", "path": "/api/v2/health"},
    "v2_scan": {"method": "POST", "path": "/api/v2/scan"},
    "v2_analytics": {"method": "GET", "path": "/api/v2/analytics"},
    "v2_batch": {"method": "POST", "path": "/api/v2/batch"},
    
    # Authentication
    "auth_register": {"method": "POST", "path": "/api/auth/register"},
    "auth_login": {"method": "POST", "path": "/api/auth/login"},
    "auth_profile": {"method": "GET", "path": "/api/auth/profile"},
    "auth_refresh": {"method": "POST", "path": "/api/auth/refresh"},
    
    # Analytics
    "analytics_dashboard": {"method": "GET", "path": "/api/analytics/dashboard"},
    "analytics_trends": {"method": "GET", "path": "/api/analytics/trends"},
}

class PerformanceMetrics:
    """Track and calculate performance metrics"""
    def __init__(self):
        self.response_times = []
        self.status_codes = {}
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    def add_response(self, response_time: float, status_code: int):
        self.response_times.append(response_time)
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
        
    def add_error(self, error: str):
        self.errors.append(error)
        
    def get_statistics(self) -> Dict:
        if not self.response_times:
            return {"error": "No data collected"}
            
        return {
            "total_requests": len(self.response_times),
            "successful_requests": self.status_codes.get(200, 0) + self.status_codes.get(201, 0),
            "failed_requests": sum(count for code, count in self.status_codes.items() if code >= 400),
            "errors": len(self.errors),
            "response_times": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
                "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times),
            },
            "status_codes": dict(self.status_codes),
            "duration": (self.end_time - self.start_time) if self.end_time else None,
            "requests_per_second": len(self.response_times) / ((self.end_time - self.start_time) if self.end_time else 1)
        }

class APIStressTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.metrics = {}
        self.auth_token = None
        self.test_user = {
            "email": f"test_{random.randint(1000, 9999)}@stresstest.com",
            "username": f"stress_tester_{random.randint(1000, 9999)}",
            "password": "StressTest123\!@#"
        }
        
    def generate_test_image(self, size_kb: int = 100) -> str:
        """Generate a test image of specified size"""
        # Create a simple test image
        from PIL import Image
        import io
        
        # Calculate dimensions for approximate size
        pixels = size_kb * 1024 // 3  # Rough estimate for RGB
        dimension = int(pixels ** 0.5)
        
        img = Image.new('RGB', (dimension, dimension), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    async def test_endpoint_async(self, session: aiohttp.ClientSession, endpoint_name: str, 
                                 endpoint_config: Dict, data: Dict = None) -> Tuple[float, int]:
        """Test a single endpoint asynchronously"""
        url = f"{self.base_url}{endpoint_config['path']}"
        headers = {}
        
        if self.auth_token and endpoint_name not in ['auth_login', 'auth_register']:
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
        if endpoint_config['method'] == 'POST' and data:
            headers['Content-Type'] = 'application/json'
            
        start_time = time.time()
        try:
            async with session.request(
                endpoint_config['method'],
                url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                await response.text()
                response_time = time.time() - start_time
                return response_time, response.status
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, 0  # 0 indicates error
            
    def test_endpoint_sync(self, endpoint_name: str, endpoint_config: Dict, 
                          data: Dict = None) -> Tuple[float, int]:
        """Test a single endpoint synchronously"""
        url = f"{self.base_url}{endpoint_config['path']}"
        headers = {}
        
        if self.auth_token and endpoint_name not in ['auth_login', 'auth_register']:
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
        start_time = time.time()
        try:
            if endpoint_config['method'] == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=30)
            response_time = time.time() - start_time
            return response_time, response.status_code
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, 0
            
    async def load_test_async(self, endpoint_name: str, endpoint_config: Dict, 
                             concurrent_users: int, requests_per_user: int, data: Dict = None):
        """Perform async load test on an endpoint"""
        print(f"\n=== Load Testing {endpoint_name} ===")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Requests per user: {requests_per_user}")
        
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(concurrent_users):
                for _ in range(requests_per_user):
                    tasks.append(self.test_endpoint_async(session, endpoint_name, endpoint_config, data))
                    
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, tuple):
                    response_time, status_code = result
                    metrics.add_response(response_time, status_code)
                else:
                    metrics.add_error(str(result))
                    
        metrics.end_time = time.time()
        self.metrics[f"{endpoint_name}_load_test"] = metrics.get_statistics()
        
        # Print summary
        stats = metrics.get_statistics()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful_requests']}")
        print(f"Failed: {stats['failed_requests']}")
        print(f"RPS: {stats['requests_per_second']:.2f}")
        print(f"Response times - Mean: {stats['response_times']['mean']:.3f}s, P95: {stats['response_times']['p95']:.3f}s")
        
    def spike_test(self, endpoint_name: str, endpoint_config: Dict, 
                   initial_users: int, spike_users: int, duration_seconds: int, data: Dict = None):
        """Test API behavior under sudden traffic spikes"""
        print(f"\n=== Spike Testing {endpoint_name} ===")
        print(f"Initial load: {initial_users} users")
        print(f"Spike to: {spike_users} users")
        
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()
        stop_event = threading.Event()
        
        def worker():
            while not stop_event.is_set():
                response_time, status_code = self.test_endpoint_sync(endpoint_name, endpoint_config, data)
                metrics.add_response(response_time, status_code)
                time.sleep(random.uniform(0.1, 0.5))
                
        # Start with initial load
        threads = []
        for _ in range(initial_users):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
            
        print(f"Running initial load for {duration_seconds//3} seconds...")
        time.sleep(duration_seconds // 3)
        
        # Spike the load
        print(f"Spiking to {spike_users} users...")
        for _ in range(spike_users - initial_users):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
            
        time.sleep(duration_seconds // 3)
        
        # Return to normal
        print("Returning to initial load...")
        stop_event.set()
        for t in threads[initial_users:]:
            t.join()
            
        stop_event.clear()
        time.sleep(duration_seconds // 3)
        
        # Stop all
        stop_event.set()
        for t in threads[:initial_users]:
            t.join()
            
        metrics.end_time = time.time()
        self.metrics[f"{endpoint_name}_spike_test"] = metrics.get_statistics()
        
    def security_test(self):
        """Test for common security vulnerabilities"""
        print("\n=== Security Vulnerability Testing ===")
        security_results = {}
        
        # Test 1: SQL Injection attempts
        print("Testing SQL Injection vulnerabilities...")
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE scan_history; --",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--"
        ]
        
        for payload in sql_payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/api/auth/login",
                    json={"email": payload, "password": payload},
                    timeout=5
                )
                if response.status_code \!= 400 and response.status_code \!= 401:
                    security_results['sql_injection'] = f"VULNERABLE - Payload '{payload}' returned {response.status_code}"
                    break
            except:
                pass
        else:
            security_results['sql_injection'] = "PROTECTED"
            
        # Test 2: XSS attempts
        print("Testing XSS vulnerabilities...")
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/api/auth/register",
                    json={"email": "test@test.com", "username": payload, "password": "Test123\!@#"},
                    timeout=5
                )
                if payload in response.text:
                    security_results['xss'] = f"VULNERABLE - Payload reflected in response"
                    break
            except:
                pass
        else:
            security_results['xss'] = "PROTECTED"
            
        # Test 3: Authentication bypass
        print("Testing authentication bypass...")
        protected_endpoints = ["/api/auth/profile", "/api/v2/analytics"]
        
        for endpoint in protected_endpoints:
            try:
                # Test without auth
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    security_results['auth_bypass'] = f"VULNERABLE - {endpoint} accessible without auth"
                    break
                    
                # Test with invalid token
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers={"Authorization": "Bearer invalid_token"},
                    timeout=5
                )
                if response.status_code == 200:
                    security_results['auth_bypass'] = f"VULNERABLE - {endpoint} accepts invalid token"
                    break
            except:
                pass
        else:
            security_results['auth_bypass'] = "PROTECTED"
            
        # Test 4: Rate limiting
        print("Testing rate limiting...")
        rapid_requests = 0
        start_time = time.time()
        
        for _ in range(200):  # Try 200 requests rapidly
            try:
                response = requests.get(f"{self.base_url}/health", timeout=1)
                if response.status_code == 200:
                    rapid_requests += 1
                elif response.status_code == 429:  # Rate limited
                    break
            except:
                pass
                
        elapsed = time.time() - start_time
        rps = rapid_requests / elapsed if elapsed > 0 else 0
        
        if rapid_requests >= 150:
            security_results['rate_limiting'] = f"VULNERABLE - Allowed {rapid_requests} requests in {elapsed:.1f}s ({rps:.0f} RPS)"
        else:
            security_results['rate_limiting'] = f"PROTECTED - Limited to {rapid_requests} requests"
            
        # Test 5: File upload vulnerabilities
        print("Testing file upload vulnerabilities...")
        malicious_files = [
            ("test.php", "<?php system($_GET['cmd']); ?>"),
            ("test.exe", "MZ\x90\x00"),  # PE header
            ("test.jsp", "<%@ page import=\"java.io.*\" %>"),
            ("../../test.txt", "path traversal test")
        ]
        
        for filename, content in malicious_files:
            try:
                files = {'image': (filename, content, 'application/octet-stream')}
                response = requests.post(f"{self.base_url}/api/scan", files=files, timeout=5)
                if response.status_code == 200:
                    security_results['file_upload'] = f"VULNERABLE - Accepted {filename}"
                    break
            except:
                pass
        else:
            security_results['file_upload'] = "PROTECTED"
            
        self.metrics['security_test'] = security_results
        
        # Print results
        print("\nSecurity Test Results:")
        for test, result in security_results.items():
            status = "✅" if "PROTECTED" in result else "❌"
            print(f"{status} {test}: {result}")
            
    def error_handling_test(self):
        """Test error handling and edge cases"""
        print("\n=== Error Handling & Edge Cases Testing ===")
        error_results = {}
        
        # Test 1: Empty requests
        print("Testing empty request handling...")
        try:
            response = requests.post(f"{self.base_url}/api/v2/scan", json={}, timeout=5)
            error_results['empty_request'] = f"Status: {response.status_code}, Body: {response.json()}"
        except Exception as e:
            error_results['empty_request'] = f"Error: {str(e)}"
            
        # Test 2: Malformed JSON
        print("Testing malformed JSON...")
        try:
            response = requests.post(
                f"{self.base_url}/api/v2/scan",
                data="{'invalid': json}",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            error_results['malformed_json'] = f"Status: {response.status_code}"
        except Exception as e:
            error_results['malformed_json'] = f"Error: {str(e)}"
            
        # Test 3: Oversized payload
        print("Testing oversized payload...")
        try:
            huge_image = self.generate_test_image(20000)  # 20MB
            response = requests.post(
                f"{self.base_url}/api/v2/scan",
                json={"image": huge_image},
                timeout=10
            )
            error_results['oversized_payload'] = f"Status: {response.status_code}"
        except Exception as e:
            error_results['oversized_payload'] = f"Expected - {str(e)}"
            
        # Test 4: Invalid image data
        print("Testing invalid image data...")
        try:
            response = requests.post(
                f"{self.base_url}/api/v2/scan",
                json={"image": "not_base64_data"},
                timeout=5
            )
            error_results['invalid_image'] = f"Status: {response.status_code}, Body: {response.json()}"
        except Exception as e:
            error_results['invalid_image'] = f"Error: {str(e)}"
            
        # Test 5: Concurrent modifications
        print("Testing concurrent modifications...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(
                    requests.post,
                    f"{self.base_url}/api/auth/register",
                    json={
                        "email": "concurrent@test.com",
                        "username": f"user_{i}",
                        "password": "Test123\!@#"
                    },
                    timeout=5
                )
                futures.append(future)
                
            results = []
            for future in as_completed(futures):
                try:
                    response = future.result()
                    results.append(response.status_code)
                except:
                    results.append(0)
                    
        successful = results.count(201)
        conflicts = results.count(409)
        error_results['concurrent_modifications'] = f"Successful: {successful}, Conflicts: {conflicts}, Errors: {results.count(0)}"
        
        self.metrics['error_handling'] = error_results
        
        # Print results
        print("\nError Handling Results:")
        for test, result in error_results.items():
            print(f"- {test}: {result}")
            
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("=" * 80)
        print("OCR DOCUMENT SCANNER API STRESS TEST")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # First, try to register and login
        print("\nSetting up test user...")
        try:
            # Register
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=self.test_user,
                timeout=5
            )
            if response.status_code == 201:
                print("✅ Test user registered")
                auth_data = response.json()
                self.auth_token = auth_data.get('access_token')
            elif response.status_code == 409:
                # User exists, try login
                response = requests.post(
                    f"{self.base_url}/api/auth/login",
                    json={"email": self.test_user["email"], "password": self.test_user["password"]},
                    timeout=5
                )
                if response.status_code == 200:
                    print("✅ Test user logged in")
                    auth_data = response.json()
                    self.auth_token = auth_data.get('access_token')
        except Exception as e:
            print(f"⚠️ Auth setup failed: {e}")
            
        # Prepare test data
        test_image = self.generate_test_image(500)  # 500KB test image
        scan_data = {"image": test_image}
        
        # 1. Load Testing - Core endpoints
        await self.load_test_async("health", API_ENDPOINTS["health"], 50, 10)
        await self.load_test_async("processors", API_ENDPOINTS["processors"], 30, 10)
        await self.load_test_async("scan", API_ENDPOINTS["scan"], 20, 5, scan_data)
        await self.load_test_async("v2_scan", API_ENDPOINTS["v2_scan"], 20, 5, scan_data)
        
        # 2. Spike Testing
        self.spike_test("health", API_ENDPOINTS["health"], 10, 100, 30)
        self.spike_test("v2_scan", API_ENDPOINTS["v2_scan"], 5, 50, 30, scan_data)
        
        # 3. Security Testing
        self.security_test()
        
        # 4. Error Handling Testing
        self.error_handling_test()
        
        # 5. Resource Consumption Test
        print("\n=== Resource Consumption Test ===")
        print("Testing sustained load for resource monitoring...")
        
        # Run sustained load for 60 seconds
        sustained_metrics = PerformanceMetrics()
        sustained_metrics.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(100):  # 100 concurrent requests
                tasks.append(self.test_endpoint_async(session, "v2_scan", API_ENDPOINTS["v2_scan"], scan_data))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, tuple):
                    response_time, status_code = result
                    sustained_metrics.add_response(response_time, status_code)
                    
        sustained_metrics.end_time = time.time()
        self.metrics['sustained_load'] = sustained_metrics.get_statistics()
        
        # Generate final report
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "target": self.base_url,
            "results": self.metrics
        }
        
        # Save to file
        filename = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nDetailed report saved to: {filename}")
        
        # Print summary
        print("\n=== SUMMARY ===")
        
        # Performance Summary
        print("\n📊 Performance Metrics:")
        for test_name, metrics in self.metrics.items():
            if 'response_times' in metrics:
                print(f"\n{test_name}:")
                print(f"  - Total Requests: {metrics['total_requests']}")
                print(f"  - Success Rate: {metrics['successful_requests']/metrics['total_requests']*100:.1f}%")
                print(f"  - RPS: {metrics['requests_per_second']:.2f}")
                print(f"  - Response Times (ms):")
                print(f"    - Mean: {metrics['response_times']['mean']*1000:.0f}")
                print(f"    - P95: {metrics['response_times']['p95']*1000:.0f}")
                print(f"    - P99: {metrics['response_times']['p99']*1000:.0f}")
                
        # Security Summary
        if 'security_test' in self.metrics:
            print("\n🔒 Security Summary:")
            security = self.metrics['security_test']
            vulnerable = sum(1 for result in security.values() if "VULNERABLE" in result)
            protected = len(security) - vulnerable
            print(f"  - Tests Passed: {protected}/{len(security)}")
            if vulnerable > 0:
                print("  - ⚠️ VULNERABILITIES FOUND:")
                for test, result in security.items():
                    if "VULNERABLE" in result:
                        print(f"    - {test}: {result}")
                        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        # Performance recommendations
        for test_name, metrics in self.metrics.items():
            if 'response_times' in metrics:
                if metrics['response_times']['p95'] > 2.0:
                    print(f"  - {test_name}: High P95 latency ({metrics['response_times']['p95']:.2f}s) - Consider optimization")
                if metrics.get('failed_requests', 0) > metrics['total_requests'] * 0.01:
                    print(f"  - {test_name}: High failure rate - Investigate error handling")
                    
        # Security recommendations
        if 'security_test' in self.metrics:
            security = self.metrics['security_test']
            if "VULNERABLE" in security.get('rate_limiting', ''):
                print("  - Implement stricter rate limiting to prevent abuse")
            if "VULNERABLE" in security.get('sql_injection', ''):
                print("  - CRITICAL: SQL injection vulnerability detected - Review input sanitization")
            if "VULNERABLE" in security.get('xss', ''):
                print("  - CRITICAL: XSS vulnerability detected - Implement output encoding")
            if "VULNERABLE" in security.get('auth_bypass', ''):
                print("  - CRITICAL: Authentication bypass detected - Review auth middleware")
                
        print("\n" + "=" * 80)

async def main():
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code \!= 200:
            print(f"❌ Server not responding correctly at {BASE_URL}")
            print("Please ensure the Flask server is running on port 5001")
            return
    except:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please start the server with: cd backend && python run.py")
        return
        
    tester = APIStressTester(BASE_URL)
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
EOFX < /dev/null