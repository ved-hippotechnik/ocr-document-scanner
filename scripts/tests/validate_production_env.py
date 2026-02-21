#!/usr/bin/env python3
"""
Production Environment Validation Script

This script validates that all required environment variables
are properly configured for production deployment.

Usage:
    python validate_production_env.py
"""

import os
import sys
import urllib.parse
from typing import List, Dict, Any
from datetime import datetime

class ProductionValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def validate_secret_key(self, key_name: str, min_length: int = 32):
        """Validate secret keys are properly configured."""
        key_value = os.getenv(key_name)
        
        if not key_value:
            self.errors.append(f"{key_name} is not set")
            return False
            
        if key_value.startswith('CHANGE_THIS') or key_value == 'dev-secret-key':
            self.errors.append(f"{key_name} is using default/placeholder value")
            return False
            
        if len(key_value) < min_length:
            self.warnings.append(f"{key_name} is shorter than recommended {min_length} characters")
            
        self.passed.append(f"{key_name} is properly configured")
        return True
    
    def validate_database_url(self):
        """Validate database configuration."""
        db_url = os.getenv('DATABASE_URL')
        
        if not db_url:
            self.errors.append("DATABASE_URL is not set")
            return False
            
        if 'sqlite' in db_url.lower():
            self.warnings.append("Using SQLite database - consider PostgreSQL for production")
            
        if 'localhost' in db_url or '127.0.0.1' in db_url:
            self.warnings.append("Database appears to be localhost - ensure this is correct for production")
            
        try:
            parsed = urllib.parse.urlparse(db_url)
            if not parsed.username or not parsed.password:
                self.warnings.append("Database credentials not found in DATABASE_URL")
        except Exception:
            self.errors.append("DATABASE_URL format is invalid")
            return False
            
        self.passed.append("Database URL is configured")
        return True
    
    def validate_redis_config(self):
        """Validate Redis configuration."""
        redis_url = os.getenv('REDIS_URL')
        
        if not redis_url:
            self.errors.append("REDIS_URL is not set")
            return False
            
        if 'localhost' in redis_url or '127.0.0.1' in redis_url:
            self.warnings.append("Redis appears to be localhost - ensure this is correct for production")
            
        try:
            parsed = urllib.parse.urlparse(redis_url)
            if not parsed.password and 'password' not in redis_url:
                self.warnings.append("Redis password not configured - consider adding authentication")
        except Exception:
            self.errors.append("REDIS_URL format is invalid")
            return False
            
        self.passed.append("Redis URL is configured")
        return True
    
    def validate_ssl_config(self):
        """Validate SSL configuration."""
        ssl_cert = os.getenv('SSL_CERT_PATH')
        ssl_key = os.getenv('SSL_KEY_PATH')
        
        if not ssl_cert or not ssl_key:
            self.warnings.append("SSL certificates not configured - HTTPS required for production")
            return False
            
        if not os.path.exists(ssl_cert):
            self.errors.append(f"SSL certificate file not found: {ssl_cert}")
            
        if not os.path.exists(ssl_key):
            self.errors.append(f"SSL key file not found: {ssl_key}")
            
        self.passed.append("SSL configuration is set")
        return True
    
    def validate_cors_origins(self):
        """Validate CORS configuration."""
        cors_origins = os.getenv('CORS_ORIGINS')
        
        if not cors_origins:
            self.errors.append("CORS_ORIGINS is not set")
            return False
            
        if '*' in cors_origins:
            self.errors.append("CORS_ORIGINS contains wildcard (*) - security risk for production")
            return False
            
        if 'localhost' in cors_origins:
            self.warnings.append("CORS_ORIGINS contains localhost - remove for production")
            
        self.passed.append("CORS origins are configured")
        return True
    
    def validate_environment_settings(self):
        """Validate general environment settings."""
        flask_env = os.getenv('FLASK_ENV')
        debug = os.getenv('DEBUG')
        flask_debug = os.getenv('FLASK_DEBUG')
        
        if flask_env != 'production':
            self.errors.append(f"FLASK_ENV should be 'production', got '{flask_env}'")
            
        if debug and debug.lower() not in ['false', '0', 'no']:
            self.errors.append("DEBUG should be false in production")
            
        if flask_debug and flask_debug.lower() not in ['false', '0', 'no']:
            self.errors.append("FLASK_DEBUG should be false in production")
            
        self.passed.append("Environment settings validated")
    
    def validate_rate_limiting(self):
        """Validate rate limiting configuration."""
        rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED')
        
        if rate_limit_enabled != 'true':
            self.warnings.append("Rate limiting is not enabled - recommended for production")
            
        self.passed.append("Rate limiting configuration checked")
    
    def validate_monitoring(self):
        """Validate monitoring configuration."""
        prometheus_enabled = os.getenv('PROMETHEUS_ENABLED')
        metrics_enabled = os.getenv('METRICS_ENABLED')
        
        if prometheus_enabled != 'true':
            self.warnings.append("Prometheus monitoring is not enabled")
            
        if metrics_enabled != 'true':
            self.warnings.append("Metrics collection is not enabled")
            
        self.passed.append("Monitoring configuration checked")
    
    def run_validation(self) -> bool:
        """Run all validations."""
        print("=" * 80)
        print("OCR DOCUMENT SCANNER - PRODUCTION ENVIRONMENT VALIDATION")
        print("=" * 80)
        print(f"Validation run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all validations
        self.validate_secret_key('SECRET_KEY', 32)
        self.validate_secret_key('JWT_SECRET_KEY', 32)
        self.validate_database_url()
        self.validate_redis_config()
        self.validate_ssl_config()
        self.validate_cors_origins()
        self.validate_environment_settings()
        self.validate_rate_limiting()
        self.validate_monitoring()
        
        # Print results
        if self.passed:
            print("✅ PASSED CHECKS:")
            for check in self.passed:
                print(f"   ✅ {check}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   ⚠️  {warning}")
            print()
        
        if self.errors:
            print("❌ ERRORS (MUST FIX BEFORE DEPLOYMENT):")
            for error in self.errors:
                print(f"   ❌ {error}")
            print()
        
        # Overall result
        print("=" * 80)
        if self.errors:
            print("❌ PRODUCTION READINESS: FAILED")
            print(f"   {len(self.errors)} critical errors must be fixed")
            print(f"   {len(self.warnings)} warnings should be addressed")
            return False
        elif self.warnings:
            print("⚠️  PRODUCTION READINESS: CONDITIONAL")
            print(f"   {len(self.warnings)} warnings should be addressed")
            print("   Deployment possible but not recommended")
            return True
        else:
            print("✅ PRODUCTION READINESS: PASSED")
            print("   All critical checks passed")
            return True

def main():
    # Try to load .env.production if it exists
    env_file = '.env.production'
    if os.path.exists(env_file):
        print(f"Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if not os.getenv(key):  # Don't override existing env vars
                        os.environ[key] = value
    else:
        print(f"Warning: {env_file} not found, using current environment")
    
    validator = ProductionValidator()
    success = validator.run_validation()
    
    if not success:
        print("\nRecommended actions:")
        print("1. Run: python generate_production_secrets.py")
        print("2. Update .env.production with generated secrets")
        print("3. Configure database and Redis connections")
        print("4. Set up SSL certificates")
        print("5. Run this validation script again")
        sys.exit(1)
    else:
        print("\nEnvironment is ready for production deployment!")
        sys.exit(0)

if __name__ == "__main__":
    main()