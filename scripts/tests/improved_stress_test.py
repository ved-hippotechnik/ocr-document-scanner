#\!/usr/bin/env python3
"""
Comprehensive API Stress Testing for OCR Document Scanner - Improved Version
Tests all new features and improvements
"""

import time
import json
import base64
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io
import os

BASE_URL = "http://localhost:5001"

class ImprovedAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {}
        self.test_timestamp = datetime.now()
        
    def generate_test_image(self, size_kb: int = 100, text: str = "TEST") -> bytes:
        """Generate a test image with text"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Calculate dimensions
        pixels = size_kb * 1024 // 3
        dimension = max(100, int(pixels ** 0.5))
        
        # Create image with text
        img = Image.new('RGB', (dimension, dimension), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text to make OCR testable
        text_to_draw = f"{text}\nDocument ID: 123456\nDate: 2025-01-01"
        draw.text((10, 10), text_to_draw, fill='black')
        
        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n" + "="*60)
        print("TESTING: Rate Limiting")
        print("="*60)
        
        results = {
            "scan_endpoint": {},
            "health_endpoint": {},
            "auth_endpoint": {}
        }
        
        # Test 1: Scan endpoint rate limit (2/sec, 20/min)
        print("\n1. Testing scan endpoint rate limit...")
        scan_count = 0
        scan_blocked = False
        
        test_image = self.generate_test_image(100)
        
        for i in range(30):  # Try 30 requests rapidly
            try:
                files = {'image': ('test.jpg', test_image, 'image/jpeg')}
                response = requests.post(f"{self.base_url}/api/v3/scan", files=files, timeout=5)
                
                if response.status_code == 429:
                    scan_blocked = True
                    results["scan_endpoint"] = {
                        "status": "WORKING",
                        "triggered_after": i,
                        "message": "Rate limit enforced correctly"
                    }
                    print(f"   ✅ Rate limit triggered after {i} requests")
                    break
                elif response.status_code in [200, 400]:
                    scan_count += 1
            except Exception as e:
                print(f"   Error: {e}")
                
        if not scan_blocked:
            results["scan_endpoint"] = {
                "status": "NOT WORKING",
                "allowed_requests": scan_count,
                "message": "Rate limit not enforced"
            }
            print(f"   ❌ Rate limit NOT working - allowed {scan_count} requests")
        
        # Wait a bit before next test
        time.sleep(2)
        
        # Test 2: Health endpoint (lighter limit)
        print("\n2. Testing health endpoint rate limit...")
        health_count = 0
        health_blocked = False
        
        for i in range(150):  # Try 150 requests rapidly
            try:
                response = requests.get(f"{self.base_url}/api/v3/health", timeout=1)
                
                if response.status_code == 429:
                    health_blocked = True
                    results["health_endpoint"] = {
                        "status": "WORKING",
                        "triggered_after": i,
                        "message": "Rate limit enforced"
                    }
                    print(f"   ✅ Rate limit triggered after {i} requests")
                    break
                elif response.status_code in [200, 503]:
                    health_count += 1
            except:
                pass
                
        if not health_blocked:
            results["health_endpoint"] = {
                "status": "NOT WORKING",
                "allowed_requests": health_count,
                "message": "Rate limit not enforced"
            }
            print(f"   ❌ Rate limit NOT working - allowed {health_count} requests")
        
        self.results["rate_limiting"] = results
        return results
    
    def test_error_handling(self):
        """Test improved error handling"""
        print("\n" + "="*60)
        print("TESTING: Error Handling")
        print("="*60)
        
        test_cases = [
            {
                "name": "Empty file",
                "test": lambda: requests.post(
                    f"{self.base_url}/api/v3/scan",
                    files={'image': ('empty.jpg', b'', 'image/jpeg')}
                ),
                "expected_status": [400],
                "expected_error": "EMPTY_FILE"
            },
            {
                "name": "Invalid image data",
                "test": lambda: requests.post(
                    f"{self.base_url}/api/v3/scan",
                    files={'image': ('corrupt.jpg', b'not-an-image', 'image/jpeg')}
                ),
                "expected_status": [400],
                "expected_error": "INVALID_IMAGE"
            },
            {
                "name": "Oversized file",
                "test": lambda: requests.post(
                    f"{self.base_url}/api/v3/scan",
                    files={'image': ('huge.jpg', b'X' * (50 * 1024 * 1024), 'image/jpeg')}
                ),
                "expected_status": [413, 400],
                "expected_error": "FILE_TOO_LARGE"
            },
            {
                "name": "Missing file",
                "test": lambda: requests.post(
                    f"{self.base_url}/api/v3/scan",
                    data={'test': 'data'}
                ),
                "expected_status": [400],
                "expected_error": "FILE_REQUIRED"
            },
            {
                "name": "Invalid content type",
                "test": lambda: requests.post(
                    f"{self.base_url}/api/v3/scan",
                    data="plain text",
                    headers={'Content-Type': 'text/plain'}
                ),
                "expected_status": [400],
                "expected_error": "Invalid content type"
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            print(f"\n{test_case['name']}...")
            try:
                response = test_case["test"]()
                
                if response.status_code in test_case["expected_status"]:
                    try:
                        data = response.json()
                        if 'error' in data or 'code' in data:
                            results[test_case["name"]] = {
                                "status": "PASS",
                                "http_status": response.status_code,
                                "error_code": data.get('code', data.get('error'))
                            }
                            print(f"   ✅ Correct error handling - Status {response.status_code}")
                        else:
                            results[test_case["name"]] = {
                                "status": "PARTIAL",
                                "http_status": response.status_code,
                                "message": "Status code correct but no error details"
                            }
                            print(f"   ⚠️ Partial - Status {response.status_code} but no error details")
                    except:
                        results[test_case["name"]] = {
                            "status": "PARTIAL",
                            "http_status": response.status_code,
                            "message": "Could not parse response"
                        }
                else:
                    results[test_case["name"]] = {
                        "status": "FAIL",
                        "http_status": response.status_code,
                        "message": f"Expected {test_case['expected_status']}, got {response.status_code}"
                    }
                    print(f"   ❌ Wrong status code - Expected {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                results[test_case["name"]] = {
                    "status": "ERROR",
                    "message": str(e)
                }
                print(f"   ❌ Error: {e}")
        
        self.results["error_handling"] = results
        return results
    
    def test_security_validation(self):
        """Test security validation features"""
        print("\n" + "="*60)
        print("TESTING: Security Validation")
        print("="*60)
        
        results = {}
        
        # Test 1: SQL Injection in parameters
        print("\n1. SQL Injection attempts...")
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--"
        ]
        
        sql_protected = True
        for payload in sql_payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v3/scan",
                    files={'image': ('test.jpg', self.generate_test_image(), 'image/jpeg')},
                    data={'document_type': payload}
                )
                if response.status_code == 200:
                    # Check if payload was sanitized
                    data = response.json()
                    if payload in str(data):
                        sql_protected = False
                        break
            except:
                pass
        
        results["sql_injection"] = {
            "status": "PROTECTED" if sql_protected else "VULNERABLE",
            "message": "SQL injection attempts blocked" if sql_protected else "SQL payloads accepted"
        }
        print(f"   {'✅' if sql_protected else '❌'} SQL Injection: {results['sql_injection']['status']}")
        
        # Test 2: Path Traversal in filenames
        print("\n2. Path traversal attempts...")
        path_payloads = [
            "../../etc/passwd",
            "../../../windows/system32/config/sam",
            "..\\..\\..\\windows\\system32\\config\\sam"
        ]
        
        path_protected = True
        for payload in path_payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v3/scan",
                    files={'image': (payload, self.generate_test_image(), 'image/jpeg')}
                )
                if response.status_code == 200:
                    path_protected = False
                    break
            except:
                pass
        
        results["path_traversal"] = {
            "status": "PROTECTED" if path_protected else "VULNERABLE",
            "message": "Path traversal blocked" if path_protected else "Dangerous filenames accepted"
        }
        print(f"   {'✅' if path_protected else '❌'} Path Traversal: {results['path_traversal']['status']}")
        
        # Test 3: XSS in parameters
        print("\n3. XSS attempts...")
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ]
        
        xss_protected = True
        for payload in xss_payloads:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v3/scan",
                    files={'image': ('test.jpg', self.generate_test_image(), 'image/jpeg')},
                    data={'session_id': payload}
                )
                if response.status_code == 200:
                    data = response.json()
                    # Check if payload appears unsanitized
                    if payload in str(data):
                        xss_protected = False
                        break
            except:
                pass
        
        results["xss"] = {
            "status": "PROTECTED" if xss_protected else "VULNERABLE",
            "message": "XSS attempts sanitized" if xss_protected else "XSS payloads not sanitized"
        }
        print(f"   {'✅' if xss_protected else '❌'} XSS: {results['xss']['status']}")
        
        self.results["security_validation"] = results
        return results
    
    def test_monitoring_endpoints(self):
        """Test monitoring endpoints"""
        print("\n" + "="*60)
        print("TESTING: Monitoring Endpoints")
        print("="*60)
        
        results = {}
        
        # Test 1: Prometheus metrics endpoint
        print("\n1. Testing /metrics endpoint...")
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            if response.status_code == 200:
                content = response.text
                # Check for Prometheus format
                if "# HELP" in content and "# TYPE" in content:
                    results["prometheus_metrics"] = {
                        "status": "WORKING",
                        "message": "Prometheus metrics available",
                        "sample_metrics": content[:200]
                    }
                    print("   ✅ Prometheus metrics endpoint working")
                else:
                    results["prometheus_metrics"] = {
                        "status": "PARTIAL",
                        "message": "Endpoint exists but format incorrect"
                    }
                    print("   ⚠️ Endpoint exists but format incorrect")
            else:
                results["prometheus_metrics"] = {
                    "status": "NOT FOUND",
                    "http_status": response.status_code
                }
                print(f"   ❌ Metrics endpoint returned {response.status_code}")
        except Exception as e:
            results["prometheus_metrics"] = {
                "status": "ERROR",
                "message": str(e)
            }
            print(f"   ❌ Error accessing metrics: {e}")
        
        # Test 2: JSON metrics summary
        print("\n2. Testing /api/metrics/summary endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/metrics/summary", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'timestamp' in data and 'requests' in data:
                    results["metrics_summary"] = {
                        "status": "WORKING",
                        "message": "JSON metrics available",
                        "data_keys": list(data.keys())
                    }
                    print("   ✅ JSON metrics summary working")
                else:
                    results["metrics_summary"] = {
                        "status": "PARTIAL",
                        "message": "Endpoint works but data incomplete"
                    }
                    print("   ⚠️ Endpoint works but data incomplete")
            else:
                results["metrics_summary"] = {
                    "status": "NOT FOUND",
                    "http_status": response.status_code
                }
                print(f"   ❌ Summary endpoint returned {response.status_code}")
        except Exception as e:
            results["metrics_summary"] = {
                "status": "ERROR",
                "message": str(e)
            }
            print(f"   ❌ Error: {e}")
        
        # Test 3: Check for X-Request-Duration header
        print("\n3. Testing X-Request-Duration header...")
        try:
            response = requests.get(f"{self.base_url}/api/v3/health", timeout=5)
            if 'X-Request-Duration' in response.headers:
                results["duration_header"] = {
                    "status": "PRESENT",
                    "value": response.headers['X-Request-Duration']
                }
                print(f"   ✅ X-Request-Duration header present: {response.headers['X-Request-Duration']}")
            else:
                results["duration_header"] = {
                    "status": "MISSING",
                    "headers": list(response.headers.keys())
                }
                print("   ❌ X-Request-Duration header missing")
        except Exception as e:
            results["duration_header"] = {
                "status": "ERROR",
                "message": str(e)
            }
            print(f"   ❌ Error: {e}")
        
        self.results["monitoring"] = results
        return results
    
    def test_caching(self):
        """Test caching functionality"""
        print("\n" + "="*60)
        print("TESTING: Caching")
        print("="*60)
        
        results = {}
        
        # Test processor list caching
        print("\n1. Testing processor list caching...")
        
        # First request
        start = time.time()
        response1 = requests.get(f"{self.base_url}/api/v3/processors")
        time1 = time.time() - start
        
        # Second request (should be cached)
        start = time.time()
        response2 = requests.get(f"{self.base_url}/api/v3/processors")
        time2 = time.time() - start
        
        # Third request
        start = time.time()
        response3 = requests.get(f"{self.base_url}/api/v3/processors")
        time3 = time.time() - start
        
        if time2 < time1 * 0.5 and time3 < time1 * 0.5:
            results["processor_cache"] = {
                "status": "WORKING",
                "first_request_ms": round(time1 * 1000, 2),
                "cached_request_ms": round(time2 * 1000, 2),
                "speedup": f"{round(time1/time2, 1)}x"
            }
            print(f"   ✅ Caching working - {results['processor_cache']['speedup']} speedup")
        else:
            results["processor_cache"] = {
                "status": "NOT WORKING",
                "times_ms": [round(time1*1000, 2), round(time2*1000, 2), round(time3*1000, 2)]
            }
            print(f"   ❌ Caching not effective - Times: {results['processor_cache']['times_ms']}")
        
        self.results["caching"] = results
        return results
    
    def load_test(self, name: str, endpoint: str, method: str = "GET", 
                  concurrent: int = 10, duration_seconds: int = 10, 
                  data_func=None):
        """Perform load test on endpoint"""
        print("\n" + "="*60)
        print(f"LOAD TEST: {name}")
        print("="*60)
        print(f"Endpoint: {method} {endpoint}")
        print(f"Concurrent users: {concurrent}")
        print(f"Duration: {duration_seconds}s")
        
        results = {
            "response_times": [],
            "status_codes": {},
            "errors": []
        }
        
        start_time = time.time()
        request_count = 0
        
        def worker():
            nonlocal request_count
            worker_results = []
            
            while time.time() - start_time < duration_seconds:
                try:
                    req_start = time.time()
                    
                    if data_func:
                        data = data_func()
                        if 'files' in data:
                            response = requests.post(f"{self.base_url}{endpoint}", 
                                                    files=data['files'], timeout=30)
                        else:
                            response = requests.post(f"{self.base_url}{endpoint}", 
                                                    json=data, timeout=30)
                    else:
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                    
                    req_time = time.time() - req_start
                    worker_results.append({
                        "time": req_time,
                        "status": response.status_code
                    })
                    request_count += 1
                    
                except Exception as e:
                    worker_results.append({
                        "time": time.time() - req_start,
                        "status": 0,
                        "error": str(e)
                    })
            
            return worker_results
        
        # Run concurrent workers
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(worker) for _ in range(concurrent)]
            
            for future in as_completed(futures):
                try:
                    worker_results = future.result()
                    for result in worker_results:
                        results["response_times"].append(result["time"])
                        status = result["status"]
                        results["status_codes"][status] = results["status_codes"].get(status, 0) + 1
                        if status == 0 or status >= 400:
                            results["errors"].append(result.get("error", f"Status {status}"))
                except Exception as e:
                    results["errors"].append(str(e))
        
        # Calculate statistics
        actual_duration = time.time() - start_time
        total_requests = len(results["response_times"])
        successful = sum(count for status, count in results["status_codes"].items() 
                        if 200 <= status < 400)
        
        if results["response_times"]:
            stats = {
                "name": name,
                "total_requests": total_requests,
                "successful": successful,
                "failed": total_requests - successful,
                "duration": actual_duration,
                "rps": total_requests / actual_duration,
                "response_times": {
                    "min": min(results["response_times"]) * 1000,
                    "max": max(results["response_times"]) * 1000,
                    "mean": statistics.mean(results["response_times"]) * 1000,
                    "median": statistics.median(results["response_times"]) * 1000,
                    "p95": statistics.quantiles(results["response_times"], n=20)[18] * 1000 if len(results["response_times"]) > 20 else max(results["response_times"]) * 1000,
                    "p99": statistics.quantiles(results["response_times"], n=100)[98] * 1000 if len(results["response_times"]) > 100 else max(results["response_times"]) * 1000,
                },
                "status_codes": results["status_codes"],
                "error_sample": results["errors"][:5]
            }
            
            print(f"\nResults:")
            print(f"  Total: {total_requests} requests in {actual_duration:.1f}s")
            print(f"  RPS: {stats['rps']:.1f}")
            print(f"  Success rate: {(successful/total_requests*100):.1f}%")
            print(f"  Response times (ms):")
            print(f"    Mean: {stats['response_times']['mean']:.0f}")
            print(f"    P95: {stats['response_times']['p95']:.0f}")
            print(f"    P99: {stats['response_times']['p99']:.0f}")
            print(f"  Status codes: {stats['status_codes']}")
            
            self.results[f"load_test_{name}"] = stats
            return stats
        
        return None
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("OCR DOCUMENT SCANNER - IMPROVED API STRESS TEST")
        print("="*80)
        print(f"Target: {self.base_url}")
        print(f"Time: {self.test_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Check connectivity
        print("\nChecking server connectivity...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print("❌ Server not responding properly")
                return
            print("✅ Server is online")
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return
        
        # Run all test suites
        print("\n" + "="*80)
        print("PHASE 1: FEATURE VERIFICATION")
        print("="*80)
        
        # Test new features
        self.test_rate_limiting()
        self.test_error_handling()
        self.test_security_validation()
        self.test_monitoring_endpoints()
        self.test_caching()
        
        print("\n" + "="*80)
        print("PHASE 2: LOAD TESTING")
        print("="*80)
        
        # Load tests
        self.load_test("Health Check", "/api/v3/health", "GET", 50, 5)
        self.load_test("Processor List", "/api/v3/processors", "GET", 30, 5)
        
        # OCR scan load test
        def create_scan_data():
            return {'files': {'image': ('test.jpg', self.generate_test_image(), 'image/jpeg')}}
        
        self.load_test("OCR Scan", "/api/v3/scan", "POST", 10, 10, create_scan_data)
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("FINAL TEST REPORT")
        print("="*80)
        
        # Save detailed results
        filename = f"improved_test_report_{self.test_timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": self.test_timestamp.isoformat(),
                "target": self.base_url,
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")
        
        # Summary of improvements
        print("\n" + "="*60)
        print("IMPROVEMENT VERIFICATION SUMMARY")
        print("="*60)
        
        improvements = {
            "Rate Limiting": False,
            "Error Handling": False,
            "Security Validation": False,
            "Monitoring": False,
            "Caching": False
        }
        
        # Check rate limiting
        if "rate_limiting" in self.results:
            rl = self.results["rate_limiting"]
            if any(v.get("status") == "WORKING" for v in rl.values()):
                improvements["Rate Limiting"] = True
        
        # Check error handling
        if "error_handling" in self.results:
            eh = self.results["error_handling"]
            passed = sum(1 for v in eh.values() if v.get("status") == "PASS")
            if passed > len(eh) * 0.7:  # 70% pass rate
                improvements["Error Handling"] = True
        
        # Check security
        if "security_validation" in self.results:
            sv = self.results["security_validation"]
            if all(v.get("status") == "PROTECTED" for v in sv.values()):
                improvements["Security Validation"] = True
        
        # Check monitoring
        if "monitoring" in self.results:
            mon = self.results["monitoring"]
            if any(v.get("status") in ["WORKING", "PRESENT"] for v in mon.values()):
                improvements["Monitoring"] = True
        
        # Check caching
        if "caching" in self.results:
            cache = self.results["caching"]
            if any(v.get("status") == "WORKING" for v in cache.values()):
                improvements["Caching"] = True
        
        print("\nImprovement Status:")
        for feature, working in improvements.items():
            status = "✅ VERIFIED" if working else "❌ NOT WORKING"
            print(f"  {feature}: {status}")
        
        # Performance comparison
        print("\n" + "="*60)
        print("PERFORMANCE METRICS")
        print("="*60)
        
        for test_name, result in self.results.items():
            if test_name.startswith("load_test_"):
                name = test_name.replace("load_test_", "")
                print(f"\n{name}:")
                print(f"  RPS: {result['rps']:.1f}")
                print(f"  Success Rate: {(result['successful']/result['total_requests']*100):.1f}%")
                print(f"  Avg Response: {result['response_times']['mean']:.0f}ms")
                print(f"  P95 Response: {result['response_times']['p95']:.0f}ms")
        
        # Overall assessment
        print("\n" + "="*60)
        print("OVERALL ASSESSMENT")
        print("="*60)
        
        working_count = sum(1 for v in improvements.values() if v)
        total_count = len(improvements)
        
        print(f"\nImprovements Working: {working_count}/{total_count}")
        
        if working_count == total_count:
            print("🎉 ALL IMPROVEMENTS VERIFIED AND WORKING\!")
            print("✅ The API is production-ready with all security and performance features.")
        elif working_count >= total_count * 0.6:
            print("⚠️ MOST improvements are working, but some issues remain.")
            print("Recommendation: Fix the remaining issues before production deployment.")
        else:
            print("❌ MANY improvements are not working properly.")
            print("Recommendation: Review and fix the implementation before deployment.")
        
        # Specific recommendations
        print("\n" + "="*60)
        print("RECOMMENDATIONS")
        print("="*60)
        
        if not improvements["Rate Limiting"]:
            print("\n1. RATE LIMITING:")
            print("   - Ensure RATE_LIMIT_ENABLED=true in environment")
            print("   - Check Redis connection for distributed rate limiting")
            print("   - Verify Flask-Limiter is properly initialized")
        
        if not improvements["Error Handling"]:
            print("\n2. ERROR HANDLING:")
            print("   - Implement proper validation in routes_improved.py")
            print("   - Return appropriate HTTP status codes")
            print("   - Include error details in response body")
        
        if not improvements["Security Validation"]:
            print("\n3. SECURITY:")
            print("   - Enable input sanitization")
            print("   - Implement file validation")
            print("   - Add SQL injection protection")
        
        if not improvements["Monitoring"]:
            print("\n4. MONITORING:")
            print("   - Register monitoring blueprint")
            print("   - Initialize Prometheus metrics")
            print("   - Add request duration tracking")
        
        if not improvements["Caching"]:
            print("\n5. CACHING:")
            print("   - Configure cache backend (Redis recommended)")
            print("   - Implement cache decorators")
            print("   - Set appropriate TTL values")
        
        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)

if __name__ == "__main__":
    tester = ImprovedAPITester()
    tester.run_comprehensive_test()
