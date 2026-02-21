#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for OCR Document Scanner
Includes: Load Testing, Performance Testing, Security Testing
Author: API Testing Specialist
Date: 2025-01-13
"""

import asyncio
import aiohttp
import json
import time
import random
import statistics
import sys
import os
import traceback
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import psutil
import requests
from collections import defaultdict, Counter
import numpy as np
from io import BytesIO
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_URL = "http://localhost:5001"
TEST_RESULTS_DIR = Path("test_results")
TEST_RESULTS_DIR.mkdir(exist_ok=True)

# Test Configuration
class TestConfig:
    """Test configuration parameters"""
    
    # Load test parameters
    NORMAL_LOAD_RPS = [10, 20, 30, 40, 50]  # Requests per second
    PEAK_LOAD_RPS = [100, 200, 300, 400, 500]
    STRESS_LOAD_RPS = [1000, 1500, 2000]
    
    # Duration for each test phase (seconds)
    WARMUP_DURATION = 5
    TEST_DURATION = 30
    COOLDOWN_DURATION = 5
    
    # Connection settings
    MAX_CONNECTIONS = 100
    CONNECTION_TIMEOUT = 30
    REQUEST_TIMEOUT = 60
    
    # Rate limit testing
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    EXPECTED_RATE_LIMIT = 100  # Expected requests per window
    
    # Security testing
    SECURITY_PAYLOADS = {
        'sql_injection': ["' OR '1'='1", "admin' --", "1; DROP TABLE users--"],
        'xss': ["<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>"],
        'path_traversal': ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam"],
        'command_injection': ["; ls -la", "| whoami", "&& cat /etc/passwd"],
        'xxe': ['<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>']
    }

class MetricsCollector:
    """Collects and analyzes performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.status_codes: Counter = Counter()
        self.errors: List[Dict] = []
        self.rate_limit_hits = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.end_time = None
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.concurrent_connections = 0
        self.max_concurrent = 0
        self.lock = threading.Lock()
        
    def record_request(self, response_time: float, status_code: int, error: Optional[str] = None):
        """Record a single request's metrics"""
        with self.lock:
            self.response_times.append(response_time)
            self.status_codes[status_code] += 1
            
            if status_code == 429:
                self.rate_limit_hits += 1
            
            if 200 <= status_code < 300:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
            if error:
                self.errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': error,
                    'status_code': status_code
                })
    
    def record_system_metrics(self):
        """Record system resource usage"""
        with self.lock:
            self.memory_usage.append(psutil.virtual_memory().percent)
            self.cpu_usage.append(psutil.cpu_percent(interval=0.1))
    
    def update_concurrent_connections(self, delta: int):
        """Update concurrent connection count"""
        with self.lock:
            self.concurrent_connections += delta
            self.max_concurrent = max(self.max_concurrent, self.concurrent_connections)
    
    def get_statistics(self) -> Dict:
        """Calculate and return statistics"""
        if not self.response_times:
            return {'error': 'No data collected'}
        
        sorted_times = sorted(self.response_times)
        
        return {
            'summary': {
                'total_requests': len(self.response_times),
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (self.successful_requests / len(self.response_times) * 100) if self.response_times else 0,
                'rate_limit_hits': self.rate_limit_hits,
                'test_duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
                'max_concurrent_connections': self.max_concurrent
            },
            'response_times': {
                'min': min(self.response_times),
                'max': max(self.response_times),
                'mean': statistics.mean(self.response_times),
                'median': statistics.median(self.response_times),
                'stdev': statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0,
                'p50': sorted_times[int(len(sorted_times) * 0.5)],
                'p75': sorted_times[int(len(sorted_times) * 0.75)],
                'p90': sorted_times[int(len(sorted_times) * 0.90)],
                'p95': sorted_times[int(len(sorted_times) * 0.95)],
                'p99': sorted_times[int(len(sorted_times) * 0.99)]
            },
            'status_codes': dict(self.status_codes),
            'errors': self.errors[:10],  # First 10 errors
            'error_count': len(self.errors),
            'system_resources': {
                'avg_memory_usage': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max_memory_usage': max(self.memory_usage) if self.memory_usage else 0,
                'avg_cpu_usage': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max_cpu_usage': max(self.cpu_usage) if self.cpu_usage else 0
            }
        }

