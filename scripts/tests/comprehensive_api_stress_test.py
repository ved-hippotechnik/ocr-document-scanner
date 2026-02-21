#!/usr/bin/env python3
"""
Comprehensive API Stress Testing and Security Assessment
for OCR Document Scanner Backend API
"""

import asyncio
import aiohttp
import time
import json
import statistics
import threading
import base64
import random
import string
import hashlib
import concurrent.futures
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Any, Optional
import logging
import io
import os
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'stress_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class APIStressTester:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = None
        self.results = {
            'load_tests': {},
            'security_tests': {},
            'performance_metrics': {},
            'vulnerability_findings': [],
            'recommendations': []
        }
        self.response_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.status_codes = defaultdict(lambda: defaultdict(int))
        
        # Test endpoints configuration
        self.endpoints = {
            'health': {
                'paths': ['/health', '/api/v2/health', '/api/v3/health'],
                'method': 'GET',
                'category': 'monitoring'
            },
            'stats': {
                'paths': ['/api/stats', '/api/documents'],
                'method': 'GET', 
                'category': 'data'
            },
            'processors': {
                'paths': ['/api/processors', '/api/v3/processors'],
                'method': 'GET',
                'category': 'data'
            },
            'scan': {
                'paths': ['/api/scan', '/api/v2/scan', '/api/v3/scan'],
                'method': 'POST',
                'category': 'upload',
                'requires_file': True
            },
            'auth': {
                'paths': ['/api/auth/login', '/api/auth/register'],
                'method': 'POST',
                'category': 'auth'
            },
            'analytics': {
                'paths': ['/api/analytics/dashboard', '/api/analytics/trends'],
                'method': 'GET',
                'category': 'analytics'
            },
            'batch': {
                'paths': ['/api/batch/process', '/api/batch/status'],
                'method': 'GET',
                'category': 'batch'
            }
        }
        
    async def create_session(self):
        """Create aiohttp session with appropriate timeouts"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=1000, limit_per_host=100)
        )
        
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            
    def create_test_image(self, width: int = 800, height: int = 600) -> bytes:
        """Create a test image for file upload tests"""
        img = Image.new('RGB', (width, height), color='white')
        
        # Add some text to make it look like a document
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
            except:
                font = ImageFont.load_default()
                
            draw.text((50, 50), "Test Document", fill='black', font=font)
            draw.text((50, 100), "ID Number: 123456789", fill='black', font=font)
            draw.text((50, 150), "Name: Test User", fill='black', font=font)
            draw.text((50, 200), "Date: 2024-01-01", fill='black', font=font)
        except ImportError:
            # PIL might not have ImageDraw/ImageFont
            pass
            
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def create_malicious_payloads(self) -> List[Dict]:
        """Create various malicious payloads for security testing"""
        return [
            # SQL Injection attempts
            {"type": "sql_injection", "payload": "'; DROP TABLE scan_history; --"},
            {"type": "sql_injection", "payload": "1' OR '1'='1"},
            {"type": "sql_injection", "payload": "admin'/*"},
            {"type": "sql_injection", "payload": "1' UNION SELECT * FROM users--"},
            
            # XSS attempts
            {"type": "xss", "payload": "<script>alert('XSS')</script>"},
            {"type": "xss", "payload": "javascript:alert('XSS')"},
            {"type": "xss", "payload": "<img src=x onerror=alert('XSS')>"},
            {"type": "xss", "payload": "'><script>alert('XSS')</script>"},
            
            # Path traversal
            {"type": "path_traversal", "payload": "../../../etc/passwd"},
            {"type": "path_traversal", "payload": "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"},
            {"type": "path_traversal", "payload": "....//....//....//etc/passwd"},
            
            # Command injection
            {"type": "command_injection", "payload": "; cat /etc/passwd"},
            {"type": "command_injection", "payload": "| ls -la"},
            {"type": "command_injection", "payload": "$(whoami)"},
            {"type": "command_injection", "payload": "`id`"},
            
            # LDAP injection
            {"type": "ldap_injection", "payload": "*)(uid=*))(|(uid=*"},
            {"type": "ldap_injection", "payload": "*)(|(password=*)"},
            
            # NoSQL injection
            {"type": "nosql_injection", "payload": "'; return db.users.find(); var dummy='"},
            {"type": "nosql_injection", "payload": "{$ne: null}"},
            
            # Large payloads (DoS attempts)
            {"type": "dos", "payload": "A" * 10000},
            {"type": "dos", "payload": "A" * 100000},
            
            # Null bytes
            {"type": "null_byte", "payload": "test\x00.jpg"},
            {"type": "null_byte", "payload": "../../etc/passwd\x00.png"},
            
            # Unicode/encoding attacks
            {"type": "unicode", "payload": "\u0000\u0001\u0002\u0003"},
            {"type": "unicode", "payload": "%00%01%02%03"},
        ]
        
    async def test_single_endpoint(self, url: str, method: str = 'GET', 
                                 data: Any = None, files: Dict = None,
                                 headers: Dict = None) -> Dict:
        """Test a single endpoint and return metrics"""
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    content = await response.text()
                    return {
                        'url': url,
                        'method': method,
                        'status_code': response.status,
                        'response_time': response_time,
                        'content_length': len(content),
                        'success': 200 <= response.status < 400,
                        'headers': dict(response.headers),
                        'content': content[:1000]  # First 1000 chars for analysis
                    }
            elif method.upper() == 'POST':
                if files:
                    # Handle file uploads
                    form_data = aiohttp.FormData()
                    for key, value in files.items():
                        if isinstance(value, bytes):
                            form_data.add_field(key, value, filename='test.jpg', 
                                              content_type='image/jpeg')
                        else:
                            form_data.add_field(key, value)
                    
                    if data:
                        for key, value in data.items():
                            form_data.add_field(key, str(value))
                            
                    async with self.session.post(url, data=form_data, headers=headers) as response:
                        response_time = time.time() - start_time
                        content = await response.text()
                        return {
                            'url': url,
                            'method': method,
                            'status_code': response.status,
                            'response_time': response_time,
                            'content_length': len(content),
                            'success': 200 <= response.status < 400,
                            'headers': dict(response.headers),
                            'content': content[:1000]
                        }
                else:
                    # Handle JSON/form data
                    if data and isinstance(data, dict):
                        json_data = data if headers and 'application/json' in headers.get('Content-Type', '') else None
                        form_data = data if not json_data else None
                    else:
                        json_data = None
                        form_data = data
                        
                    async with self.session.post(url, json=json_data, data=form_data, headers=headers) as response:
                        response_time = time.time() - start_time
                        content = await response.text()
                        return {
                            'url': url,
                            'method': method,
                            'status_code': response.status,
                            'response_time': response_time,
                            'content_length': len(content),
                            'success': 200 <= response.status < 400,
                            'headers': dict(response.headers),
                            'content': content[:1000]
                        }
                        
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'url': url,
                'method': method,
                'status_code': 0,
                'response_time': response_time,
                'content_length': 0,
                'success': False,
                'error': str(e),
                'headers': {},
                'content': ''
            }
            
    async def load_test_endpoint(self, endpoint_config: Dict, concurrent_users: int = 10,
                               requests_per_user: int = 10) -> Dict:
        """Perform load testing on a specific endpoint"""
        logger.info(f"Load testing {endpoint_config['category']} endpoints with {concurrent_users} users, {requests_per_user} requests each")
        
        results = []
        tasks = []
        
        for path in endpoint_config['paths']:
            url = f"{self.base_url}{path}"
            
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    if endpoint_config.get('requires_file'):
                        # Create test image for file upload
                        test_image = self.create_test_image()
                        files = {'image': test_image}
                        task = self.test_single_endpoint(url, endpoint_config['method'], files=files)
                    elif endpoint_config['category'] == 'auth':
                        # Create test auth data
                        test_data = {
                            'username': f'testuser_{user}_{request}',
                            'email': f'test_{user}_{request}@example.com',
                            'password': 'TestPassword123!'
                        }
                        task = self.test_single_endpoint(url, endpoint_config['method'], data=test_data)
                    else:
                        task = self.test_single_endpoint(url, endpoint_config['method'])
                    
                    tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_results = [r for r in results if isinstance(r, dict)]
        error_results = [r for r in results if not isinstance(r, dict)]
        
        if error_results:
            logger.warning(f"Found {len(error_results)} error results: {error_results[:3]}")
        
        # Calculate metrics
        if valid_results:
            response_times = [r['response_time'] for r in valid_results if 'response_time' in r]
            success_count = sum(1 for r in valid_results if r.get('success', False))
            
            metrics = {
                'endpoint_category': endpoint_config['category'],
                'total_requests': len(valid_results),
                'successful_requests': success_count,
                'failed_requests': len(valid_results) - success_count,
                'success_rate': (success_count / len(valid_results)) * 100 if valid_results else 0,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'p50_response_time': statistics.median(response_times) if response_times else 0,
                'p95_response_time': self.percentile(response_times, 95) if response_times else 0,
                'p99_response_time': self.percentile(response_times, 99) if response_times else 0,
                'requests_per_second': len(valid_results) / max(response_times) if response_times else 0,
                'status_code_distribution': {},
                'errors': []
            }
            
            # Status code distribution
            for result in valid_results:
                status = result.get('status_code', 0)
                metrics['status_code_distribution'][status] = metrics['status_code_distribution'].get(status, 0) + 1
            
            # Collect unique errors
            errors = set()
            for result in valid_results:
                if not result.get('success', False):
                    error_msg = result.get('error', f"HTTP {result.get('status_code', 'Unknown')}")
                    errors.add(error_msg)
            
            metrics['errors'] = list(errors)
            
            return metrics
        else:
            return {
                'endpoint_category': endpoint_config['category'],
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0,
                'error': 'No valid results obtained'
            }
    
    @staticmethod
    def percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    async def security_test_endpoint(self, url: str, method: str = 'GET') -> List[Dict]:
        """Test endpoint for security vulnerabilities"""
        vulnerabilities = []
        malicious_payloads = self.create_malicious_payloads()
        
        logger.info(f"Security testing {url}")
        
        # Test 1: Check security headers
        try:
            response_data = await self.test_single_endpoint(url, method)
            headers = response_data.get('headers', {})
            
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': None,  # Just check presence
                'Content-Security-Policy': None,
                'Referrer-Policy': None
            }
            
            for header, expected in security_headers.items():
                if header not in headers:
                    vulnerabilities.append({
                        'type': 'missing_security_header',
                        'severity': 'medium',
                        'url': url,
                        'description': f'Missing security header: {header}',
                        'recommendation': f'Add {header} header to responses'
                    })
                elif expected and isinstance(expected, list):
                    if headers[header] not in expected:
                        vulnerabilities.append({
                            'type': 'weak_security_header',
                            'severity': 'low',
                            'url': url,
                            'description': f'Weak {header} header value: {headers[header]}',
                            'recommendation': f'Set {header} to one of: {expected}'
                        })
        except Exception as e:
            logger.error(f"Error checking security headers for {url}: {e}")
        
        # Test 2: Input validation tests
        for payload_info in malicious_payloads[:10]:  # Test first 10 to avoid overwhelming
            try:
                if method == 'POST':
                    if 'scan' in url:  # File upload endpoint
                        # Test malicious file content
                        malicious_content = payload_info['payload'].encode('utf-8', errors='ignore')
                        files = {'image': malicious_content}
                        response_data = await self.test_single_endpoint(url, method, files=files)
                    else:
                        # Test malicious form data
                        data = {'test_param': payload_info['payload']}
                        response_data = await self.test_single_endpoint(url, method, data=data)
                else:
                    # Test malicious query parameters
                    malicious_url = f"{url}?test_param={payload_info['payload']}"
                    response_data = await self.test_single_endpoint(malicious_url, method)
                
                # Analyze response for potential vulnerabilities
                if response_data.get('status_code') == 500:
                    vulnerabilities.append({
                        'type': 'input_validation_error',
                        'severity': 'medium',
                        'url': url,
                        'payload_type': payload_info['type'],
                        'payload': payload_info['payload'][:100],
                        'description': f'Server error (500) with {payload_info["type"]} payload',
                        'recommendation': 'Implement proper input validation and error handling'
                    })
                elif payload_info['payload'] in response_data.get('content', ''):
                    if payload_info['type'] in ['xss', 'sql_injection']:
                        vulnerabilities.append({
                            'type': 'potential_injection',
                            'severity': 'high',
                            'url': url,
                            'payload_type': payload_info['type'],
                            'payload': payload_info['payload'][:100],
                            'description': f'Payload reflected in response - potential {payload_info["type"]}',
                            'recommendation': 'Implement proper input sanitization and output encoding'
                        })
                
                await asyncio.sleep(0.1)  # Rate limit our security tests
                
            except Exception as e:
                logger.debug(f"Security test error for {url} with payload {payload_info['type']}: {e}")
        
        # Test 3: Rate limiting
        try:
            rapid_requests = []
            for i in range(50):  # Try 50 rapid requests
                task = self.test_single_endpoint(url, method)
                rapid_requests.append(task)
            
            rate_limit_results = await asyncio.gather(*rapid_requests, return_exceptions=True)
            rate_limit_blocked = sum(1 for r in rate_limit_results 
                                   if isinstance(r, dict) and r.get('status_code') == 429)
            
            if rate_limit_blocked == 0:
                vulnerabilities.append({
                    'type': 'weak_rate_limiting',
                    'severity': 'medium',
                    'url': url,
                    'description': 'No rate limiting detected - sent 50 rapid requests without blocking',
                    'recommendation': 'Implement proper rate limiting to prevent abuse'
                })
                
        except Exception as e:
            logger.error(f"Rate limiting test error for {url}: {e}")
        
        return vulnerabilities
    
    async def test_authentication_security(self) -> List[Dict]:
        """Test authentication and authorization security"""
        vulnerabilities = []
        auth_endpoints = ['/api/auth/login', '/api/auth/register']
        
        logger.info("Testing authentication security")
        
        for endpoint in auth_endpoints:
            url = f"{self.base_url}{endpoint}"
            
            # Test 1: Weak password acceptance
            weak_passwords = ['123456', 'password', 'abc123', '123', 'qwerty', 'admin']
            for weak_pass in weak_passwords:
                try:
                    data = {
                        'username': 'testuser',
                        'email': 'test@example.com',
                        'password': weak_pass
                    }
                    response_data = await self.test_single_endpoint(url, 'POST', data=data)
                    
                    if response_data.get('success', False):
                        vulnerabilities.append({
                            'type': 'weak_password_accepted',
                            'severity': 'high',
                            'url': url,
                            'description': f'Weak password "{weak_pass}" was accepted',
                            'recommendation': 'Implement strong password requirements'
                        })
                except Exception as e:
                    logger.debug(f"Weak password test error: {e}")
            
            # Test 2: SQL injection in auth
            sql_payloads = ["admin'--", "admin'/*", "' OR '1'='1", "' OR 1=1--"]
            for payload in sql_payloads:
                try:
                    data = {
                        'username': payload,
                        'password': 'anything'
                    }
                    response_data = await self.test_single_endpoint(url, 'POST', data=data)
                    
                    if response_data.get('success', False):
                        vulnerabilities.append({
                            'type': 'sql_injection_auth',
                            'severity': 'critical',
                            'url': url,
                            'payload': payload,
                            'description': f'Possible SQL injection bypass in authentication',
                            'recommendation': 'Use parameterized queries and proper input validation'
                        })
                except Exception as e:
                    logger.debug(f"Auth SQL injection test error: {e}")
        
        return vulnerabilities
    
    async def test_file_upload_security(self) -> List[Dict]:
        """Test file upload security vulnerabilities"""
        vulnerabilities = []
        upload_endpoints = ['/api/scan', '/api/v2/scan', '/api/v3/scan']
        
        logger.info("Testing file upload security")
        
        for endpoint in upload_endpoints:
            url = f"{self.base_url}{endpoint}"
            
            # Test 1: Malicious file types
            malicious_files = [
                {'name': 'test.php', 'content': b'<?php system($_GET["cmd"]); ?>', 'type': 'application/x-php'},
                {'name': 'test.jsp', 'content': b'<%Runtime.getRuntime().exec(request.getParameter("cmd"));%>', 'type': 'application/x-jsp'},
                {'name': 'test.exe', 'content': b'MZ\x90\x00' + b'A' * 100, 'type': 'application/x-executable'},
                {'name': 'test.bat', 'content': b'@echo off\ndir', 'type': 'application/x-bat'},
                {'name': '../../../test.txt', 'content': b'path traversal test', 'type': 'text/plain'},
            ]
            
            for malicious_file in malicious_files:
                try:
                    files = {'image': malicious_file['content']}
                    headers = {'Content-Type': 'multipart/form-data'}
                    response_data = await self.test_single_endpoint(url, 'POST', files=files, headers=headers)
                    
                    if response_data.get('success', False):
                        vulnerabilities.append({
                            'type': 'malicious_file_accepted',
                            'severity': 'high',
                            'url': url,
                            'filename': malicious_file['name'],
                            'description': f'Malicious file {malicious_file["name"]} was accepted',
                            'recommendation': 'Implement proper file type validation and scanning'
                        })
                        
                    # Check for path traversal in response
                    if '../' in malicious_file['name'] and malicious_file['name'] in response_data.get('content', ''):
                        vulnerabilities.append({
                            'type': 'path_traversal_vulnerability',
                            'severity': 'high',
                            'url': url,
                            'description': 'Path traversal sequence reflected in response',
                            'recommendation': 'Sanitize file names and prevent directory traversal'
                        })
                        
                except Exception as e:
                    logger.debug(f"Malicious file test error for {malicious_file['name']}: {e}")
            
            # Test 2: Large file upload (DoS)
            try:
                large_file = b'A' * (20 * 1024 * 1024)  # 20MB file
                files = {'image': large_file}
                response_data = await self.test_single_endpoint(url, 'POST', files=files)
                
                if response_data.get('success', False):
                    vulnerabilities.append({
                        'type': 'large_file_accepted',
                        'severity': 'medium',
                        'url': url,
                        'description': 'Large file (20MB) was accepted - potential DoS vector',
                        'recommendation': 'Implement proper file size limits'
                    })
            except Exception as e:
                logger.debug(f"Large file test error: {e}")
        
        return vulnerabilities
    
    async def performance_benchmark(self) -> Dict:
        """Run performance benchmarks"""
        logger.info("Running performance benchmarks")
        
        # Test different load patterns
        load_patterns = [
            {'users': 1, 'requests': 10, 'name': 'baseline'},
            {'users': 5, 'requests': 10, 'name': 'light_load'},
            {'users': 10, 'requests': 10, 'name': 'medium_load'},
            {'users': 20, 'requests': 10, 'name': 'heavy_load'},
            {'users': 50, 'requests': 5, 'name': 'spike_test'},
        ]
        
        benchmark_results = {}
        
        for pattern in load_patterns:
            logger.info(f"Running {pattern['name']} test: {pattern['users']} users, {pattern['requests']} requests each")
            
            # Test core endpoints under load
            pattern_results = {}
            for endpoint_name, endpoint_config in self.endpoints.items():
                if endpoint_name in ['health', 'stats', 'processors']:  # Test most stable endpoints
                    try:
                        result = await self.load_test_endpoint(
                            endpoint_config, 
                            concurrent_users=pattern['users'],
                            requests_per_user=pattern['requests']
                        )
                        pattern_results[endpoint_name] = result
                    except Exception as e:
                        logger.error(f"Benchmark error for {endpoint_name}: {e}")
                        pattern_results[endpoint_name] = {'error': str(e)}
            
            benchmark_results[pattern['name']] = pattern_results
            
            # Wait between tests to let system recover
            await asyncio.sleep(5)
        
        return benchmark_results
    
    async def run_comprehensive_test(self) -> Dict:
        """Run all tests and compile comprehensive report"""
        logger.info("Starting comprehensive API stress test and security assessment")
        
        await self.create_session()
        
        try:
            # 1. Load Testing
            logger.info("=== LOAD TESTING PHASE ===")
            load_test_results = {}
            
            for endpoint_name, endpoint_config in self.endpoints.items():
                try:
                    if endpoint_name not in ['scan']:  # Skip heavy file upload for initial load tests
                        result = await self.load_test_endpoint(endpoint_config)
                        load_test_results[endpoint_name] = result
                        await asyncio.sleep(2)  # Brief pause between endpoint tests
                except Exception as e:
                    logger.error(f"Load test error for {endpoint_name}: {e}")
                    load_test_results[endpoint_name] = {'error': str(e)}
            
            self.results['load_tests'] = load_test_results
            
            # 2. Security Testing
            logger.info("=== SECURITY TESTING PHASE ===")
            all_vulnerabilities = []
            
            # Test each endpoint for security issues
            for endpoint_name, endpoint_config in self.endpoints.items():
                for path in endpoint_config['paths']:
                    url = f"{self.base_url}{path}"
                    try:
                        vulnerabilities = await self.security_test_endpoint(url, endpoint_config['method'])
                        all_vulnerabilities.extend(vulnerabilities)
                    except Exception as e:
                        logger.error(f"Security test error for {url}: {e}")
            
            # Test authentication security
            try:
                auth_vulnerabilities = await self.test_authentication_security()
                all_vulnerabilities.extend(auth_vulnerabilities)
            except Exception as e:
                logger.error(f"Authentication security test error: {e}")
            
            # Test file upload security
            try:
                upload_vulnerabilities = await self.test_file_upload_security()
                all_vulnerabilities.extend(upload_vulnerabilities)
            except Exception as e:
                logger.error(f"File upload security test error: {e}")
            
            self.results['vulnerability_findings'] = all_vulnerabilities
            
            # 3. Performance Benchmarking
            logger.info("=== PERFORMANCE BENCHMARKING PHASE ===")
            try:
                benchmark_results = await self.performance_benchmark()
                self.results['performance_metrics'] = benchmark_results
            except Exception as e:
                logger.error(f"Performance benchmark error: {e}")
                self.results['performance_metrics'] = {'error': str(e)}
            
            # 4. Generate Recommendations
            self.results['recommendations'] = self.generate_recommendations()
            
        finally:
            await self.close_session()
        
        return self.results
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze load test results
        load_results = self.results.get('load_tests', {})
        for endpoint, metrics in load_results.items():
            if isinstance(metrics, dict) and 'avg_response_time' in metrics:
                if metrics['avg_response_time'] > 2.0:
                    recommendations.append({
                        'category': 'performance',
                        'priority': 'high',
                        'issue': f'{endpoint} endpoint has slow response time',
                        'current_value': f"{metrics['avg_response_time']:.2f}s average",
                        'recommendation': 'Optimize database queries, add caching, or implement connection pooling',
                        'target': 'Response time under 1 second for 95% of requests'
                    })
                
                if metrics['success_rate'] < 95:
                    recommendations.append({
                        'category': 'reliability',
                        'priority': 'critical',
                        'issue': f'{endpoint} endpoint has low success rate',
                        'current_value': f"{metrics['success_rate']:.1f}% success rate",
                        'recommendation': 'Investigate and fix error conditions causing failures',
                        'target': 'Success rate above 99%'
                    })
        
        # Analyze security vulnerabilities
        vulnerabilities = self.results.get('vulnerability_findings', [])
        
        # Group vulnerabilities by severity
        critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'critical']
        high_vulns = [v for v in vulnerabilities if v.get('severity') == 'high']
        medium_vulns = [v for v in vulnerabilities if v.get('severity') == 'medium']
        
        if critical_vulns:
            recommendations.append({
                'category': 'security',
                'priority': 'critical',
                'issue': f'Found {len(critical_vulns)} critical security vulnerabilities',
                'current_value': f"Critical vulnerabilities: {[v['type'] for v in critical_vulns]}",
                'recommendation': 'Immediately address all critical security vulnerabilities before production deployment',
                'target': 'Zero critical vulnerabilities'
            })
        
        if high_vulns:
            recommendations.append({
                'category': 'security',
                'priority': 'high',
                'issue': f'Found {len(high_vulns)} high severity security issues',
                'current_value': f"High severity issues: {[v['type'] for v in high_vulns]}",
                'recommendation': 'Address high severity security issues within 1 week',
                'target': 'Minimal high-severity vulnerabilities'
            })
        
        # Add general security recommendations
        missing_headers = [v for v in vulnerabilities if v.get('type') == 'missing_security_header']
        if missing_headers:
            recommendations.append({
                'category': 'security',
                'priority': 'medium',
                'issue': 'Missing security headers',
                'current_value': f"Missing headers: {set(v['description'] for v in missing_headers)}",
                'recommendation': 'Implement all standard security headers (HSTS, CSP, X-Frame-Options, etc.)',
                'target': 'All security headers properly configured'
            })
        
        # Performance recommendations
        benchmark_results = self.results.get('performance_metrics', {})
        if benchmark_results and not isinstance(benchmark_results.get('spike_test'), str):
            spike_results = benchmark_results.get('spike_test', {})
            if spike_results:
                health_spike = spike_results.get('health', {})
                if health_spike and health_spike.get('success_rate', 100) < 90:
                    recommendations.append({
                        'category': 'scalability',
                        'priority': 'high',
                        'issue': 'Poor performance under spike load',
                        'current_value': f"Success rate under spike: {health_spike.get('success_rate', 0):.1f}%",
                        'recommendation': 'Implement auto-scaling, load balancing, and circuit breakers',
                        'target': 'Maintain >95% success rate under spike loads'
                    })
        
        # Production readiness recommendations
        recommendations.extend([
            {
                'category': 'monitoring',
                'priority': 'high',
                'issue': 'Production monitoring needed',
                'recommendation': 'Implement comprehensive monitoring with metrics, logging, and alerting',
                'target': 'Full observability stack in production'
            },
            {
                'category': 'backup',
                'priority': 'medium',
                'issue': 'Data backup strategy needed',
                'recommendation': 'Implement automated database backups and disaster recovery procedures',
                'target': 'Automated daily backups with tested recovery procedures'
            },
            {
                'category': 'documentation',
                'priority': 'medium',
                'issue': 'API documentation should be comprehensive',
                'recommendation': 'Create detailed API documentation with examples and error codes',
                'target': 'Complete OpenAPI/Swagger documentation'
            }
        ])
        
        return recommendations
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive test report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"api_stress_test_report_{timestamp}.json"
        
        # Add summary statistics
        self.results['summary'] = {
            'test_timestamp': datetime.now().isoformat(),
            'total_endpoints_tested': len(self.results.get('load_tests', {})),
            'total_vulnerabilities_found': len(self.results.get('vulnerability_findings', [])),
            'critical_vulnerabilities': len([v for v in self.results.get('vulnerability_findings', []) if v.get('severity') == 'critical']),
            'high_vulnerabilities': len([v for v in self.results.get('vulnerability_findings', []) if v.get('severity') == 'high']),
            'total_recommendations': len(self.results.get('recommendations', [])),
            'base_url': self.base_url
        }
        
        # Write detailed results to file
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Comprehensive test report saved to {output_file}")
        return output_file


async def main():
    """Main execution function"""
    tester = APIStressTester("http://localhost:5001")
    
    try:
        results = await tester.run_comprehensive_test()
        report_file = tester.generate_report()
        
        # Print summary
        print("\n" + "="*80)
        print("API STRESS TEST & SECURITY ASSESSMENT COMPLETE")
        print("="*80)
        
        summary = results.get('summary', {})
        print(f"Endpoints Tested: {summary.get('total_endpoints_tested', 'N/A')}")
        print(f"Vulnerabilities Found: {summary.get('total_vulnerabilities_found', 'N/A')}")
        print(f"Critical Issues: {summary.get('critical_vulnerabilities', 'N/A')}")
        print(f"High Severity Issues: {summary.get('high_vulnerabilities', 'N/A')}")
        print(f"Recommendations: {summary.get('total_recommendations', 'N/A')}")
        print(f"\nDetailed report: {report_file}")
        
        # Print top recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            print("\nTOP RECOMMENDATIONS:")
            print("-" * 50)
            critical_recs = [r for r in recommendations if r.get('priority') == 'critical']
            high_recs = [r for r in recommendations if r.get('priority') == 'high']
            
            for rec in (critical_recs + high_recs)[:5]:
                print(f"🚨 [{rec.get('priority', '').upper()}] {rec.get('issue', '')}")
                print(f"   → {rec.get('recommendation', '')}")
                print()
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
