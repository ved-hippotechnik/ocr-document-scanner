#!/usr/bin/env python3
"""
Direct Python Testing - Test OCR application without Docker
This script tests the application directly using Python for development validation
"""

import sys
import os
import subprocess
import time
import signal
import threading
import requests
from pathlib import Path

class DirectPythonTester:
    def __init__(self):
        self.app_process = None
        self.base_url = "http://localhost:5000"
        self.project_root = Path(__file__).parent
        
    def check_python_dependencies(self):
        """Check if required Python packages are available"""
        print("🔍 Checking Python dependencies...")
        
        # Map package names to their import names
        package_imports = {
            'flask': 'flask',
            'flask_cors': 'flask_cors',
            'pillow': 'PIL',
            'opencv-python': 'cv2',
            'numpy': 'numpy',
            'pytesseract': 'pytesseract',
            'requests': 'requests'
        }
        
        missing_packages = []
        
        for package, import_name in package_imports.items():
            try:
                __import__(import_name)
                print(f"✅ {package} - Available")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} - Missing")
        
        if missing_packages:
            print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        else:
            print("✅ All required packages are available")
            return True
    
    def setup_environment(self):
        """Set up environment variables for testing"""
        print("🔧 Setting up test environment...")
        
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = 'True'
        os.environ['SECRET_KEY'] = 'test-secret-key-for-development'
        os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_ocr.db'
        os.environ['UPLOAD_FOLDER'] = str(self.project_root / 'test_uploads')
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['PYTHONPATH'] = str(self.project_root)
        
        # Create test uploads directory
        test_uploads = Path(self.project_root / 'test_uploads')
        test_uploads.mkdir(exist_ok=True)
        
        print("✅ Environment configured")
    
    def start_flask_app(self):
        """Start the Flask application in development mode"""
        print("🚀 Starting Flask application...")
        
        # Change to backend directory
        backend_dir = self.project_root / 'backend'
        
        if not backend_dir.exists():
            print("❌ Backend directory not found")
            return False
        
        # Start Flask app
        try:
            cmd = [
                sys.executable, 'run.py'
            ]
            
            self.app_process = subprocess.Popen(
                cmd,
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            
            print("✅ Flask application started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start Flask app: {e}")
            return False
    
    def wait_for_app_ready(self, timeout=30):
        """Wait for the Flask app to be ready"""
        print("⏳ Waiting for application to be ready...")
        
        for attempt in range(timeout):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Application is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            print(f"   Attempt {attempt + 1}/{timeout}...")
            time.sleep(1)
        
        print("❌ Application failed to start within timeout")
        return False
    
    def run_basic_tests(self):
        """Run basic API tests"""
        print("\n🧪 Running Basic API Tests")
        print("-" * 40)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Health Check
        total_tests += 1
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health Check - PASS")
                tests_passed += 1
            else:
                print(f"❌ Health Check - FAIL (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Health Check - FAIL ({e})")
        
        # Test 2: Processors List
        total_tests += 1
        try:
            response = requests.get(f"{self.base_url}/api/processors", timeout=5)
            if response.status_code == 200:
                data = response.json()
                processor_count = data.get('total_processors', 0)
                print(f"✅ Processors List - PASS ({processor_count} processors)")
                tests_passed += 1
            else:
                print(f"❌ Processors List - FAIL (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Processors List - FAIL ({e})")
        
        # Test 3: Basic Document Processing (if available)
        total_tests += 1
        try:
            # Create a simple test payload
            test_payload = {
                "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",  # 1x1 white pixel PNG
                "document_type": "passport"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v2/scan",
                json=test_payload,
                timeout=10
            )
            
            if response.status_code in [200, 400, 422]:  # 400/422 might be expected for invalid image
                print("✅ Basic Processing - PASS (endpoint responds)")
                tests_passed += 1
            else:
                print(f"❌ Basic Processing - FAIL (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Basic Processing - FAIL ({e})")
        
        print(f"\n📊 Test Results: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests
    
    def stop_flask_app(self):
        """Stop the Flask application"""
        if self.app_process:
            print("🛑 Stopping Flask application...")
            self.app_process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.app_process.kill()
                self.app_process.wait()
            
            print("✅ Flask application stopped")
    
    def show_app_logs(self):
        """Show application logs if available"""
        if self.app_process:
            stdout, stderr = self.app_process.communicate(timeout=1)
            if stdout:
                print("📋 Application Output:")
                print(stdout.decode('utf-8', errors='ignore'))
            if stderr:
                print("⚠️ Application Errors:")
                print(stderr.decode('utf-8', errors='ignore'))
    
    def run_full_test(self):
        """Run complete testing sequence"""
        print("🧪 OCR Document Scanner - Direct Python Testing")
        print("=" * 55)
        
        try:
            # Step 1: Check dependencies
            if not self.check_python_dependencies():
                print("\n❌ Dependencies check failed. Please install missing packages.")
                return False
            
            # Step 2: Setup environment
            self.setup_environment()
            
            # Step 3: Start Flask app
            if not self.start_flask_app():
                print("\n❌ Failed to start Flask application")
                return False
            
            # Step 4: Wait for app to be ready
            if not self.wait_for_app_ready():
                print("\n❌ Application not ready")
                self.show_app_logs()
                return False
            
            # Step 5: Run tests
            success = self.run_basic_tests()
            
            if success:
                print("\n🎉 All tests passed! Application is working correctly.")
                print(f"🌐 Access the application at: {self.base_url}")
                print("📚 API Documentation: Check the ENHANCED_DEPLOYMENT.md file")
            else:
                print("\n⚠️ Some tests failed. Check the application logs.")
            
            return success
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Testing interrupted by user")
            return False
        except Exception as e:
            print(f"\n💥 Testing encountered an error: {e}")
            return False
        finally:
            self.stop_flask_app()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Direct Python testing for OCR application')
    parser.add_argument('--keep-running', action='store_true', help='Keep the application running after tests')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    
    args = parser.parse_args()
    
    tester = DirectPythonTester()
    
    if args.port != 5000:
        tester.base_url = f"http://localhost:{args.port}"
        os.environ['PORT'] = str(args.port)
    
    success = tester.run_full_test()
    
    if args.keep_running and success:
        print(f"\n🔄 Application is running at {tester.base_url}")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Stopping application...")
            tester.stop_flask_app()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