class APITester:
    """Main API testing class"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        self.metrics = MetricsCollector()
        self.auth_token = None
        
    def generate_test_image(self, size: Tuple[int, int] = (100, 100)) -> bytes:
        """Generate a test image for upload"""
        img = Image.new('RGB', size, color=(73, 109, 137))
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def generate_malformed_file(self) -> bytes:
        """Generate a malformed file for testing"""
        return b"Not a valid image file" + b"\x00" * 100
    
    async def make_request(self, 
                          method: str, 
                          endpoint: str, 
                          data: Optional[Dict] = None,
                          files: Optional[Dict] = None,
                          headers: Optional[Dict] = None) -> Tuple[int, float, Optional[Dict]]:
        """Make an async HTTP request and record metrics"""
        
        url = f"{self.base_url}{endpoint}"
        self.metrics.update_concurrent_connections(1)
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                # Prepare request
                kwargs = {
                    'timeout': aiohttp.ClientTimeout(total=TestConfig.REQUEST_TIMEOUT)
                }
                
                if headers:
                    kwargs['headers'] = headers
                
                if files:
                    form = aiohttp.FormData()
                    for key, value in files.items():
                        form.add_field(key, value, filename='test.png', content_type='image/png')
                    kwargs['data'] = form
                elif data:
                    kwargs['json'] = data
                
                # Make request
                async with session.request(method, url, **kwargs) as response:
                    status_code = response.status
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    
                    self.metrics.record_request(response_time, status_code)
                    
                    return status_code, response_time, response_data
                    
        except asyncio.TimeoutError:
            response_time = TestConfig.REQUEST_TIMEOUT * 1000
            self.metrics.record_request(response_time, 0, "Timeout")
            return 0, response_time, {"error": "Request timeout"}
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.metrics.record_request(response_time, 0, str(e))
            return 0, response_time, {"error": str(e)}
            
        finally:
            self.metrics.update_concurrent_connections(-1)
    
    async def test_endpoint_basic(self, endpoint: str, method: str = "GET") -> Dict:
        """Test basic endpoint functionality"""
        print(f"\nTesting {method} {endpoint}...")
        
        results = {
            'endpoint': endpoint,
            'method': method,
            'tests': []
        }
        
        # Test 1: Normal request
        status, response_time, data = await self.make_request(method, endpoint)
        results['tests'].append({
            'test': 'Normal request',
            'status': status,
            'response_time_ms': response_time,
            'passed': 200 <= status < 300
        })
        
        # Test 2: Invalid method (if GET, try POST and vice versa)
        alt_method = "POST" if method == "GET" else "GET"
        status, response_time, data = await self.make_request(alt_method, endpoint)
        results['tests'].append({
            'test': f'Invalid method ({alt_method})',
            'status': status,
            'response_time_ms': response_time,
            'passed': status in [405, 404]  # Method not allowed or not found
        })
        
        return results
    
    async def test_rate_limiting(self) -> Dict:
        """Test rate limiting functionality"""
        print("\n=== Testing Rate Limiting ===")
        
        results = {
            'test': 'Rate Limiting',
            'requests_sent': 0,
            'rate_limited': 0,
            'first_limit_at': None
        }
        
        # Send rapid requests to trigger rate limit
        tasks = []
        for i in range(150):  # Send more than expected limit
            tasks.append(self.make_request("GET", "/api/v3/health"))
        
        responses = await asyncio.gather(*tasks)
        
        for i, (status, _, _) in enumerate(responses):
            results['requests_sent'] += 1
            if status == 429:
                results['rate_limited'] += 1
                if results['first_limit_at'] is None:
                    results['first_limit_at'] = i + 1
        
        results['rate_limit_working'] = results['rate_limited'] > 0
        results['effective_limit'] = results['first_limit_at'] if results['first_limit_at'] else 'Not reached'
        
        return results
    
    async def test_file_upload_security(self) -> Dict:
        """Test file upload security"""
        print("\n=== Testing File Upload Security ===")
        
        results = {
            'test': 'File Upload Security',
            'vulnerabilities': []
        }
        
        # Test 1: Empty file
        status, _, data = await self.make_request(
            "POST", "/api/v3/scan",
            files={'image': b''}
        )
        results['empty_file_handled'] = status == 400
        
        # Test 2: Oversized file
        large_file = b'x' * (20 * 1024 * 1024)  # 20MB
        status, _, data = await self.make_request(
            "POST", "/api/v3/scan",
            files={'image': large_file}
        )
        results['oversized_file_handled'] = status in [400, 413]
        
        # Test 3: Malformed file
        status, _, data = await self.make_request(
            "POST", "/api/v3/scan",
            files={'image': self.generate_malformed_file()}
        )
        results['malformed_file_handled'] = status == 400
        
        # Test 4: Path traversal in filename
        form = aiohttp.FormData()
        form.add_field('image', self.generate_test_image(), 
                      filename='../../../etc/passwd.png',
                      content_type='image/png')
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/api/v3/scan", data=form) as response:
                    status = response.status
                    results['path_traversal_prevented'] = status in [400, 403]
            except:
                results['path_traversal_prevented'] = True
        
        return results
    
    async def test_sql_injection(self) -> Dict:
        """Test SQL injection vulnerabilities"""
        print("\n=== Testing SQL Injection Protection ===")
        
        results = {
            'test': 'SQL Injection',
            'payloads_tested': [],
            'vulnerable': False
        }
        
        for payload in TestConfig.SECURITY_PAYLOADS['sql_injection']:
            # Test in various parameters
            test_data = {
                'username': payload,
                'document_type': payload,
                'metadata': {'field': payload}
            }
            
            status, _, data = await self.make_request(
                "POST", "/api/auth/login",
                data={'username': payload, 'password': 'test'}
            )
            
            # If we get anything other than 401/400, might be vulnerable
            is_safe = status in [400, 401, 403]
            results['payloads_tested'].append({
                'payload': payload,
                'status': status,
                'safe': is_safe
            })
            
            if not is_safe and status != 0:
                results['vulnerable'] = True
        
        return results
    
    async def test_xss_protection(self) -> Dict:
        """Test XSS protection"""
        print("\n=== Testing XSS Protection ===")
        
        results = {
            'test': 'XSS Protection',
            'payloads_tested': [],
            'vulnerable': False
        }
        
        for payload in TestConfig.SECURITY_PAYLOADS['xss']:
            # Test XSS in various endpoints
            status, _, data = await self.make_request(
                "POST", "/api/v3/scan",
                data={'metadata': {'description': payload}}
            )
            
            # Check if payload is reflected without escaping
            if isinstance(data, dict) and payload in str(data):
                results['vulnerable'] = True
            
            results['payloads_tested'].append({
                'payload': payload[:30] + '...' if len(payload) > 30 else payload,
                'reflected': payload in str(data) if data else False
            })
        
        return results
    
    async def test_path_traversal(self) -> Dict:
        """Test path traversal vulnerabilities"""
        print("\n=== Testing Path Traversal Protection ===")
        
        results = {
            'test': 'Path Traversal',
            'payloads_tested': [],
            'vulnerable': False
        }
        
        for payload in TestConfig.SECURITY_PAYLOADS['path_traversal']:
            # Test in file parameter
            status, _, data = await self.make_request(
                "GET", f"/api/download/{payload}"
            )
            
            is_safe = status in [400, 403, 404]
            results['payloads_tested'].append({
                'payload': payload,
                'status': status,
                'safe': is_safe
            })
            
            if not is_safe and status == 200:
                results['vulnerable'] = True
        
        return results
    
    async def load_test(self, rps_levels: List[int], duration: int = 30) -> Dict:
        """Perform load testing at different RPS levels"""
        
        results = {
            'load_levels': []
        }
        
        for rps in rps_levels:
            print(f"\n=== Load Testing at {rps} RPS ===")
            
            self.metrics = MetricsCollector()  # Reset metrics
            self.metrics.start_time = datetime.now()
            
            # Calculate delay between requests
            delay = 1.0 / rps if rps > 0 else 1.0
            
            # System monitoring thread
            stop_monitoring = threading.Event()
            def monitor_system():
                while not stop_monitoring.is_set():
                    self.metrics.record_system_metrics()
                    time.sleep(1)
            
            monitor_thread = threading.Thread(target=monitor_system)
            monitor_thread.start()
            
            # Generate load
            tasks = []
            start_time = time.time()
            request_count = 0
            
            while time.time() - start_time < duration:
                # Randomly select endpoint
                endpoint = random.choice([
                    ("/api/v3/health", "GET", None, None),
                    ("/api/v3/processors", "GET", None, None),
                    ("/api/v3/scan", "POST", None, {'image': self.generate_test_image()})
                ])
                
                tasks.append(self.make_request(endpoint[1], endpoint[0], endpoint[2], endpoint[3]))
                request_count += 1
                
                # Control request rate
                if request_count % 10 == 0:
                    # Process batch of requests
                    await asyncio.gather(*tasks[-10:])
                
                await asyncio.sleep(delay)
            
            # Wait for remaining requests
            if tasks:
                await asyncio.gather(*tasks)
            
            # Stop monitoring
            stop_monitoring.set()
            monitor_thread.join()
            
            self.metrics.end_time = datetime.now()
            
            # Collect statistics
            stats = self.metrics.get_statistics()
            stats['target_rps'] = rps
            stats['actual_rps'] = request_count / duration
            
            results['load_levels'].append(stats)
            
            # Cool down between tests
            print(f"Cooling down for {TestConfig.COOLDOWN_DURATION} seconds...")
            await asyncio.sleep(TestConfig.COOLDOWN_DURATION)
        
        return results
    
    async def stress_test(self) -> Dict:
        """Perform stress testing to find breaking point"""
        print("\n=== STRESS TESTING - Finding Breaking Point ===")
        
        results = {
            'breaking_point': None,
            'max_sustainable_rps': 0,
            'degradation_points': []
        }
        
        rps = 10
        previous_success_rate = 100
        
        while rps <= 2000:
            print(f"\nTesting at {rps} RPS...")
            
            self.metrics = MetricsCollector()
            self.metrics.start_time = datetime.now()
            
            # Generate burst load
            tasks = []
            for _ in range(rps):
                tasks.append(self.make_request("GET", "/api/v3/health"))
            
            # Execute all requests concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.metrics.end_time = datetime.now()
            stats = self.metrics.get_statistics()
            
            success_rate = stats['summary']['success_rate']
            avg_response_time = stats['response_times']['mean']
            
            # Check for degradation
            if success_rate < 99:
                results['degradation_points'].append({
                    'rps': rps,
                    'success_rate': success_rate,
                    'avg_response_time_ms': avg_response_time
                })
            
            # Check for breaking point (success rate < 50%)
            if success_rate < 50 and results['breaking_point'] is None:
                results['breaking_point'] = rps
                break
            
            # Track maximum sustainable RPS (> 95% success rate)
            if success_rate > 95:
                results['max_sustainable_rps'] = rps
            
            # Increase load
            if rps < 100:
                rps += 10
            elif rps < 500:
                rps += 50
            else:
                rps += 100
            
            # Brief cooldown
            await asyncio.sleep(2)
        
        return results
    
    async def test_concurrent_connections(self) -> Dict:
        """Test maximum concurrent connections"""
        print("\n=== Testing Concurrent Connection Limits ===")
        
        results = {
            'max_tested': 0,
            'max_successful': 0,
            'connection_limit_found': False
        }
        
        connection_counts = [10, 50, 100, 200, 500, 1000]
        
        for count in connection_counts:
            print(f"Testing {count} concurrent connections...")
            
            self.metrics = MetricsCollector()
            
            # Create long-running requests
            tasks = []
            for _ in range(count):
                # Use scan endpoint with image to create longer processing time
                tasks.append(self.make_request(
                    "POST", "/api/v3/scan",
                    files={'image': self.generate_test_image()}
                ))
            
            # Execute all concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            successful = sum(1 for r in responses if not isinstance(r, Exception) and r[0] in range(200, 300))
            
            results['max_tested'] = count
            
            if successful == count:
                results['max_successful'] = count
            else:
                results['connection_limit_found'] = True
                break
            
            # Brief cooldown
            await asyncio.sleep(2)
        
        return results
    
    async def test_database_connection_pool(self) -> Dict:
        """Test database connection pooling"""
        print("\n=== Testing Database Connection Pool ===")
        
        results = {
            'pool_exhaustion_test': {},
            'connection_reuse': {}
        }
        
        # Test 1: Attempt to exhaust connection pool
        print("Testing connection pool exhaustion...")
        
        # Send many requests that require DB access
        tasks = []
        for _ in range(100):
            tasks.append(self.make_request("GET", "/api/stats"))
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        errors = sum(1 for r in responses if isinstance(r, Exception) or r[0] >= 500)
        
        results['pool_exhaustion_test'] = {
            'requests_sent': 100,
            'errors': errors,
            'duration_seconds': duration,
            'pool_handling': 'Good' if errors < 5 else 'Poor'
        }
        
        # Test 2: Connection reuse efficiency
        print("Testing connection reuse...")
        
        # Sequential requests to test connection reuse
        response_times = []
        for _ in range(20):
            status, response_time, _ = await self.make_request("GET", "/api/stats")
            if status == 200:
                response_times.append(response_time)
        
        if response_times:
            # First request might be slower due to connection establishment
            first_request_time = response_times[0]
            avg_subsequent = statistics.mean(response_times[1:]) if len(response_times) > 1 else 0
            
            results['connection_reuse'] = {
                'first_request_ms': first_request_time,
                'avg_subsequent_ms': avg_subsequent,
                'reuse_efficiency': 'Good' if avg_subsequent < first_request_time * 0.5 else 'Poor'
            }
        
        return results
    
    async def test_cache_effectiveness(self) -> Dict:
        """Test cache effectiveness"""
        print("\n=== Testing Cache Effectiveness ===")
        
        results = {
            'cache_hit_test': {},
            'cache_invalidation': {}
        }
        
        # Test 1: Cache hits for repeated requests
        print("Testing cache hits...")
        
        # Make same request multiple times
        endpoint = "/api/v3/processors"
        response_times = []
        
        for i in range(10):
            status, response_time, _ = await self.make_request("GET", endpoint)
            if status == 200:
                response_times.append(response_time)
        
        if len(response_times) >= 2:
            first_time = response_times[0]
            cached_times = response_times[1:]
            avg_cached = statistics.mean(cached_times)
            
            results['cache_hit_test'] = {
                'first_request_ms': first_time,
                'avg_cached_ms': avg_cached,
                'cache_speedup': f"{first_time / avg_cached:.2f}x" if avg_cached > 0 else 'N/A',
                'cache_working': avg_cached < first_time * 0.7
            }
        
        # Test 2: Cache invalidation
        print("Testing cache invalidation...")
        
        # This would require knowing specific cache invalidation triggers
        # For now, we'll test if cache has TTL by waiting
        
        await asyncio.sleep(5)  # Brief wait
        
        status, response_time_after_wait, _ = await self.make_request("GET", endpoint)
        
        results['cache_invalidation'] = {
            'response_after_wait_ms': response_time_after_wait,
            'note': 'Manual cache invalidation testing requires specific endpoints'
        }
        
        return results
    
    async def test_error_handling(self) -> Dict:
        """Test error handling capabilities"""
        print("\n=== Testing Error Handling ===")
        
        results = {
            'error_scenarios': []
        }
        
        # Test 1: Invalid JSON
        status, _, data = await self.make_request(
            "POST", "/api/v3/scan",
            data="Invalid JSON"
        )
        results['error_scenarios'].append({
            'test': 'Invalid JSON',
            'status': status,
            'handled_properly': status == 400
        })
        
        # Test 2: Missing required fields
        status, _, data = await self.make_request(
            "POST", "/api/v3/scan",
            data={}
        )
        results['error_scenarios'].append({
            'test': 'Missing required fields',
            'status': status,
            'handled_properly': status == 400
        })
        
        # Test 3: Invalid content type
        headers = {'Content-Type': 'text/plain'}
        status, _, data = await self.make_request(
            "POST", "/api/v3/scan",
            data="Plain text",
            headers=headers
        )
        results['error_scenarios'].append({
            'test': 'Invalid content type',
            'status': status,
            'handled_properly': status in [400, 415]
        })
        
        # Test 4: Nonexistent endpoint
        status, _, data = await self.make_request(
            "GET", "/api/nonexistent"
        )
        results['error_scenarios'].append({
            'test': 'Nonexistent endpoint',
            'status': status,
            'handled_properly': status == 404
        })
        
        return results
    
    async def test_authentication(self) -> Dict:
        """Test authentication and authorization"""
        print("\n=== Testing Authentication & Authorization ===")
        
        results = {
            'auth_tests': []
        }
        
        # Test 1: Access protected endpoint without auth
        status, _, data = await self.make_request(
            "GET", "/api/auth/profile"
        )
        results['auth_tests'].append({
            'test': 'Access without authentication',
            'status': status,
            'properly_blocked': status in [401, 403]
        })
        
        # Test 2: Invalid credentials
        status, _, data = await self.make_request(
            "POST", "/api/auth/login",
            data={'username': 'invalid', 'password': 'wrong'}
        )
        results['auth_tests'].append({
            'test': 'Invalid credentials',
            'status': status,
            'properly_rejected': status == 401
        })
        
        # Test 3: Malformed auth header
        headers = {'Authorization': 'InvalidToken'}
        status, _, data = await self.make_request(
            "GET", "/api/auth/profile",
            headers=headers
        )
        results['auth_tests'].append({
            'test': 'Malformed auth header',
            'status': status,
            'properly_rejected': status in [401, 403]
        })
        
        # Test 4: Expired token simulation
        # Generate a fake expired JWT (this is just for testing)
        fake_expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.invalid"
        headers = {'Authorization': f'Bearer {fake_expired_token}'}
        status, _, data = await self.make_request(
            "GET", "/api/auth/profile",
            headers=headers
        )
        results['auth_tests'].append({
            'test': 'Expired token',
            'status': status,
            'properly_rejected': status in [401, 403]
        })
        
        return results
    
    async def run_comprehensive_tests(self) -> Dict:
        """Run all comprehensive tests"""
        
        print("\n" + "="*80)
        print("    COMPREHENSIVE API TESTING SUITE")
        print("    Target: " + self.base_url)
        print("    Started: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*80)
        
        all_results = {
            'test_info': {
                'base_url': self.base_url,
                'start_time': datetime.now().isoformat(),
                'test_config': {
                    'normal_load_rps': TestConfig.NORMAL_LOAD_RPS,
                    'peak_load_rps': TestConfig.PEAK_LOAD_RPS,
                    'stress_load_rps': TestConfig.STRESS_LOAD_RPS,
                    'test_duration': TestConfig.TEST_DURATION
                }
            },
            'results': {}
        }
        
        try:
            # 1. Basic endpoint testing
            print("\n" + "="*40)
            print("PHASE 1: Basic Endpoint Testing")
            print("="*40)
            
            endpoints = [
                ("/api/v3/health", "GET"),
                ("/api/v3/processors", "GET"),
                ("/api/v3/scan", "POST"),
                ("/api/stats", "GET"),
                ("/health", "GET")
            ]
            
            endpoint_results = []
            for endpoint, method in endpoints:
                result = await self.test_endpoint_basic(endpoint, method)
                endpoint_results.append(result)
            
            all_results['results']['endpoint_tests'] = endpoint_results
            
            # 2. Security testing
            print("\n" + "="*40)
            print("PHASE 2: Security Testing")
            print("="*40)
            
            all_results['results']['security'] = {
                'file_upload': await self.test_file_upload_security(),
                'sql_injection': await self.test_sql_injection(),
                'xss': await self.test_xss_protection(),
                'path_traversal': await self.test_path_traversal(),
                'authentication': await self.test_authentication()
            }
            
            # 3. Rate limiting
            print("\n" + "="*40)
            print("PHASE 3: Rate Limiting Testing")
            print("="*40)
            
            all_results['results']['rate_limiting'] = await self.test_rate_limiting()
            
            # 4. Error handling
            print("\n" + "="*40)
            print("PHASE 4: Error Handling Testing")
            print("="*40)
            
            all_results['results']['error_handling'] = await self.test_error_handling()
            
            # 5. Performance testing
            print("\n" + "="*40)
            print("PHASE 5: Performance Testing")
            print("="*40)
            
            all_results['results']['performance'] = {
                'concurrent_connections': await self.test_concurrent_connections(),
                'database_pool': await self.test_database_connection_pool(),
                'cache_effectiveness': await self.test_cache_effectiveness()
            }
            
            # 6. Load testing
            print("\n" + "="*40)
            print("PHASE 6: Load Testing")
            print("="*40)
            
            print("\n--- Normal Load Testing ---")
            normal_load = await self.load_test(TestConfig.NORMAL_LOAD_RPS[:3], duration=20)
            all_results['results']['normal_load'] = normal_load
            
            print("\n--- Peak Load Testing ---")
            peak_load = await self.load_test(TestConfig.PEAK_LOAD_RPS[:2], duration=15)
            all_results['results']['peak_load'] = peak_load
            
            # 7. Stress testing
            print("\n" + "="*40)
            print("PHASE 7: Stress Testing")
            print("="*40)
            
            stress_results = await self.stress_test()
            all_results['results']['stress_test'] = stress_results
            
        except Exception as e:
            print(f"\n[ERROR] Test suite failed: {str(e)}")
            traceback.print_exc()
            all_results['error'] = str(e)
        
        all_results['test_info']['end_time'] = datetime.now().isoformat()
        
        return all_results

def generate_report(results: Dict) -> str:
    """Generate a comprehensive test report"""
    
    report = []
    report.append("="*80)
    report.append("COMPREHENSIVE API TEST REPORT")
    report.append("="*80)
    report.append(f"\nTest URL: {results['test_info']['base_url']}")
    report.append(f"Test Started: {results['test_info']['start_time']}")
    report.append(f"Test Completed: {results['test_info']['end_time']}")
    report.append("\n")
    
    # Executive Summary
    report.append("="*40)
    report.append("EXECUTIVE SUMMARY")
    report.append("="*40)
    
    # Calculate overall health score
    health_score = 100
    critical_issues = []
    warnings = []
    successes = []
    
    # Check security results
    if 'security' in results['results']:
        sec = results['results']['security']
        
        # File upload security
        if 'file_upload' in sec:
            fu = sec['file_upload']
            if not fu.get('empty_file_handled'):
                critical_issues.append("Empty files not properly handled")
                health_score -= 10
            if not fu.get('path_traversal_prevented'):
                critical_issues.append("Path traversal vulnerability detected")
                health_score -= 20
            else:
                successes.append("Path traversal protection working")
        
        # SQL injection
        if 'sql_injection' in sec and sec['sql_injection'].get('vulnerable'):
            critical_issues.append("SQL injection vulnerability detected")
            health_score -= 25
        else:
            successes.append("SQL injection protection working")
        
        # XSS
        if 'xss' in sec and sec['xss'].get('vulnerable'):
            critical_issues.append("XSS vulnerability detected")
            health_score -= 15
        else:
            successes.append("XSS protection working")
    
    # Check rate limiting
    if 'rate_limiting' in results['results']:
        rl = results['results']['rate_limiting']
        if rl.get('rate_limit_working'):
            successes.append(f"Rate limiting active (limit: {rl.get('effective_limit', 'unknown')} requests)")
        else:
            warnings.append("Rate limiting not detected")
            health_score -= 10
    
    # Check performance
    if 'stress_test' in results['results']:
        st = results['results']['stress_test']
        max_rps = st.get('max_sustainable_rps', 0)
        if max_rps < 50:
            warnings.append(f"Low maximum sustainable RPS: {max_rps}")
            health_score -= 10
        else:
            successes.append(f"Good performance: {max_rps} RPS sustainable")
    
    # Overall health
    if health_score >= 90:
        health_status = "EXCELLENT"
    elif health_score >= 70:
        health_status = "GOOD"
    elif health_score >= 50:
        health_status = "FAIR"
    else:
        health_status = "POOR"
    
    report.append(f"\nOVERALL HEALTH SCORE: {health_score}/100 ({health_status})")
    
    if critical_issues:
        report.append("\n🔴 CRITICAL ISSUES:")
        for issue in critical_issues:
            report.append(f"  - {issue}")
    
    if warnings:
        report.append("\n🟡 WARNINGS:")
        for warning in warnings:
            report.append(f"  - {warning}")
    
    if successes:
        report.append("\n🟢 SUCCESSES:")
        for success in successes:
            report.append(f"  - {success}")
    
    # Detailed Results
    report.append("\n" + "="*40)
    report.append("DETAILED TEST RESULTS")
    report.append("="*40)
    
    # 1. Endpoint Tests
    if 'endpoint_tests' in results['results']:
        report.append("\n1. ENDPOINT FUNCTIONALITY:")
        for endpoint in results['results']['endpoint_tests']:
            report.append(f"\n  {endpoint['method']} {endpoint['endpoint']}:")
            for test in endpoint['tests']:
                status = "✓" if test['passed'] else "✗"
                report.append(f"    {status} {test['test']}: Status {test['status']}, {test['response_time_ms']:.2f}ms")
    
    # 2. Security Tests
    if 'security' in results['results']:
        report.append("\n2. SECURITY ASSESSMENT:")
        
        sec = results['results']['security']
        
        # File upload
        if 'file_upload' in sec:
            report.append("\n  File Upload Security:")
            fu = sec['file_upload']
            report.append(f"    - Empty file handling: {'✓ Passed' if fu.get('empty_file_handled') else '✗ Failed'}")
            report.append(f"    - Oversized file handling: {'✓ Passed' if fu.get('oversized_file_handled') else '✗ Failed'}")
            report.append(f"    - Malformed file handling: {'✓ Passed' if fu.get('malformed_file_handled') else '✗ Failed'}")
            report.append(f"    - Path traversal prevention: {'✓ Passed' if fu.get('path_traversal_prevented') else '✗ Failed'}")
        
        # SQL Injection
        if 'sql_injection' in sec:
            report.append("\n  SQL Injection Protection:")
            si = sec['sql_injection']
            report.append(f"    - Vulnerable: {'✗ YES' if si.get('vulnerable') else '✓ NO'}")
            report.append(f"    - Payloads tested: {len(si.get('payloads_tested', []))}")
        
        # Authentication
        if 'authentication' in sec:
            report.append("\n  Authentication & Authorization:")
            auth = sec['authentication']
            for test in auth.get('auth_tests', []):
                status = "✓" if test.get('properly_blocked') or test.get('properly_rejected') else "✗"
                report.append(f"    {status} {test['test']}: Status {test['status']}")
    
    # 3. Rate Limiting
    if 'rate_limiting' in results['results']:
        report.append("\n3. RATE LIMITING:")
        rl = results['results']['rate_limiting']
        report.append(f"  - Rate limiting active: {'✓ Yes' if rl.get('rate_limit_working') else '✗ No'}")
        report.append(f"  - Requests sent: {rl.get('requests_sent', 0)}")
        report.append(f"  - Rate limited: {rl.get('rate_limited', 0)}")
        report.append(f"  - Effective limit: {rl.get('effective_limit', 'Not determined')}")
    
    # 4. Performance
    if 'performance' in results['results']:
        report.append("\n4. PERFORMANCE METRICS:")
        
        perf = results['results']['performance']
        
        # Concurrent connections
        if 'concurrent_connections' in perf:
            cc = perf['concurrent_connections']
            report.append(f"\n  Concurrent Connections:")
            report.append(f"    - Max tested: {cc.get('max_tested', 0)}")
            report.append(f"    - Max successful: {cc.get('max_successful', 0)}")
        
        # Database pool
        if 'database_pool' in perf:
            dp = perf['database_pool']
            if 'pool_exhaustion_test' in dp:
                pet = dp['pool_exhaustion_test']
                report.append(f"\n  Database Connection Pool:")
                report.append(f"    - Requests: {pet.get('requests_sent', 0)}")
                report.append(f"    - Errors: {pet.get('errors', 0)}")
                report.append(f"    - Pool handling: {pet.get('pool_handling', 'Unknown')}")
        
        # Cache
        if 'cache_effectiveness' in perf:
            cache = perf['cache_effectiveness']
            if 'cache_hit_test' in cache:
                cht = cache['cache_hit_test']
                report.append(f"\n  Cache Effectiveness:")
                report.append(f"    - Cache working: {'✓ Yes' if cht.get('cache_working') else '✗ No'}")
                if 'cache_speedup' in cht:
                    report.append(f"    - Cache speedup: {cht['cache_speedup']}")
    
    # 5. Load Testing
    if 'normal_load' in results['results']:
        report.append("\n5. LOAD TESTING RESULTS:")
        
        # Normal load
        report.append("\n  Normal Load:")
        for level in results['results']['normal_load'].get('load_levels', []):
            report.append(f"\n    {level['target_rps']} RPS:")
            report.append(f"      - Success rate: {level['summary']['success_rate']:.1f}%")
            report.append(f"      - Avg response: {level['response_times']['mean']:.2f}ms")
            report.append(f"      - P95 response: {level['response_times']['p95']:.2f}ms")
            report.append(f"      - Rate limit hits: {level['summary']['rate_limit_hits']}")
    
    # 6. Stress Testing
    if 'stress_test' in results['results']:
        report.append("\n6. STRESS TEST RESULTS:")
        st = results['results']['stress_test']
        report.append(f"  - Maximum sustainable RPS: {st.get('max_sustainable_rps', 0)}")
        report.append(f"  - Breaking point: {st.get('breaking_point', 'Not reached')}")
        
        if st.get('degradation_points'):
            report.append("\n  Degradation points:")
            for dp in st['degradation_points'][:3]:  # Show first 3
                report.append(f"    - At {dp['rps']} RPS: {dp['success_rate']:.1f}% success, {dp['avg_response_time_ms']:.2f}ms avg")
    
    # Recommendations
    report.append("\n" + "="*40)
    report.append("RECOMMENDATIONS")
    report.append("="*40)
    
    recommendations = []
    
    # Based on test results
    if health_score < 70:
        recommendations.append("CRITICAL: Address security vulnerabilities immediately")
    
    if 'stress_test' in results['results']:
        max_rps = results['results']['stress_test'].get('max_sustainable_rps', 0)
        if max_rps < 100:
            recommendations.append("Improve performance: Consider caching, query optimization, or scaling")
    
    if not results['results'].get('rate_limiting', {}).get('rate_limit_working'):
        recommendations.append("Enable rate limiting to prevent abuse")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report.append(f"\n{i}. {rec}")
    else:
        report.append("\nNo critical recommendations. System is performing well.")
    
    report.append("\n" + "="*80)
    report.append("END OF REPORT")
    report.append("="*80)
    
    return "\n".join(report)

async def main():
    """Main test execution"""
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✓ Server is running at {BASE_URL}")
    except Exception as e:
        print(f"✗ Server not responding at {BASE_URL}")
        print(f"  Error: {str(e)}")
        print("\nPlease ensure the backend server is running:")
        print("  cd backend && python run.py")
        return
    
    # Run tests
    tester = APITester(BASE_URL)
    results = await tester.run_comprehensive_tests()
    
    # Generate report
    report = generate_report(results)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON results
    json_file = TEST_RESULTS_DIR / f"comprehensive_test_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save text report
    report_file = TEST_RESULTS_DIR / f"comprehensive_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Print report
    print("\n" + report)
    
    print(f"\n✓ Results saved to:")
    print(f"  - JSON: {json_file}")
    print(f"  - Report: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
