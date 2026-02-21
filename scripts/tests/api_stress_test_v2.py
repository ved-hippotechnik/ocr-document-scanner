#!/usr/bin/env python3
"""
API Stress Testing Suite V2 - Focused and Efficient
Tests rate limiting, V3 endpoints, security, and performance
"""

import requests
import json
import time
import concurrent.futures
import statistics
from datetime import datetime
from pathlib import Path
import traceback
from io import BytesIO
from PIL import Image
import threading
import psutil
from collections import Counter, defaultdict

# Configuration
BASE_URL = "http://localhost:5001"
RESULTS_FILE = f"stress_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

class APIStressTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': BASE_URL,
            'tests': {}
        }
        self.metrics = defaultdict(list)
        
    def generate_test_image(self):
        """Generate a small test image"""
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    def test_endpoint_availability(self):
        """Test which endpoints are available"""
        print("\n=== Testing Endpoint Availability ===")
        endpoints = [
            ('GET', '/health'),
            ('GET', '/api/processors'),
            ('GET', '/api/stats'),
            ('GET', '/api/v2/health'),
            ('GET', '/api/v3/health'),
            ('GET', '/api/v3/processors'),
            ('POST', '/api/scan'),
            ('POST', '/api/v2/scan'),
            ('POST', '/api/v3/scan'),
        ]
        
        results = []
        for method, endpoint in endpoints:
            try:
                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", timeout=5)
                
                results.append({
                    'endpoint': endpoint,
                    'method': method,
                    'status': response.status_code,
                    'available': response.status_code != 404
                })
                print(f"  {method:4} {endpoint:30} -> {response.status_code} {'✓' if response.status_code != 404 else '✗'}")
            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'method': method,
                    'error': str(e),
                    'available': False
                })
                print(f"  {method:4} {endpoint:30} -> ERROR: {str(e)[:50]}")
        
        self.results['tests']['endpoint_availability'] = results
        return results
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n=== Testing Rate Limiting ===")
        
        # Use a working endpoint
        test_endpoint = '/api/stats'  # This endpoint was confirmed working
        
        results = {
            'endpoint': test_endpoint,
            'requests_sent': 0,
            'rate_limited': 0,
            'status_codes': Counter()
        }
        
        print(f"  Sending 150 rapid requests to {test_endpoint}...")
        
        def make_request():
            try:
                response = self.session.get(f"{self.base_url}{test_endpoint}", timeout=5)
                return response.status_code
            except:
                return 0
        
        # Send requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(150)]
            
            for future in concurrent.futures.as_completed(futures):
                status = future.result()
                results['requests_sent'] += 1
                results['status_codes'][status] += 1
                if status == 429:
                    results['rate_limited'] += 1
        
        results['rate_limiting_active'] = results['rate_limited'] > 0
        
        print(f"  Requests sent: {results['requests_sent']}")
        print(f"  Rate limited (429): {results['rate_limited']}")
        print(f"  Status codes: {dict(results['status_codes'])}")
        print(f"  Rate limiting: {'✓ ACTIVE' if results['rate_limiting_active'] else '✗ NOT DETECTED'}")
        
        self.results['tests']['rate_limiting'] = results
        return results
    
    def test_file_upload_security(self):
        """Test file upload security measures"""
        print("\n=== Testing File Upload Security ===")
        
        # Find a working scan endpoint
        scan_endpoints = ['/api/scan', '/api/v2/scan', '/api/v3/scan']
        working_endpoint = None
        
        for endpoint in scan_endpoints:
            try:
                response = self.session.post(f"{self.base_url}{endpoint}", timeout=2)
                if response.status_code != 404:
                    working_endpoint = endpoint
                    break
            except:
                pass
        
        if not working_endpoint:
            print("  No scan endpoint available for testing")
            self.results['tests']['file_upload_security'] = {'error': 'No scan endpoint found'}
            return
        
        print(f"  Using endpoint: {working_endpoint}")
        results = {'endpoint': working_endpoint, 'tests': []}
        
        # Test 1: Empty file
        print("  Testing empty file...")
        try:
            response = self.session.post(
                f"{self.base_url}{working_endpoint}",
                files={'image': ('test.png', b'', 'image/png')},
                timeout=5
            )
            results['tests'].append({
                'test': 'empty_file',
                'status': response.status_code,
                'handled': response.status_code in [400, 422],
                'message': response.json().get('error', '') if response.status_code >= 400 else 'accepted'
            })
            print(f"    Empty file: {response.status_code} {'✓' if response.status_code in [400, 422] else '✗'}")
        except Exception as e:
            results['tests'].append({'test': 'empty_file', 'error': str(e)})
        
        # Test 2: Invalid file type
        print("  Testing invalid file type...")
        try:
            response = self.session.post(
                f"{self.base_url}{working_endpoint}",
                files={'image': ('test.exe', b'MZ\x90\x00', 'application/x-msdownload')},
                timeout=5
            )
            results['tests'].append({
                'test': 'invalid_type',
                'status': response.status_code,
                'handled': response.status_code in [400, 422, 415],
                'message': response.json().get('error', '') if response.status_code >= 400 else 'accepted'
            })
            print(f"    Invalid type: {response.status_code} {'✓' if response.status_code in [400, 422, 415] else '✗'}")
        except Exception as e:
            results['tests'].append({'test': 'invalid_type', 'error': str(e)})
        
        # Test 3: Path traversal attempt
        print("  Testing path traversal...")
        try:
            img = self.generate_test_image()
            response = self.session.post(
                f"{self.base_url}{working_endpoint}",
                files={'image': ('../../../etc/passwd', img, 'image/png')},
                timeout=5
            )
            results['tests'].append({
                'test': 'path_traversal',
                'status': response.status_code,
                'handled': response.status_code in [400, 403],
                'safe': '../' not in str(response.json()) if response.status_code == 200 else True
            })
            print(f"    Path traversal: {response.status_code} {'✓ BLOCKED' if response.status_code in [400, 403] or '../' not in str(response.json()) else '✗ VULNERABLE'}")
        except Exception as e:
            results['tests'].append({'test': 'path_traversal', 'error': str(e)})
        
        # Test 4: Oversized file
        print("  Testing oversized file...")
        try:
            large_data = b'x' * (20 * 1024 * 1024)  # 20MB
            response = self.session.post(
                f"{self.base_url}{working_endpoint}",
                files={'image': ('large.png', large_data, 'image/png')},
                timeout=10
            )
            results['tests'].append({
                'test': 'oversized_file',
                'status': response.status_code,
                'handled': response.status_code in [400, 413]
            })
            print(f"    Oversized file: {response.status_code} {'✓' if response.status_code in [400, 413] else '✗'}")
        except Exception as e:
            results['tests'].append({'test': 'oversized_file', 'error': str(e)})
        
        self.results['tests']['file_upload_security'] = results
        return results
    
    def test_error_handling(self):
        """Test error handling for malformed requests"""
        print("\n=== Testing Error Handling ===")
        
        results = {'tests': []}
        
        # Find working endpoints
        endpoints = {
            'scan': None,
            'auth': '/api/auth/login'
        }
        
        for endpoint in ['/api/scan', '/api/v2/scan', '/api/v3/scan']:
            try:
                response = self.session.post(f"{self.base_url}{endpoint}", timeout=2)
                if response.status_code != 404:
                    endpoints['scan'] = endpoint
                    break
            except:
                pass
        
        # Test 1: Invalid JSON
        if endpoints['auth']:
            print(f"  Testing invalid JSON on {endpoints['auth']}...")
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoints['auth']}",
                    data='{"invalid json',
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                results['tests'].append({
                    'test': 'invalid_json',
                    'endpoint': endpoints['auth'],
                    'status': response.status_code,
                    'handled': response.status_code in [400, 422]
                })
                print(f"    Invalid JSON: {response.status_code} {'✓' if response.status_code in [400, 422] else '✗'}")
            except Exception as e:
                results['tests'].append({'test': 'invalid_json', 'error': str(e)})
        
        # Test 2: Missing required fields
        if endpoints['scan']:
            print(f"  Testing missing fields on {endpoints['scan']}...")
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoints['scan']}",
                    data={},
                    timeout=5
                )
                results['tests'].append({
                    'test': 'missing_fields',
                    'endpoint': endpoints['scan'],
                    'status': response.status_code,
                    'handled': response.status_code in [400, 422]
                })
                print(f"    Missing fields: {response.status_code} {'✓' if response.status_code in [400, 422] else '✗'}")
            except Exception as e:
                results['tests'].append({'test': 'missing_fields', 'error': str(e)})
        
        self.results['tests']['error_handling'] = results
        return results
    
    def test_performance_under_load(self):
        """Test performance under different load levels"""
        print("\n=== Testing Performance Under Load ===")
        
        test_endpoint = '/api/stats'  # Use a simple endpoint
        results = {'load_levels': []}
        
        load_levels = [10, 50, 100, 200]
        
        for num_requests in load_levels:
            print(f"\n  Testing with {num_requests} concurrent requests...")
            
            response_times = []
            errors = 0
            status_counts = Counter()
            
            def make_timed_request():
                try:
                    start = time.time()
                    response = self.session.get(f"{self.base_url}{test_endpoint}", timeout=10)
                    elapsed = (time.time() - start) * 1000  # ms
                    return elapsed, response.status_code
                except Exception as e:
                    return None, 0
            
            # Execute concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(num_requests, 50)) as executor:
                futures = [executor.submit(make_timed_request) for _ in range(num_requests)]
                
                for future in concurrent.futures.as_completed(futures):
                    elapsed, status = future.result()
                    if elapsed:
                        response_times.append(elapsed)
                        status_counts[status] += 1
                    else:
                        errors += 1
                        status_counts[0] += 1
            
            if response_times:
                level_results = {
                    'concurrent_requests': num_requests,
                    'successful': len(response_times),
                    'errors': errors,
                    'response_times': {
                        'min': min(response_times),
                        'max': max(response_times),
                        'mean': statistics.mean(response_times),
                        'median': statistics.median(response_times),
                        'p95': sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0]
                    },
                    'status_codes': dict(status_counts)
                }
                
                print(f"    Success: {len(response_times)}/{num_requests}")
                print(f"    Avg response: {level_results['response_times']['mean']:.2f}ms")
                print(f"    P95 response: {level_results['response_times']['p95']:.2f}ms")
                
                results['load_levels'].append(level_results)
        
        self.results['tests']['performance'] = results
        return results
    
    def test_database_connection_pooling(self):
        """Test database connection pool handling"""
        print("\n=== Testing Database Connection Pool ===")
        
        results = {}
        
        # Test rapid sequential requests (connection reuse)
        print("  Testing connection reuse (20 sequential requests)...")
        sequential_times = []
        
        for i in range(20):
            try:
                start = time.time()
                response = self.session.get(f"{self.base_url}/api/stats", timeout=5)
                elapsed = (time.time() - start) * 1000
                if response.status_code == 200:
                    sequential_times.append(elapsed)
            except:
                pass
        
        if sequential_times:
            results['connection_reuse'] = {
                'first_request_ms': sequential_times[0],
                'avg_subsequent_ms': statistics.mean(sequential_times[1:]) if len(sequential_times) > 1 else 0,
                'speedup': sequential_times[0] / statistics.mean(sequential_times[1:]) if len(sequential_times) > 1 and statistics.mean(sequential_times[1:]) > 0 else 1
            }
            print(f"    First request: {results['connection_reuse']['first_request_ms']:.2f}ms")
            print(f"    Avg subsequent: {results['connection_reuse']['avg_subsequent_ms']:.2f}ms")
            print(f"    Speedup: {results['connection_reuse']['speedup']:.2f}x")
        
        # Test connection pool exhaustion
        print("  Testing connection pool exhaustion (100 concurrent DB requests)...")
        
        def db_intensive_request():
            try:
                response = self.session.get(f"{self.base_url}/api/stats", timeout=10)
                return response.status_code
            except:
                return 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(db_intensive_request) for _ in range(100)]
            statuses = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        errors = sum(1 for s in statuses if s >= 500 or s == 0)
        results['pool_exhaustion'] = {
            'requests': 100,
            'errors': errors,
            'handling': 'Good' if errors < 5 else 'Poor'
        }
        
        print(f"    Errors: {errors}/100")
        print(f"    Pool handling: {results['pool_exhaustion']['handling']}")
        
        self.results['tests']['database_pool'] = results
        return results
    
    def test_memory_usage(self):
        """Monitor memory usage during stress"""
        print("\n=== Testing Memory Usage Under Stress ===")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  Initial memory: {initial_memory:.2f} MB")
        
        # Generate load while monitoring memory
        print("  Generating load and monitoring memory...")
        
        memory_samples = []
        
        def monitor_memory():
            for _ in range(10):
                memory_samples.append(process.memory_info().rss / 1024 / 1024)
                time.sleep(1)
        
        # Start memory monitoring in background
        monitor_thread = threading.Thread(target=monitor_memory)
        monitor_thread.start()
        
        # Generate load
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for _ in range(100):
                futures.append(executor.submit(
                    self.session.get, 
                    f"{self.base_url}/api/stats",
                    timeout=10
                ))
            
            concurrent.futures.wait(futures)
        
        monitor_thread.join()
        
        peak_memory = max(memory_samples) if memory_samples else initial_memory
        avg_memory = statistics.mean(memory_samples) if memory_samples else initial_memory
        
        results = {
            'initial_mb': initial_memory,
            'peak_mb': peak_memory,
            'average_mb': avg_memory,
            'increase_mb': peak_memory - initial_memory,
            'increase_percent': ((peak_memory - initial_memory) / initial_memory * 100) if initial_memory > 0 else 0
        }
        
        print(f"  Peak memory: {peak_memory:.2f} MB")
        print(f"  Memory increase: {results['increase_mb']:.2f} MB ({results['increase_percent']:.1f}%)")
        
        self.results['tests']['memory_usage'] = results
        return results
    
    def compare_with_previous(self):
        """Compare with previous test results if available"""
        print("\n=== Comparison with Previous Tests ===")
        
        # Look for recent test files
        test_files = list(Path('.').glob('stress_test_report_*.json'))
        test_files.sort()
        
        if len(test_files) < 2:
            print("  No previous test results found for comparison")
            return
        
        try:
            # Load previous test
            with open(test_files[-2], 'r') as f:
                previous = json.load(f)
            
            comparison = {}
            
            # Compare rate limiting
            if 'rate_limiting' in previous.get('tests', {}):
                prev_rl = previous['tests']['rate_limiting']
                curr_rl = self.results['tests'].get('rate_limiting', {})
                
                comparison['rate_limiting'] = {
                    'previous': prev_rl.get('rate_limiting_active', False),
                    'current': curr_rl.get('rate_limiting_active', False),
                    'change': 'Improved' if curr_rl.get('rate_limiting_active') and not prev_rl.get('rate_limiting_active') else 'Same'
                }
            
            # Compare performance
            if 'performance' in previous.get('tests', {}):
                prev_perf = previous['tests']['performance'].get('load_levels', [])
                curr_perf = self.results['tests'].get('performance', {}).get('load_levels', [])
                
                if prev_perf and curr_perf:
                    # Compare response times for same load level
                    for curr_level in curr_perf:
                        req_count = curr_level['concurrent_requests']
                        prev_level = next((p for p in prev_perf if p['concurrent_requests'] == req_count), None)
                        
                        if prev_level:
                            prev_mean = prev_level['response_times']['mean']
                            curr_mean = curr_level['response_times']['mean']
                            improvement = ((prev_mean - curr_mean) / prev_mean * 100) if prev_mean > 0 else 0
                            
                            print(f"  {req_count} requests: {curr_mean:.2f}ms vs {prev_mean:.2f}ms ({improvement:+.1f}%)")
            
            self.results['comparison'] = comparison
            
        except Exception as e:
            print(f"  Error comparing with previous results: {e}")
    
    def generate_summary(self):
        """Generate test summary and recommendations"""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        summary = {
            'health_score': 100,
            'issues': [],
            'recommendations': []
        }
        
        # Check endpoint availability
        if 'endpoint_availability' in self.results['tests']:
            v3_available = any(e['endpoint'].startswith('/api/v3') and e.get('available') 
                              for e in self.results['tests']['endpoint_availability'])
            if not v3_available:
                summary['issues'].append("V3 endpoints not available")
                summary['health_score'] -= 20
                summary['recommendations'].append("Register V3 routes in Flask app")
        
        # Check rate limiting
        if 'rate_limiting' in self.results['tests']:
            if not self.results['tests']['rate_limiting'].get('rate_limiting_active'):
                summary['issues'].append("Rate limiting not active")
                summary['health_score'] -= 15
                summary['recommendations'].append("Enable rate limiting (RATE_LIMIT_ENABLED=true)")
        
        # Check file upload security
        if 'file_upload_security' in self.results['tests']:
            security_tests = self.results['tests']['file_upload_security'].get('tests', [])
            for test in security_tests:
                if test.get('test') == 'path_traversal' and not test.get('safe', True):
                    summary['issues'].append("Path traversal vulnerability")
                    summary['health_score'] -= 25
                    summary['recommendations'].append("Implement strict filename validation")
                
                if test.get('test') == 'empty_file' and not test.get('handled'):
                    summary['issues'].append("Empty files not properly handled")
                    summary['health_score'] -= 10
                    summary['recommendations'].append("Add validation for empty files")
        
        # Check performance
        if 'performance' in self.results['tests']:
            load_levels = self.results['tests']['performance'].get('load_levels', [])
            for level in load_levels:
                if level['concurrent_requests'] == 100:
                    if level['response_times']['p95'] > 1000:  # > 1 second
                        summary['issues'].append("High response times under load")
                        summary['health_score'] -= 10
                        summary['recommendations'].append("Optimize database queries and add caching")
        
        # Determine overall status
        if summary['health_score'] >= 90:
            status = "✅ EXCELLENT"
        elif summary['health_score'] >= 70:
            status = "⚠️  GOOD"
        elif summary['health_score'] >= 50:
            status = "⚠️  FAIR"
        else:
            status = "❌ NEEDS IMPROVEMENT"
        
        print(f"\nHealth Score: {summary['health_score']}/100 {status}")
        
        if summary['issues']:
            print("\n🔴 Issues Found:")
            for issue in summary['issues']:
                print(f"  - {issue}")
        
        if summary['recommendations']:
            print("\n💡 Recommendations:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
        
        self.results['summary'] = summary
        
        print("\n" + "="*50)
        
        return summary
    
    def run_all_tests(self):
        """Run all stress tests"""
        print("\n" + "="*50)
        print("API STRESS TESTING SUITE V2")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        try:
            # Check server is running
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            print(f"✓ Server is running (health check: {response.status_code})")
        except Exception as e:
            print(f"✗ Server not responding: {e}")
            return
        
        # Run all tests
        self.test_endpoint_availability()
        self.test_rate_limiting()
        self.test_file_upload_security()
        self.test_error_handling()
        self.test_performance_under_load()
        self.test_database_connection_pooling()
        self.test_memory_usage()
        self.compare_with_previous()
        self.generate_summary()
        
        # Save results
        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n✓ Results saved to: {RESULTS_FILE}")
        
        return self.results

if __name__ == "__main__":
    tester = APIStressTester()
    tester.run_all_tests()
