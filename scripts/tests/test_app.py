#!/usr/bin/env python3
"""
Quick test script to verify the OCR application is working
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_app_import():
    """Test if the Flask app can be imported"""
    try:
        from backend.app import create_app
        print("✅ Flask app import successful")
        return True
    except Exception as e:
        print(f"❌ Flask app import failed: {e}")
        return False

def test_app_creation():
    """Test if the Flask app can be created"""
    try:
        from backend.app import create_app
        app = create_app()
        print("✅ Flask app creation successful")
        return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def test_health_endpoint():
    """Test if the health endpoint works"""
    try:
        from backend.app import create_app
        app = create_app()
        
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                return True
            else:
                print(f"❌ Health endpoint returned {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing OCR Document Scanner Application")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_app_import),
        ("App Creation Test", test_app_creation),
        ("Health Endpoint Test", test_health_endpoint),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"⚠️  {test_name} failed")
    
    print(f"\n{'=' * 50}")
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready to use.")
        print("\n📋 Next steps:")
        print("1. Start the application: python backend/run.py")
        print("2. Access health check: http://localhost:5000/health")
        print("3. Use the simplified Docker setup: docker-compose.simple.yml")
        return True
    else:
        print("❌ Some tests failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)