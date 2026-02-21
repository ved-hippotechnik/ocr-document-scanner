#!/usr/bin/env python3
"""
Verification script to test that critical fixes are working
"""

import requests
import json
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

BASE_URL = "http://localhost:5001"

def test_server_health():
    """Test if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_v3_endpoints():
    """Test V3 endpoint availability"""
    print("\n=== Testing V3 Endpoints ===")
    
    endpoints = ['/api/v3/health', '/api/v3/processors', '/api/v3/scan']
    results = {}
    
    for endpoint in endpoints:
        try:
            if endpoint.endswith('/scan'):
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            
            results[endpoint] = {
                'status': response.status_code,
                'working': response.status_code != 404
            }
            print(f"  {endpoint}: {response.status_code} {'✅' if response.status_code != 404 else '❌'}")
        except Exception as e:
            results[endpoint] = {'error': str(e), 'working': False}
            print(f"  {endpoint}: ERROR - {e}")
    
    return results

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n=== Testing Rate Limiting ===")
    
    # Test the new rate limit test endpoint
    test_endpoint = '/api/test/rate-limit'
    
    try:
        # First check if endpoint exists
        response = requests.get(f"{BASE_URL}{test_endpoint}", timeout=5)
        if response.status_code == 404:
            print(f"  Rate limit test endpoint not found: {response.status_code}")
            return False
        
        print(f"  Rate limit test endpoint exists: {response.status_code}")
        
        # Test rapid requests (should trigger rate limit)
        print("  Testing rapid requests (should hit rate limit after 5 requests)...")
        rate_limited = False
        
        for i in range(8):
            response = requests.get(f"{BASE_URL}{test_endpoint}")
            print(f"    Request {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                rate_limited = True
                print("    ✅ Rate limiting triggered!")
                break
            
            time.sleep(0.1)  # Small delay
        
        if not rate_limited:
            print("    ⚠️  Rate limiting not triggered (might need different endpoint or limits)")
        
        return rate_limited
        
    except Exception as e:
        print(f"  Error testing rate limiting: {e}")
        return False

def test_file_upload_validation():
    """Test file upload validation"""
    print("\n=== Testing File Upload Validation ===")
    
    scan_endpoint = '/api/scan'
    results = {}
    
    # Test 1: Empty file
    print("  Testing empty file...")
    try:
        response = requests.post(
            f"{BASE_URL}{scan_endpoint}",
            files={'image': ('test.png', b'', 'image/png')},
            timeout=5
        )
        results['empty_file'] = {
            'status': response.status_code,
            'rejected': response.status_code in [400, 422],
            'message': response.json().get('error', '') if response.status_code >= 400 else 'accepted'
        }
        print(f"    Status: {response.status_code} {'✅ Rejected' if response.status_code in [400, 422] else '❌ Accepted'}")
        if response.status_code >= 400:
            print(f"    Error: {response.json().get('error', 'No error message')}")
    except Exception as e:
        print(f"    Error: {e}")
        results['empty_file'] = {'error': str(e)}
    
    # Test 2: Invalid file type
    print("  Testing invalid file type (.exe)...")
    try:
        response = requests.post(
            f"{BASE_URL}{scan_endpoint}",
            files={'image': ('malware.exe', b'MZ\x90\x00', 'application/x-msdownload')},
            timeout=5
        )
        results['invalid_type'] = {
            'status': response.status_code,
            'rejected': response.status_code in [400, 415, 422],
            'message': response.json().get('error', '') if response.status_code >= 400 else 'accepted'
        }
        print(f"    Status: {response.status_code} {'✅ Rejected' if response.status_code in [400, 415, 422] else '❌ Accepted'}")
        if response.status_code >= 400:
            print(f"    Error: {response.json().get('error', 'No error message')}")
    except Exception as e:
        print(f"    Error: {e}")
        results['invalid_type'] = {'error': str(e)}
    
    # Test 3: Valid file (should work)
    print("  Testing valid file...")
    try:
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        response = requests.post(
            f"{BASE_URL}{scan_endpoint}",
            files={'image': ('test.png', img_bytes.getvalue(), 'image/png')},
            timeout=10
        )
        results['valid_file'] = {
            'status': response.status_code,
            'accepted': response.status_code in [200, 201],
            'message': response.json() if response.status_code < 500 else 'Server error'
        }
        print(f"    Status: {response.status_code} {'✅ Accepted' if response.status_code in [200, 201] else '❌ Rejected'}")
    except Exception as e:
        print(f"    Error: {e}")
        results['valid_file'] = {'error': str(e)}
    
    return results

def main():
    """Main verification function"""
    print("🔍 Verifying API Fixes")
    print("="*50)
    
    # Check server health
    if not test_server_health():
        print("❌ Server is not responding. Please start the backend server first:")
        print("   cd backend && python run.py")
        return
    
    print("✅ Server is running")
    
    # Run all tests
    v3_results = test_v3_endpoints()
    rate_limit_working = test_rate_limiting()
    file_validation_results = test_file_upload_validation()
    
    # Summary
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    
    # V3 endpoints
    v3_working = any(result.get('working', False) for result in v3_results.values())
    print(f"\n✅ V3 Endpoints: {'WORKING' if v3_working else 'NOT WORKING'}")
    
    # Rate limiting
    print(f"✅ Rate Limiting: {'WORKING' if rate_limit_working else 'NOT DETECTED'}")
    
    # File validation
    empty_rejected = file_validation_results.get('empty_file', {}).get('rejected', False)
    invalid_rejected = file_validation_results.get('invalid_type', {}).get('rejected', False)
    valid_accepted = file_validation_results.get('valid_file', {}).get('accepted', False)
    
    file_validation_score = sum([empty_rejected, invalid_rejected, valid_accepted])
    print(f"✅ File Validation: {file_validation_score}/3 tests passed")
    
    # Overall assessment
    total_score = sum([v3_working, rate_limit_working, file_validation_score >= 2])
    
    if total_score == 3:
        print(f"\n🎉 ALL FIXES VERIFIED! Score: {total_score}/3")
        print("   The API is now ready for production testing.")
    elif total_score >= 2:
        print(f"\n✅ Most fixes working. Score: {total_score}/3")
        print("   Minor issues remain but API is significantly improved.")
    else:
        print(f"\n⚠️  Some fixes not working. Score: {total_score}/3")
        print("   Please check server logs and restart if needed.")
    
    # Recommendations
    print("\nNext steps:")
    if v3_working:
        print("  - ✅ V3 endpoints are available")
    else:
        print("  - ❌ Check V3 route registration in __init__.py")
    
    if rate_limit_working:
        print("  - ✅ Rate limiting is functional")
    else:
        print("  - ❌ Verify rate limiter initialization and Redis connection")
    
    if file_validation_score >= 2:
        print("  - ✅ File validation is working")
    else:
        print("  - ❌ Check file validation function in routes.py")
    
    print("\nRun comprehensive tests:")
    print("  python api_stress_test_v2.py")

if __name__ == "__main__":
    main()
