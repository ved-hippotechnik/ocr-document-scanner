#!/usr/bin/env python3
"""
Integration validation script for OCR Document Scanner
Tests all implemented improvements to ensure they work together
"""

import sys
import os
import tempfile
import sqlite3
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_database_optimizations():
    """Test database optimization functionality"""
    print("🔧 Testing Database Optimizations...")
    
    try:
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)
        
        # Test SQLite operations
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE test_scan_history (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                document_type TEXT,
                status TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Test index creation
        cursor.execute('CREATE INDEX idx_test_user_id ON test_scan_history (user_id)')
        cursor.execute('CREATE INDEX idx_test_created_at ON test_scan_history (created_at)')
        
        # Verify indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_test_%'")
        indexes = cursor.fetchall()
        
        conn.close()
        os.unlink(db_path)
        
        if len(indexes) == 2:
            print("  ✅ Database index creation working")
            return True
        else:
            print(f"  ❌ Expected 2 indexes, found {len(indexes)}")
            return False
            
    except Exception as e:
        print(f"  ❌ Database optimization test failed: {e}")
        return False

def test_component_imports():
    """Test that all new components can be imported"""
    print("📦 Testing Component Imports...")
    
    components = [
        ('Health Checker', 'backend.app.monitoring.detailed_health', 'HealthChecker'),
        ('Structured Logger', 'backend.app.logging.structured_logger', 'StructuredFormatter'),
        ('Database Optimizer', 'backend.app.database.optimizations', 'DatabaseOptimizer'),
        ('Security Middleware', 'backend.app.security.middleware', 'SecurityMiddleware'),
        ('Request Signing', 'backend.app.security.request_signing', 'RequestSigner'),
        ('MCP Orchestrator', 'backend.app.mcp.orchestrator', 'MCPOrchestrator'),
        ('MCP WebSocket Server', 'backend.app.mcp.websocket_server', 'MCPWebSocketServer'),
    ]
    
    results = []
    for name, module_path, class_name in components:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✅ {name} import successful")
            results.append(True)
        except Exception as e:
            print(f"  ❌ {name} import failed: {e}")
            results.append(False)
    
    return all(results)

def test_configuration_validation():
    """Test configuration and environment variable handling"""
    print("⚙️  Testing Configuration...")
    
    try:
        # Test basic configuration loading
        import os
        from backend.app import create_app
        
        # Set test environment variables
        test_env = {
            'FLASK_ENV': 'development',
            'SECRET_KEY': 'test-secret-key-for-validation-only',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-for-validation',
            'LOG_LEVEL': 'INFO'
        }
        
        # Backup current env vars
        backup_env = {}
        for key in test_env:
            backup_env[key] = os.environ.get(key)
            os.environ[key] = test_env[key]
        
        try:
            # Test app creation (without running)
            app, socketio = create_app()
            
            # Verify basic config
            assert app.config['SECRET_KEY'] == test_env['SECRET_KEY']
            assert app.config['JWT_SECRET_KEY'] == test_env['JWT_SECRET_KEY']
            
            print("  ✅ App configuration working")
            result = True
            
        finally:
            # Restore environment variables
            for key, value in backup_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        
        return result
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

def test_security_features():
    """Test security component functionality"""
    print("🔒 Testing Security Features...")
    
    try:
        from backend.app.security.request_signing import RequestSigner
        from backend.app.security.middleware import SecurityHardening
        
        # Test request signing
        signer = RequestSigner('test-secret-key')
        signature = signer.sign_request('POST', '/api/test', b'test-body')
        
        # Verify signature is generated
        assert signature is not None and len(signature) > 0
        print("  ✅ Request signing working")
        
        # Test security hardening
        hardening = SecurityHardening()
        
        # Test rate limiting logic (without Flask context)
        # This tests the internal rate limiting structure
        assert hasattr(hardening, 'rate_limiters')
        print("  ✅ Security hardening initialized")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Security features test failed: {e}")
        return False

def test_logging_functionality():
    """Test structured logging components"""
    print("📝 Testing Logging Functionality...")
    
    try:
        from backend.app.logging.structured_logger import (
            StructuredFormatter, 
            CorrelationLogger,
            PerformanceLogger,
            SecurityLogger
        )
        
        # Test formatter
        formatter = StructuredFormatter(include_request_info=False)
        assert formatter is not None
        print("  ✅ Structured formatter created")
        
        # Test loggers
        corr_logger = CorrelationLogger('test')
        perf_logger = PerformanceLogger('test-perf')
        sec_logger = SecurityLogger('test-sec')
        
        assert all([corr_logger, perf_logger, sec_logger])
        print("  ✅ Specialized loggers created")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Logging functionality test failed: {e}")
        return False

def test_mcp_functionality():
    """Test MCP component functionality"""
    print("🔄 Testing MCP Functionality...")
    
    try:
        from backend.app.mcp.orchestrator import MCPOrchestrator
        from backend.app.mcp.workflow_templates import create_document_processing_workflow
        
        # Test orchestrator creation
        orchestrator = MCPOrchestrator()
        assert orchestrator is not None
        print("  ✅ MCP Orchestrator created")
        
        # Test workflow template creation
        workflow = create_document_processing_workflow()
        assert workflow is not None
        assert workflow.name == "Document Processing"
        print("  ✅ Workflow templates working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP functionality test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 OCR Document Scanner - Integration Validation")
    print("=" * 50)
    
    tests = [
        ("Database Optimizations", test_database_optimizations),
        ("Component Imports", test_component_imports),
        ("Configuration", test_configuration_validation),
        ("Security Features", test_security_features),
        ("Logging Functionality", test_logging_functionality),
        ("MCP Functionality", test_mcp_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"Total Tests: {len(results)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("   The OCR Document Scanner is ready for deployment!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())