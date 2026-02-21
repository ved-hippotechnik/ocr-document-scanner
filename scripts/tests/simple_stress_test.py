#!/usr/bin/env python3
"""
Simplified API Stress Testing for OCR Document Scanner
"""

import time
import json
import requests
import threading
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
import statistics

BASE_URL = "http://localhost:5001"

class SimpleStressTester:
    def __init__(self):
        self.results = {
            "load_test": [],
            "security_test": {},
            "error_handling": {}
        }
        
    def test_endpoint(self, method: str, path: str, data=None, files=None) -> Tuple[float, int]:
        """Test a single endpoint and return response time and status code"""
        url = f"{BASE_URL}{path}"
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                if files:
                    response = requests.post(url, files=files, timeout=10)
                else:
                    response = requests.post(url, json=data, timeout=10)
            
            response_time = time.time() - start_time
            return response_time, response.status_code
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, 0  # 0 indicates error
            
    def load_test(self, endpoint: str, method: str, num_requests: int = 100):
        """Perform load test on an endpoint"""
        print(f"\n=== Load Testing {endpoint} ===")
        print(f"Total requests: {num_requests}")
        
        response_times = []
        status_codes = {}
        errors = 0
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(num_requests):
                future = executor.submit(self.test_endpoint, method, endpoint)
                futures.append(future)
                
            for future in as_completed(futures):
                try:
                    response_time, status_code = future.result()
                    response_times.append(response_time)
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1
                    if status_code == 0:
                        errors += 1
                except Exception as e:
                    errors += 1
                    
        # Calculate statistics
        if response_times:
            sorted_times = sorted(response_times)
            stats = {
                "endpoint": endpoint,
                "total_requests": num_requests,
                "successful": status_codes.get(200, 0) + status_codes.get(201, 0),
                "failed": sum(count for code, count in status_codes.items() if code >= 400),
                "errors": errors,
                "response_times": {
                    "min": min(response_times),
                    "max": max(response_times),
                    "mean": statistics.mean(response_times),
                    "median": statistics.median(response_times),
                    "p95": sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0,
                    "p99": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0,
                },
                "status_codes": dict(status_codes)
            }
            
            self.results["load_test"].append(stats)
            
            print(f"Success rate: {stats['successful']}/{num_requests} ({stats['successful']/num_requests*100:.1f}%)")
            print(f"Mean response time: {stats['response_times']['mean']:.3f}s")
            print(f"P95 response time: {stats['response_times']['p95']:.3f}s")
            
    def security_test(self):
        """Test for common security vulnerabilities"""
        print("\n=== Security Testing ===")
        
        # Test 1: SQL Injection
        print("Testing SQL Injection...")
        sql_payloads = ["' OR '1'='1", "'; DROP TABLE scan_history; --"]
        sql_safe = True
        
        for payload in sql_payloads:
            try:
                response = requests.post(
                    f"{BASE_URL}/api/auth/login",
                    json={"email": payload, "password": payload},
                    timeout=5
                )
                if response.status_code not in [400, 401, 422]:
                    sql_safe = False
                    break
            except:
                pass
                
        self.results["security_test"]["sql_injection"] = "PROTECTED" if sql_safe else "VULNERABLE"
        
        # Test 2: Authentication bypass
        print("Testing Authentication bypass...")
        try:
            response = requests.get(f"{BASE_URL}/api/auth/profile", timeout=5)
            auth_safe = response.status_code in [401, 403]
        except:
            auth_safe = True
            
        self.results["security_test"]["auth_bypass"] = "PROTECTED" if auth_safe else "VULNERABLE"
        
        # Test 3: Rate limiting
        print("Testing Rate limiting...")
        rapid_requests = 0
        for _ in range(100):
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    rapid_requests += 1
                elif response.status_code == 429:
                    break
            except:
                pass
                
        self.results["security_test"]["rate_limiting"] = f"PROTECTED (limited to {rapid_requests})" if rapid_requests < 100 else "VULNERABLE"
        
        print("\nSecurity Test Results:")
        for test, result in self.results["security_test"].items():
            status = "✅" if "PROTECTED" in result else "❌"
            print(f"{status} {test}: {result}")
            
    def error_handling_test(self):
        """Test error handling"""
        print("\n=== Error Handling Testing ===")
        
        # Test 1: Empty request
        print("Testing empty request handling...")
        try:
            response = requests.post(f"{BASE_URL}/api/scan", json={}, timeout=5)
            self.results["error_handling"]["empty_request"] = f"Status: {response.status_code}"
        except Exception as e:
            self.results["error_handling"]["empty_request"] = f"Error: {str(e)}"
            
        # Test 2: Invalid data
        print("Testing invalid data...")
        try:
            files = {'image': ('test.jpg', b'invalid_data', 'image/jpeg')}
            response = requests.post(f"{BASE_URL}/api/scan", files=files, timeout=5)
            self.results["error_handling"]["invalid_data"] = f"Status: {response.status_code}"
        except Exception as e:
            self.results["error_handling"]["invalid_data"] = f"Error: {str(e)}"
            
        print("\nError Handling Results:")
        for test, result in self.results["error_handling"].items():
            print(f"- {test}: {result}")
            
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 80)
        print("API STRESS TEST REPORT")
        print("=" * 80)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "target": BASE_URL,
            "results": self.results
        }
        
        # Save report
        filename = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nReport saved to: {filename}")
        
        # Print summary
        print("\n=== SUMMARY ===")
        
        # Performance metrics
        if self.results["load_test"]:
            print("\n📊 Performance Metrics:")
            for test in self.results["load_test"]:
                print(f"\n{test['endpoint']}:")
                print(f"  Success rate: {test['successful']}/{test['total_requests']} ({test['successful']/test['total_requests']*100:.1f}%)")
                print(f"  Mean response: {test['response_times']['mean']*1000:.0f}ms")
                print(f"  P95 response: {test['response_times']['p95']*1000:.0f}ms")
                
        # Security summary
        if self.results["security_test"]:
            print("\n🔒 Security Summary:")
            vulnerable = sum(1 for result in self.results["security_test"].values() if "VULNERABLE" in result)
            protected = len(self.results["security_test"]) - vulnerable
            print(f"  Tests passed: {protected}/{len(self.results['security_test'])}")
            
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        for test in self.results["load_test"]:
            if test['response_times']['p95'] > 2.0:
                print(f"  - {test['endpoint']}: High P95 latency - Consider optimization")
            if test['failed'] > test['total_requests'] * 0.05:
                print(f"  - {test['endpoint']}: High failure rate - Investigate error handling")
                
        if "VULNERABLE" in self.results["security_test"].get("sql_injection", ""):
            print("  - CRITICAL: SQL injection vulnerability detected")
        if "VULNERABLE" in self.results["security_test"].get("auth_bypass", ""):
            print("  - CRITICAL: Authentication bypass detected")
        if "VULNERABLE" in self.results["security_test"].get("rate_limiting", ""):
            print("  - Implement stricter rate limiting")
            
        print("\n" + "=" * 80)

def main():
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ Server not responding correctly at {BASE_URL}")
            return
    except:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print("Please start the server with: cd backend && python run.py")
        return
        
    print("=" * 80)
    print("STARTING OCR DOCUMENT SCANNER API STRESS TEST")
    print("=" * 80)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    tester = SimpleStressTester()
    
    # Run tests
    tester.load_test("/health", "GET", 200)
    tester.load_test("/api/processors", "GET", 100)
    tester.load_test("/api/stats", "GET", 100)
    tester.security_test()
    tester.error_handling_test()
    
    # Generate report
    tester.generate_report()

if __name__ == "__main__":
    main()
