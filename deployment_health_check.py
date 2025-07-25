#!/usr/bin/env python3
"""
Deployment Health Check Script
Validates environment configuration and system health for production deployment
"""

import os
import sys
import json
import logging
import time
import requests
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import subprocess
import psutil
import sqlite3
import redis
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment_health_check.log')
    ]
)
logger = logging.getLogger(__name__)

class DeploymentHealthChecker:
    """Comprehensive deployment health checker"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'unknown',
            'checks': {},
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        # Load environment variables
        self.load_environment()
        
    def load_environment(self):
        """Load environment variables from .env file if it exists"""
        env_file = Path('.env')
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv()
                logger.info("Loaded environment variables from .env file")
            except ImportError:
                logger.warning("python-dotenv not installed, skipping .env file loading")
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        logger.info("Starting deployment health check...")
        
        # System checks
        self.check_system_resources()
        self.check_python_environment()
        self.check_dependencies()
        
        # Configuration checks
        self.check_environment_variables()
        self.check_security_configuration()
        
        # Service checks
        self.check_database_connection()
        self.check_redis_connection()
        self.check_ocr_dependencies()
        
        # Application checks
        self.check_application_startup()
        self.check_api_endpoints()
        
        # Performance checks
        self.check_performance_metrics()
        
        # Security checks
        self.check_security_headers()
        self.check_file_permissions()
        
        # Determine overall status
        self.determine_overall_status()
        
        logger.info(f"Health check completed with status: {self.results['overall_status']}")
        return self.results
    
    def check_system_resources(self):
        """Check system resources"""
        logger.info("Checking system resources...")
        
        try:
            # Memory check
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_usage = memory.percent
            
            # Disk check
            disk = psutil.disk_usage('/')
            disk_gb = disk.total / (1024**3)
            disk_usage = disk.percent
            
            # CPU check
            cpu_count = psutil.cpu_count()
            cpu_usage = psutil.cpu_percent(interval=1)
            
            self.results['checks']['system_resources'] = {
                'status': 'pass',
                'memory_gb': round(memory_gb, 2),
                'memory_usage_percent': memory_usage,
                'disk_gb': round(disk_gb, 2),
                'disk_usage_percent': disk_usage,
                'cpu_count': cpu_count,
                'cpu_usage_percent': cpu_usage
            }
            
            # Resource warnings
            if memory_gb < 2:
                self.results['warnings'].append("System has less than 2GB RAM. Consider upgrading for better performance.")
            
            if disk_usage > 80:
                self.results['warnings'].append(f"Disk usage is {disk_usage}%. Consider cleaning up disk space.")
            
            if cpu_usage > 90:
                self.results['warnings'].append(f"CPU usage is {cpu_usage}%. System may be under high load.")
                
        except Exception as e:
            self.results['checks']['system_resources'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"System resource check failed: {str(e)}")
    
    def check_python_environment(self):
        """Check Python environment"""
        logger.info("Checking Python environment...")
        
        try:
            python_version = sys.version_info
            python_executable = sys.executable
            
            self.results['checks']['python_environment'] = {
                'status': 'pass',
                'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                'executable': python_executable
            }
            
            # Version check
            if python_version < (3, 8):
                self.results['errors'].append("Python version is too old. Minimum required: 3.8")
                self.results['checks']['python_environment']['status'] = 'fail'
            
            elif python_version < (3, 10):
                self.results['warnings'].append("Python version is below recommended 3.10+")
                
        except Exception as e:
            self.results['checks']['python_environment'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Python environment check failed: {str(e)}")
    
    def check_dependencies(self):
        """Check required dependencies"""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'flask', 'pytesseract', 'opencv-python', 'numpy', 'Pillow',
            'redis', 'psutil', 'requests', 'gunicorn'
        ]
        
        missing_packages = []
        installed_packages = {}
        
        for package in required_packages:
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', package],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Extract version from output
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            installed_packages[package] = line.split(': ')[1]
                            break
                else:
                    missing_packages.append(package)
                    
            except Exception as e:
                missing_packages.append(package)
                logger.error(f"Error checking package {package}: {str(e)}")
        
        if missing_packages:
            self.results['checks']['dependencies'] = {
                'status': 'fail',
                'missing_packages': missing_packages,
                'installed_packages': installed_packages
            }
            self.results['errors'].append(f"Missing required packages: {missing_packages}")
        else:
            self.results['checks']['dependencies'] = {
                'status': 'pass',
                'installed_packages': installed_packages
            }
    
    def check_environment_variables(self):
        """Check environment variables"""
        logger.info("Checking environment variables...")
        
        flask_env = os.environ.get('FLASK_ENV', 'development')
        
        if flask_env == 'production':
            required_vars = [
                'SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL', 'REDIS_URL'
            ]
        else:
            required_vars = ['SECRET_KEY']
        
        missing_vars = []
        weak_vars = []
        
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            elif var in ['SECRET_KEY', 'JWT_SECRET_KEY']:
                if len(value) < 32:
                    weak_vars.append(f"{var} is too short (minimum 32 characters)")
                elif value == 'dev-key-change-in-production':
                    weak_vars.append(f"{var} is using default development value")
        
        status = 'pass'
        if missing_vars:
            status = 'fail'
            self.results['errors'].append(f"Missing required environment variables: {missing_vars}")
        elif weak_vars:
            status = 'warning'
            self.results['warnings'].extend(weak_vars)
        
        self.results['checks']['environment_variables'] = {
            'status': status,
            'flask_env': flask_env,
            'missing_vars': missing_vars,
            'weak_vars': weak_vars
        }
    
    def check_security_configuration(self):
        """Check security configuration"""
        logger.info("Checking security configuration...")
        
        issues = []
        
        # Check CORS configuration
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        if cors_origins == '*':
            issues.append("CORS is configured to allow all origins. This is insecure for production.")
        
        # Check rate limiting
        rate_limit_enabled = os.environ.get('RATE_LIMIT_ENABLED', 'false').lower() == 'true'
        if not rate_limit_enabled:
            issues.append("Rate limiting is not enabled.")
        
        # Check debug mode
        debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
        flask_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        
        if debug_mode or flask_debug:
            issues.append("Debug mode is enabled. This should be disabled in production.")
        
        if issues:
            self.results['checks']['security_configuration'] = {
                'status': 'warning',
                'issues': issues
            }
            self.results['warnings'].extend(issues)
        else:
            self.results['checks']['security_configuration'] = {
                'status': 'pass',
                'message': 'Security configuration looks good'
            }
    
    def check_database_connection(self):
        """Check database connection"""
        logger.info("Checking database connection...")
        
        try:
            database_url = os.environ.get('DATABASE_URL', 'sqlite:///ocr_scanner.db')
            
            if database_url.startswith('sqlite:'):
                # SQLite check
                db_path = database_url.replace('sqlite:///', '')
                if not os.path.exists(db_path):
                    # Try to create database
                    conn = sqlite3.connect(db_path)
                    conn.close()
                    
                conn = sqlite3.connect(db_path)
                conn.execute('SELECT 1')
                conn.close()
                
                self.results['checks']['database_connection'] = {
                    'status': 'pass',
                    'type': 'sqlite',
                    'path': db_path
                }
                
            elif database_url.startswith('postgresql:'):
                # PostgreSQL check
                try:
                    import psycopg2
                    conn = psycopg2.connect(database_url)
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    cursor.close()
                    conn.close()
                    
                    self.results['checks']['database_connection'] = {
                        'status': 'pass',
                        'type': 'postgresql'
                    }
                    
                except ImportError:
                    self.results['checks']['database_connection'] = {
                        'status': 'fail',
                        'error': 'psycopg2 not installed for PostgreSQL connection'
                    }
                    self.results['errors'].append("psycopg2 not installed for PostgreSQL connection")
                    
            else:
                self.results['checks']['database_connection'] = {
                    'status': 'warning',
                    'message': f'Unknown database type: {database_url.split("://")[0]}'
                }
                
        except Exception as e:
            self.results['checks']['database_connection'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Database connection failed: {str(e)}")
    
    def check_redis_connection(self):
        """Check Redis connection"""
        logger.info("Checking Redis connection...")
        
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            
            r = redis.from_url(redis_url)
            r.ping()
            
            self.results['checks']['redis_connection'] = {
                'status': 'pass',
                'url': redis_url
            }
            
        except Exception as e:
            self.results['checks']['redis_connection'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['warnings'].append(f"Redis connection failed: {str(e)}")
    
    def check_ocr_dependencies(self):
        """Check OCR dependencies"""
        logger.info("Checking OCR dependencies...")
        
        try:
            # Check Tesseract
            result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                tesseract_version = result.stdout.split('\n')[0]
                
                self.results['checks']['ocr_dependencies'] = {
                    'status': 'pass',
                    'tesseract_version': tesseract_version
                }
            else:
                self.results['checks']['ocr_dependencies'] = {
                    'status': 'fail',
                    'error': 'Tesseract not found'
                }
                self.results['errors'].append("Tesseract OCR not installed or not in PATH")
                
        except Exception as e:
            self.results['checks']['ocr_dependencies'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"OCR dependency check failed: {str(e)}")
    
    def check_application_startup(self):
        """Check if application starts successfully"""
        logger.info("Checking application startup...")
        
        try:
            # Try to import the main application
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
            
            from app import create_app
            app = create_app()
            
            self.results['checks']['application_startup'] = {
                'status': 'pass',
                'message': 'Application starts successfully'
            }
            
        except Exception as e:
            self.results['checks']['application_startup'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Application startup failed: {str(e)}")
    
    def check_api_endpoints(self):
        """Check API endpoints if server is running"""
        logger.info("Checking API endpoints...")
        
        try:
            # Try to connect to health endpoint
            response = requests.get('http://localhost:5000/health', timeout=10)
            
            if response.status_code == 200:
                self.results['checks']['api_endpoints'] = {
                    'status': 'pass',
                    'health_endpoint': 'accessible'
                }
            else:
                self.results['checks']['api_endpoints'] = {
                    'status': 'warning',
                    'message': f'Health endpoint returned {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            self.results['checks']['api_endpoints'] = {
                'status': 'warning',
                'message': 'Server not running - cannot check endpoints'
            }
        except Exception as e:
            self.results['checks']['api_endpoints'] = {
                'status': 'fail',
                'error': str(e)
            }
    
    def check_performance_metrics(self):
        """Check performance-related metrics"""
        logger.info("Checking performance metrics...")
        
        try:
            # Check upload directory
            upload_dir = os.environ.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Check logs directory
            logs_dir = os.environ.get('LOGS_FOLDER', 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            self.results['checks']['performance_metrics'] = {
                'status': 'pass',
                'upload_dir': upload_dir,
                'logs_dir': logs_dir
            }
            
        except Exception as e:
            self.results['checks']['performance_metrics'] = {
                'status': 'fail',
                'error': str(e)
            }
    
    def check_security_headers(self):
        """Check security headers"""
        logger.info("Checking security headers...")
        
        try:
            # This would require the server to be running
            # For now, just check if security modules are available
            try:
                from backend.app.enhanced_security_validator import security_validator
                headers = security_validator.get_security_headers()
                
                self.results['checks']['security_headers'] = {
                    'status': 'pass',
                    'headers_configured': list(headers.keys())
                }
                
            except ImportError:
                self.results['checks']['security_headers'] = {
                    'status': 'warning',
                    'message': 'Enhanced security validator not available'
                }
                
        except Exception as e:
            self.results['checks']['security_headers'] = {
                'status': 'fail',
                'error': str(e)
            }
    
    def check_file_permissions(self):
        """Check file permissions"""
        logger.info("Checking file permissions...")
        
        try:
            # Check if critical directories are writable
            dirs_to_check = ['uploads', 'logs', 'models']
            
            for dir_name in dirs_to_check:
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                
                if not os.access(dir_name, os.W_OK):
                    self.results['errors'].append(f"Directory {dir_name} is not writable")
            
            self.results['checks']['file_permissions'] = {
                'status': 'pass',
                'message': 'File permissions are correct'
            }
            
        except Exception as e:
            self.results['checks']['file_permissions'] = {
                'status': 'fail',
                'error': str(e)
            }
    
    def determine_overall_status(self):
        """Determine overall health status"""
        has_errors = len(self.results['errors']) > 0
        has_warnings = len(self.results['warnings']) > 0
        
        failed_checks = sum(1 for check in self.results['checks'].values() 
                          if check.get('status') == 'fail')
        
        if has_errors or failed_checks > 0:
            self.results['overall_status'] = 'unhealthy'
        elif has_warnings:
            self.results['overall_status'] = 'warning'
        else:
            self.results['overall_status'] = 'healthy'
        
        # Add recommendations based on status
        if has_errors:
            self.results['recommendations'].append("Fix all errors before deploying to production")
        
        if has_warnings:
            self.results['recommendations'].append("Review and address warnings for optimal security and performance")
        
        if self.results['overall_status'] == 'healthy':
            self.results['recommendations'].append("System is ready for deployment")
    
    def generate_report(self, filename: str = None):
        """Generate a detailed report"""
        if filename is None:
            filename = f"health_check_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Health check report saved to {filename}")
        return filename

def main():
    """Main function"""
    checker = DeploymentHealthChecker()
    results = checker.run_all_checks()
    
    # Generate report
    report_file = checker.generate_report()
    
    # Print summary
    print("\n" + "="*50)
    print("DEPLOYMENT HEALTH CHECK SUMMARY")
    print("="*50)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results['errors']:
        print("\nERRORS:")
        for error in results['errors']:
            print(f"  ❌ {error}")
    
    if results['warnings']:
        print("\nWARNINGS:")
        for warning in results['warnings']:
            print(f"  ⚠️  {warning}")
    
    if results['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"  💡 {rec}")
    
    print(f"\nDetailed report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'healthy' else 1)

if __name__ == "__main__":
    main()