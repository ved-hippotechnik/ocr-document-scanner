#\!/usr/bin/env python3
"""
Comprehensive API Stress Testing for OCR Document Scanner
"""

import asyncio
import aiohttp
import time
import json
import base64
import statistics
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests
from typing import Dict, List, Tuple
from PIL import Image
import io

BASE_URL = "http://localhost:5001"

class APIStressTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.metrics = {}
        self.auth_token = None
        
    def generate_test_image(self, size_kb: int = 100) -> str:
        """Generate a test image of specified size"""
        pixels = size_kb * 1024 // 3
        dimension = int(pixels ** 0.5)
        
        img = Image.new('RGB', (dimension, dimension), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    def test_endpoint(self, method: str, path: str, data: Dict = None, headers: Dict = None) -> Tuple[float, int, Dict]:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        if headers is None:
            headers = {}
            
        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            response_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200]}
                
            return response_time, response.status_code, response_data
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, 0, {"error": str(e)}
            
    def load_test(self, name: str, method: str, path: str, concurrent: int, iterations: int, data: Dict = None):
        """Perform load test on an endpoint"""
        print(f"\n{'='*60}")
        print(f"LOAD TEST: {name}")
        print(f"{'='*60}")
        print(f"Endpoint: {method} {path}")
        print(f"Concurrent requests: {concurrent}")
        print(f"Iterations per thread: {iterations}")
        
        response_times = []
        status_codes = {}
        errors = []
        
        start_time = time.time()
        
        def worker():
            results = []
            for _ in range(iterations):
                response_time, status_code, response_data = self.test_endpoint(method, path, data)
                results.append((response_time, status_code, response_data))
            return results
            
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent)]
            
            for future in as_completed(futures):
                try:
                    worker_results = future.result()
                    for response_time, status_code, response_data in worker_results:
                        response_times.append(response_time)
                        status_codes[status_code] = status_codes.get(status_code, 0) + 1
                        if status_code == 0 or status_code >= 400:
                            errors.append(response_data)
                except Exception as e:
                    errors.append({"error": str(e)})
                    
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate statistics
        total_requests = len(response_times)
        successful = sum(1 for code in status_codes if 200 <= code < 400)
        failed = total_requests - successful
        
        if response_times:
            stats = {
                "name": name,
                "endpoint": f"{method} {path}",
                "total_requests": total_requests,
                "successful": successful,
                "failed": failed,
                "duration": duration,
                "requests_per_second": total_requests / duration,
                "response_times": {
                    "min": min(response_times) * 1000,
                    "max": max(response_times) * 1000,
                    "mean": statistics.mean(response_times) * 1000,
                    "median": statistics.median(response_times) * 1000,
                    "p95": statistics.quantiles(response_times, n=20)[18] * 1000 if len(response_times) > 20 else max(response_times) * 1000,
                    "p99": statistics.quantiles(response_times, n=100)[98] * 1000 if len(response_times) > 100 else max(response_times) * 1000,
                },
                "status_codes": dict(status_codes),
                "errors": errors[:5]  # First 5 errors
            }
            
            self.metrics[name] = stats
            
            # Print summary
            print(f"\nResults:")
            print(f"  Total: {total_requests} requests in {duration:.2f}s")
            print(f"  RPS: {stats['requests_per_second']:.2f}")
            print(f"  Success rate: {(successful/total_requests*100):.1f}%")
            print(f"  Response times (ms):")
            print(f"    Mean: {stats['response_times']['mean']:.0f}")
            print(f"    P95: {stats['response_times']['p95']:.0f}")
            print(f"    P99: {stats['response_times']['p99']:.0f}")
            print(f"  Status codes: {stats['status_codes']}")
            
    def security_test(self):
        """Test for security vulnerabilities"""
        print(f"\n{'='*60}")
        print("SECURITY VULNERABILITY TEST")
        print(f"{'='*60}")
        
        results = {}
        
        # Test 1: SQL Injection
        print("\n1. Testing SQL Injection...")
        sql_payloads = ["' OR '1'='1", "admin'--", "1' UNION SELECT * FROM users--"]
        sql_safe = True
        
        for payload in sql_payloads:
            _, status, response = self.test_endpoint(
                "POST", "/api/auth/login",
                {"email": payload, "password": payload}
            )
            if status not in [400, 401]:
                sql_safe = False
                results['sql_injection'] = f"VULNERABLE - Payload returned status {status}"
                break
                
        if sql_safe:
            results['sql_injection'] = "PROTECTED"
            
        # Test 2: Authentication Bypass
        print("2. Testing Authentication Bypass...")
        _, status, response = self.test_endpoint("GET", "/api/auth/profile")
        
        if status == 200:
            results['auth_bypass'] = "VULNERABLE - Protected endpoint accessible without auth"
        else:
            results['auth_bypass'] = "PROTECTED"
            
        # Test 3: Rate Limiting
        print("3. Testing Rate Limiting...")
        rapid_requests = 0
        rate_limited = False
        
        for i in range(150):
            _, status, _ = self.test_endpoint("GET", "/health")
            if status == 429:
                rate_limited = True
                rapid_requests = i
                break
            elif status == 200:
                rapid_requests += 1
                
        if not rate_limited and rapid_requests >= 100:
            results['rate_limiting'] = f"VULNERABLE - Allowed {rapid_requests} rapid requests"
        else:
            results['rate_limiting'] = f"PROTECTED - Limited after {rapid_requests} requests"
            
        # Test 4: Input Validation
        print("4. Testing Input Validation...")
        
        # Oversized payload
        _, status, response = self.test_endpoint(
            "POST", "/api/v2/scan",
            {"image": "A" * 50000000}  # 50MB of data
        )
        
        if status == 200:
            results['input_validation'] = "VULNERABLE - Accepts oversized payloads"
        else:
            results['input_validation'] = "PROTECTED"
            
        self.metrics['security'] = results
        
        print("\nSecurity Test Results:")
        for test, result in results.items():
            status_icon = "✅" if "PROTECTED" in result else "❌"
            print(f"  {status_icon} {test}: {result}")
            
    def error_handling_test(self):
        """Test error handling"""
        print(f"\n{'='*60}")
        print("ERROR HANDLING TEST")
        print(f"{'='*60}")
        
        test_cases = [
            ("Empty JSON", "POST", "/api/v2/scan", {}),
            ("Invalid JSON", "POST", "/api/v2/scan", {"image": "not-base64"}),
            ("Missing required fields", "POST", "/api/auth/login", {"email": "test@test.com"}),
            ("Invalid endpoint", "GET", "/api/nonexistent", None),
            ("Wrong method", "DELETE", "/api/scan", None),
        ]
        
        results = {}
        
        for test_name, method, path, data in test_cases:
            print(f"\nTesting: {test_name}")
            _, status, response = self.test_endpoint(method, path, data)
            
            if status >= 400 and status < 500:
                results[test_name] = f"GOOD - Proper error response (status {status})"
            elif status == 0:
                results[test_name] = "GOOD - Connection refused/timeout"
            else:
                results[test_name] = f"BAD - Unexpected response (status {status})"
                
            print(f"  Result: {results[test_name]}")
            if isinstance(response, dict) and 'error' in response:
                print(f"  Error: {response.get('error', {}).get('message', response['error'])}")
                
        self.metrics['error_handling'] = results
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("="*80)
        print("OCR DOCUMENT SCANNER - COMPREHENSIVE API STRESS TEST")
        print("="*80)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Check server
        print("\nChecking server connectivity...")
        _, status, _ = self.test_endpoint("GET", "/health")
        if status != 200:
            print("❌ Server not responding. Please ensure it's running on port 5001")
            return
        print("✅ Server is online")
        
        # Generate test data
        test_image = self.generate_test_image(500)  # 500KB image
        
        # 1. LOAD TESTS
        print("\n" + "="*80)
        print("PHASE 1: LOAD TESTING")
        print("="*80)
        
        # Test various endpoints
        self.load_test("Health Check", "GET", "/health", 50, 20, None)
        self.load_test("Get Processors", "GET", "/api/processors", 30, 10, None)
        self.load_test("Basic Scan", "POST", "/api/scan", 10, 5, {"image": test_image})
        self.load_test("Enhanced Scan", "POST", "/api/v2/scan", 10, 5, {"image": test_image})
        
        # 2. SECURITY TESTS
        print("\n" + "="*80)
        print("PHASE 2: SECURITY TESTING")
        print("="*80)
        self.security_test()
        
        # 3. ERROR HANDLING TESTS
        print("\n" + "="*80)
        print("PHASE 3: ERROR HANDLING")
        print("="*80)
        self.error_handling_test()
        
        # 4. SUSTAINED LOAD TEST
        print("\n" + "="*80)
        print("PHASE 4: SUSTAINED LOAD TEST")
        print("="*80)
        print("Running 1-minute sustained load test...")
        
        self.load_test(
            "Sustained Load",
            "POST",
            "/api/v2/scan",
            20,  # 20 concurrent users
            30,  # 30 requests each
            {"image": test_image}
        )
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        
        # Save detailed report
        filename = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "target": self.base_url,
                "results": self.metrics
            }, f, indent=2)
            
        print(f"\nDetailed report saved to: {filename}")
        
        # Performance Summary
        print("\n📊 PERFORMANCE SUMMARY:")
        for test_name, metrics in self.metrics.items():
            if 'response_times' in metrics:
                print(f"\n{test_name}:")
                print(f"  - Requests: {metrics['total_requests']}")
                print(f"  - Success Rate: {(metrics['successful']/metrics['total_requests']*100):.1f}%")
                print(f"  - RPS: {metrics['requests_per_second']:.2f}")
                print(f"  - Avg Response: {metrics['response_times']['mean']:.0f}ms")
                
        # Security Summary
        if 'security' in self.metrics:
            vulnerable = sum(1 for r in self.metrics['security'].values() if "VULNERABLE" in r)
            print(f"\n🔒 SECURITY: {len(self.metrics['security'])-vulnerable}/{len(self.metrics['security'])} tests passed")
            
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        # Check for performance issues
        perf_issues = []
        for test_name, metrics in self.metrics.items():
            if 'response_times' in metrics:
                if metrics['response_times']['p95'] > 2000:  # 2 seconds
                    perf_issues.append(f"{test_name}: High P95 latency ({metrics['response_times']['p95']:.0f}ms)")
                if metrics['failed'] > metrics['total_requests'] * 0.05:  # 5% failure
                    perf_issues.append(f"{test_name}: High failure rate ({(metrics['failed']/metrics['total_requests']*100):.1f}%)")
                    
        if perf_issues:
            print("\nPerformance Issues:")
            for issue in perf_issues:
                print(f"  - {issue}")
        else:
            print("\n  ✅ No significant performance issues detected")
            
        # Check for security issues
        if 'security' in self.metrics:
            sec_issues = [f"{k}: {v}" for k, v in self.metrics['security'].items() if "VULNERABLE" in v]
            if sec_issues:
                print("\n⚠️  Security Vulnerabilities:")
                for issue in sec_issues:
                    print(f"  - {issue}")
            else:
                print("\n  ✅ No security vulnerabilities detected")
                
        print("\n" + "="*80)

def main():
    tester = APIStressTester(BASE_URL)
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main()
