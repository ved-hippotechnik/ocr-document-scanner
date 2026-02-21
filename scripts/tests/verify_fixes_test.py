#\!/usr/bin/env python3
"""
Comprehensive verification test for all applied fixes
"""

import requests
import time
import json
import base64
import io
import threading
from datetime import datetime
from PIL import Image
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiohttp

BASE_URL = "http://localhost:5001"

class FixVerificationTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = {}
        
    def generate_test_image(self, size_kb: int = 100) -> bytes:
        """Generate a test image"""
        pixels = size_kb * 1024 // 3
        dimension = int(pixels ** 0.5)
        img = Image.new('RGB', (dimension, dimension), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
        
    def test_rate_limiting(self):
        """Test 1: Verify rate limiting is enabled"""
        print("\n" + "="*60)
        print("TEST 1: RATE LIMITING VERIFICATION")
        print("="*60)
        
        # Make rapid requests to trigger rate limiting
        request_count = 0
        rate_limited = False
        rate_limit_status = None
        
        print("Making rapid requests to test rate limiting...")
        
        for i in range(150):  # Try 150 requests
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 429:
                    rate_limited = True
                    rate_limit_status = i
                    print(f"✅ Rate limit triggered after {i} requests (Status 429)")
                    
                    # Check for Retry-After header
                    if 'Retry-After' in response.headers:
                        print(f"   Retry-After header: {response.headers['Retry-After']} seconds")
                    break
                elif response.status_code == 200:
                    request_count += 1
            except Exception as e:
                print(f"   Request {i} failed: {e}")
                
        if rate_limited:
            self.results['rate_limiting'] = {
                'status': 'PASSED',
                'details': f'Rate limiting active - triggered after {rate_limit_status} requests',
                'triggered_at': rate_limit_status
            }
        else:
            self.results['rate_limiting'] = {
                'status': 'FAILED',
                'details': f'No rate limiting - allowed {request_count} rapid requests without limit',
                'requests_made': request_count
            }
            
        # Wait a bit before next test
        time.sleep(2)
        
    def test_v3_endpoints(self):
        """Test 2: Verify V3 endpoints are working"""
        print("\n" + "="*60)
        print("TEST 2: V3 ENDPOINTS VERIFICATION")
        print("="*60)
        
        v3_endpoints = [
            ("GET", "/api/v3/health", None, None),
            ("GET", "/api/v3/processors", None, None),
            ("POST", "/api/v3/scan", None, {'image': ('test.jpg', self.generate_test_image(50), 'image/jpeg')}),
        ]
        
        results = {}
        
        for method, endpoint, data, files in v3_endpoints:
            print(f"\nTesting {method} {endpoint}...")
            
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", files=files, timeout=10)
                    
                if response.status_code == 404:
                    results[endpoint] = {
                        'status': 'FAILED',
                        'code': 404,
                        'message': 'Endpoint not found'
                    }
                    print(f"   ❌ Endpoint not found (404)")
                elif response.status_code in [200, 201]:
                    results[endpoint] = {
                        'status': 'PASSED',
                        'code': response.status_code,
                        'message': 'Endpoint working'
                    }
                    print(f"   ✅ Endpoint working ({response.status_code})")
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    print(f"   ⏳ Rate limited, waiting 60s...")
                    time.sleep(60)
                    # Retry
                    if method == "GET":
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    else:
                        response = requests.post(f"{self.base_url}{endpoint}", files=files, timeout=10)
                    
                    results[endpoint] = {
                        'status': 'PASSED' if response.status_code in [200, 201, 400] else 'FAILED',
                        'code': response.status_code,
                        'message': f'Endpoint accessible after rate limit'
                    }
                else:
                    results[endpoint] = {
                        'status': 'WARNING',
                        'code': response.status_code,
                        'message': f'Unexpected status: {response.status_code}'
                    }
                    print(f"   ⚠️ Unexpected response ({response.status_code})")
                    
            except Exception as e:
                results[endpoint] = {
                    'status': 'FAILED',
                    'code': 0,
                    'message': str(e)
                }
                print(f"   ❌ Error: {e}")
                
        self.results['v3_endpoints'] = results
        
    def test_error_handling(self):
        """Test 3: Verify error handling for invalid inputs"""
        print("\n" + "="*60)
        print("TEST 3: ERROR HANDLING VERIFICATION")
        print("="*60)
        
        test_cases = [
            {
                'name': 'Empty file upload',
                'method': 'POST',
                'endpoint': '/api/scan',
                'files': {'image': ('empty.jpg', b'', 'image/jpeg')},
                'expected_status': [400, 422]
            },
            {
                'name': 'Invalid image data',
                'method': 'POST',
                'endpoint': '/api/scan',
                'files': {'image': ('invalid.jpg', b'not an image', 'image/jpeg')},
                'expected_status': [400, 422]
            },
            {
                'name': 'Corrupted base64',
                'method': 'POST',
                'endpoint': '/api/v2/scan',
                'json': {'image': 'invalid-base64-data!!!'},
                'expected_status': [400, 422]
            },
            {
                'name': 'Missing required field',
                'method': 'POST',
                'endpoint': '/api/v2/scan',
                'json': {},
                'expected_status': [400, 422]
            },
            {
                'name': 'Oversized payload',
                'method': 'POST',
                'endpoint': '/api/v2/scan',
                'json': {'image': 'A' * 50000000},  # 50MB
                'expected_status': [400, 413, 422]
            }
        ]
        
        results = {}
        
        for test in test_cases:
            print(f"\nTesting: {test['name']}...")
            
            try:
                if 'files' in test:
                    response = requests.post(
                        f"{self.base_url}{test['endpoint']}", 
                        files=test['files'],
                        timeout=10
                    )
                else:
                    response = requests.post(
                        f"{self.base_url}{test['endpoint']}", 
                        json=test.get('json'),
                        timeout=10
                    )
                    
                if response.status_code in test['expected_status']:
                    results[test['name']] = {
                        'status': 'PASSED',
                        'code': response.status_code,
                        'message': 'Proper error handling'
                    }
                    print(f"   ✅ Correct error response ({response.status_code})")
                else:
                    results[test['name']] = {
                        'status': 'FAILED',
                        'code': response.status_code,
                        'message': f'Expected {test["expected_status"]}, got {response.status_code}'
                    }
                    print(f"   ❌ Wrong status code: expected {test['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                results[test['name']] = {
                    'status': 'ERROR',
                    'code': 0,
                    'message': str(e)
                }
                print(f"   ❌ Error: {e}")
                
        self.results['error_handling'] = results
        
    def test_monitoring_endpoints(self):
        """Test 4: Verify monitoring endpoints are active"""
        print("\n" + "="*60)
        print("TEST 4: MONITORING ENDPOINTS VERIFICATION")
        print("="*60)
        
        monitoring_endpoints = [
            ("/metrics", "Prometheus metrics"),
            ("/api/metrics/summary", "JSON metrics summary"),
            ("/api/analytics/dashboard", "Analytics dashboard"),
            ("/health", "Basic health check"),
            ("/api/v2/health", "Detailed health check")
        ]
        
        results = {}
        
        for endpoint, description in monitoring_endpoints:
            print(f"\nTesting {endpoint} ({description})...")
            
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    results[endpoint] = {
                        'status': 'PASSED',
                        'code': 200,
                        'message': f'{description} working'
                    }
                    print(f"   ✅ Endpoint working")
                    
                    # Check response content
                    if endpoint == "/metrics" and "# HELP" in response.text:
                        print(f"   ✅ Prometheus format confirmed")
                    elif endpoint == "/api/metrics/summary":
                        try:
                            data = response.json()
                            print(f"   ✅ JSON response valid")
                        except:
                            print(f"   ⚠️ Response is not valid JSON")
                            
                else:
                    results[endpoint] = {
                        'status': 'FAILED',
                        'code': response.status_code,
                        'message': f'Endpoint returned {response.status_code}'
                    }
                    print(f"   ❌ Endpoint returned {response.status_code}")
                    
            except Exception as e:
                results[endpoint] = {
                    'status': 'ERROR',
                    'code': 0,
                    'message': str(e)
                }
                print(f"   ❌ Error: {e}")
                
        self.results['monitoring'] = results
        
    async def test_websocket(self):
        """Test 5: Verify WebSocket functionality"""
        print("\n" + "="*60)
        print("TEST 5: WEBSOCKET FUNCTIONALITY VERIFICATION")
        print("="*60)
        
        ws_url = "ws://localhost:5001/ws"
        
        try:
            async with aiohttp.ClientSession() as session:
                print(f"Attempting WebSocket connection to {ws_url}...")
                
                try:
                    async with session.ws_connect(ws_url, timeout=5) as ws:
                        print("   ✅ WebSocket connection established")
                        
                        # Send a test message
                        await ws.send_str(json.dumps({'type': 'ping'}))
                        print("   ✅ Test message sent")
                        
                        # Wait for response
                        msg = await asyncio.wait_for(ws.receive(), timeout=5)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            print(f"   ✅ Received response: {msg.data[:100]}")
                            self.results['websocket'] = {
                                'status': 'PASSED',
                                'message': 'WebSocket functional'
                            }
                        else:
                            self.results['websocket'] = {
                                'status': 'WARNING',
                                'message': f'Unexpected message type: {msg.type}'
                            }
                            
                except aiohttp.ClientError as e:
                    print(f"   ❌ WebSocket connection failed: {e}")
                    self.results['websocket'] = {
                        'status': 'FAILED',
                        'message': f'Connection failed: {str(e)}'
                    }
                    
        except Exception as e:
            print(f"   ❌ WebSocket test error: {e}")
            self.results['websocket'] = {
                'status': 'ERROR',
                'message': str(e)
            }
            
    def test_performance_consistency(self):
        """Test 6: Verify performance improvements"""
        print("\n" + "="*60)
        print("TEST 6: PERFORMANCE CONSISTENCY VERIFICATION")
        print("="*60)
        
        print("Testing response time consistency...")
        
        # Test health endpoint response times
        response_times = []
        
        for i in range(20):
            start = time.time()
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    response_times.append((time.time() - start) * 1000)  # Convert to ms
            except:
                pass
            time.sleep(0.1)  # Small delay between requests
            
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"   Response times (ms):")
            print(f"   - Average: {avg_time:.2f}")
            print(f"   - Min: {min_time:.2f}")
            print(f"   - Max: {max_time:.2f}")
            
            # Check if times are consistent (max < 5x min)
            if max_time < min_time * 5 and avg_time < 100:
                self.results['performance'] = {
                    'status': 'PASSED',
                    'avg_ms': avg_time,
                    'message': 'Consistent performance'
                }
                print("   ✅ Performance is consistent")
            else:
                self.results['performance'] = {
                    'status': 'WARNING',
                    'avg_ms': avg_time,
                    'message': 'Performance varies significantly'
                }
                print("   ⚠️ Performance varies significantly")
        else:
            self.results['performance'] = {
                'status': 'FAILED',
                'message': 'Could not measure performance'
            }
            
    def run_all_tests(self):
        """Run all verification tests"""
        print("="*80)
        print("OCR DOCUMENT SCANNER - FIX VERIFICATION TEST")
        print("="*80)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Check server connectivity first
        print("\nChecking server connectivity...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ Server returned status {response.status_code}")
                return
            print("✅ Server is online")
        except Exception as e:
            print(f"❌ Server not responding: {e}")
            print("Please ensure the server is running on port 5001")
            return
            
        # Run all tests
        self.test_rate_limiting()
        self.test_v3_endpoints()
        self.test_error_handling()
        self.test_monitoring_endpoints()
        
        # Run async tests
        asyncio.run(self.test_websocket())
        
        self.test_performance_consistency()
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate final verification report"""
        print("\n" + "="*80)
        print("VERIFICATION REPORT")
        print("="*80)
        
        # Count results
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        for category, results in self.results.items():
            if isinstance(results, dict):
                if 'status' in results:
                    total_tests += 1
                    if results['status'] == 'PASSED':
                        passed_tests += 1
                    elif results['status'] == 'FAILED':
                        failed_tests += 1
                    elif results['status'] == 'WARNING':
                        warning_tests += 1
                else:
                    # Nested results
                    for test_name, test_result in results.items():
                        if isinstance(test_result, dict) and 'status' in test_result:
                            total_tests += 1
                            if test_result['status'] == 'PASSED':
                                passed_tests += 1
                            elif test_result['status'] == 'FAILED':
                                failed_tests += 1
                            elif test_result['status'] == 'WARNING':
                                warning_tests += 1
                                
        print(f"\n📊 TEST SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  ⚠️ Warnings: {warning_tests}")
        
        print(f"\n📋 DETAILED RESULTS:")
        
        # 1. Rate Limiting
        if 'rate_limiting' in self.results:
            result = self.results['rate_limiting']
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"\n1. RATE LIMITING: {status_icon} {result['status']}")
            print(f"   {result['details']}")
            
        # 2. V3 Endpoints
        if 'v3_endpoints' in self.results:
            v3_passed = sum(1 for r in self.results['v3_endpoints'].values() if r['status'] == 'PASSED')
            v3_total = len(self.results['v3_endpoints'])
            status_icon = "✅" if v3_passed == v3_total else "⚠️" if v3_passed > 0 else "❌"
            print(f"\n2. V3 ENDPOINTS: {status_icon} {v3_passed}/{v3_total} working")
            for endpoint, result in self.results['v3_endpoints'].items():
                icon = "✅" if result['status'] == 'PASSED' else "❌"
                print(f"   {icon} {endpoint}: {result['message']}")
                
        # 3. Error Handling
        if 'error_handling' in self.results:
            eh_passed = sum(1 for r in self.results['error_handling'].values() if r['status'] == 'PASSED')
            eh_total = len(self.results['error_handling'])
            status_icon = "✅" if eh_passed == eh_total else "⚠️" if eh_passed > 0 else "❌"
            print(f"\n3. ERROR HANDLING: {status_icon} {eh_passed}/{eh_total} correct")
            for test, result in self.results['error_handling'].items():
                icon = "✅" if result['status'] == 'PASSED' else "❌"
                print(f"   {icon} {test}: {result['message']}")
                
        # 4. Monitoring
        if 'monitoring' in self.results:
            mon_passed = sum(1 for r in self.results['monitoring'].values() if r['status'] == 'PASSED')
            mon_total = len(self.results['monitoring'])
            status_icon = "✅" if mon_passed == mon_total else "⚠️" if mon_passed > 0 else "❌"
            print(f"\n4. MONITORING: {status_icon} {mon_passed}/{mon_total} active")
            for endpoint, result in self.results['monitoring'].items():
                icon = "✅" if result['status'] == 'PASSED' else "❌"
                print(f"   {icon} {endpoint}: {result['message']}")
                
        # 5. WebSocket
        if 'websocket' in self.results:
            result = self.results['websocket']
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"\n5. WEBSOCKET: {status_icon} {result['status']}")
            print(f"   {result['message']}")
            
        # 6. Performance
        if 'performance' in self.results:
            result = self.results['performance']
            status_icon = "✅" if result['status'] == 'PASSED' else "⚠️" if result['status'] == 'WARNING' else "❌"
            print(f"\n6. PERFORMANCE: {status_icon} {result['status']}")
            if 'avg_ms' in result:
                print(f"   Average response time: {result['avg_ms']:.2f}ms")
            print(f"   {result['message']}")
            
        # Final Assessment
        print("\n" + "="*80)
        print("FINAL ASSESSMENT")
        print("="*80)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine production readiness
        critical_issues = []
        
        if 'rate_limiting' in self.results and self.results['rate_limiting']['status'] == 'FAILED':
            critical_issues.append("Rate limiting not working")
            
        if 'v3_endpoints' in self.results:
            v3_working = sum(1 for r in self.results['v3_endpoints'].values() if r['status'] == 'PASSED')
            if v3_working < len(self.results['v3_endpoints']):
                critical_issues.append(f"V3 endpoints partially working ({v3_working}/{len(self.results['v3_endpoints'])})")
                
        if 'error_handling' in self.results:
            eh_working = sum(1 for r in self.results['error_handling'].values() if r['status'] == 'PASSED')
            if eh_working < len(self.results['error_handling']) * 0.8:  # Allow 20% failure
                critical_issues.append(f"Error handling issues ({eh_working}/{len(self.results['error_handling'])} correct)")
                
        print(f"\n📈 Overall Success Rate: {success_rate:.1f}%")
        
        if critical_issues:
            print("\n⚠️ CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  - {issue}")
            print("\n🔴 PRODUCTION READINESS: NO - Critical issues need to be addressed")
        elif success_rate >= 90:
            print("\n🟢 PRODUCTION READINESS: YES - All major systems operational")
        elif success_rate >= 70:
            print("\n🟡 PRODUCTION READINESS: ALMOST - Minor issues should be addressed")
        else:
            print("\n🔴 PRODUCTION READINESS: NO - Significant issues need to be fixed")
            
        # Save detailed report
        filename = f"fix_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results,
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'warnings': warning_tests,
                    'success_rate': success_rate,
                    'critical_issues': critical_issues
                }
            }, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: {filename}")

def main():
    tester = FixVerificationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
