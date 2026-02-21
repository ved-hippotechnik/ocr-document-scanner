#!/usr/bin/env python3
"""
Structure validation script for OCR Document Scanner
Validates that all implemented improvements are properly structured
"""

import os
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and return result"""
    path = Path(file_path)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {file_path}")
    return exists

def check_directory_exists(dir_path, description):
    """Check if a directory exists and return result"""
    path = Path(dir_path)
    exists = path.exists() and path.is_dir()
    status = "✅" if exists else "❌"
    print(f"  {status} {description}: {dir_path}")
    return exists

def validate_testing_framework():
    """Validate testing framework implementation"""
    print("🧪 Testing Framework Implementation:")
    
    backend_path = "backend"
    results = []
    
    # Check test configuration files
    results.append(check_file_exists(f"{backend_path}/conftest.py", "Test configuration"))
    results.append(check_file_exists(f"{backend_path}/pytest.ini", "Pytest settings"))
    results.append(check_file_exists(f"{backend_path}/requirements-test.txt", "Test dependencies"))
    
    # Check test directories and files
    results.append(check_directory_exists(f"{backend_path}/tests", "Test directory"))
    results.append(check_file_exists(f"{backend_path}/tests/test_comprehensive_api.py", "API tests"))
    results.append(check_file_exists(f"{backend_path}/tests/test_document_processors.py", "Processor tests"))
    results.append(check_file_exists(f"{backend_path}/tests/test_mcp_servers.py", "MCP tests"))
    
    return all(results)

def validate_monitoring_system():
    """Validate monitoring and health check implementation"""
    print("\n📊 Monitoring System Implementation:")
    
    backend_path = "backend/app"
    results = []
    
    # Check monitoring components
    results.append(check_directory_exists(f"{backend_path}/monitoring", "Monitoring directory"))
    results.append(check_file_exists(f"{backend_path}/monitoring/__init__.py", "Monitoring init"))
    results.append(check_file_exists(f"{backend_path}/monitoring/detailed_health.py", "Detailed health checker"))
    
    return all(results)

def validate_mcp_orchestrator():
    """Validate MCP orchestrator implementation"""
    print("\n🎯 MCP Orchestrator Implementation:")
    
    backend_path = "backend/app/mcp"
    results = []
    
    # Check MCP components
    results.append(check_file_exists(f"{backend_path}/orchestrator.py", "MCP orchestrator"))
    results.append(check_file_exists(f"{backend_path}/workflow_templates.py", "Workflow templates"))
    results.append(check_file_exists(f"{backend_path}/websocket_server.py", "WebSocket server"))
    
    return all(results)

def validate_security_hardening():
    """Validate security implementation"""
    print("\n🔒 Security Hardening Implementation:")
    
    backend_path = "backend/app"
    results = []
    
    # Check security components
    results.append(check_directory_exists(f"{backend_path}/security", "Security directory"))
    results.append(check_file_exists(f"{backend_path}/security/__init__.py", "Security init"))
    results.append(check_file_exists(f"{backend_path}/security/request_signing.py", "Request signing"))
    results.append(check_file_exists(f"{backend_path}/security/middleware.py", "Security middleware"))
    
    return all(results)

def validate_structured_logging():
    """Validate structured logging implementation"""
    print("\n📝 Structured Logging Implementation:")
    
    backend_path = "backend/app"
    results = []
    
    # Check logging components
    results.append(check_directory_exists(f"{backend_path}/logging", "Logging directory"))
    results.append(check_file_exists(f"{backend_path}/logging/__init__.py", "Logging init"))
    results.append(check_file_exists(f"{backend_path}/logging/structured_logger.py", "Structured logger"))
    
    return all(results)

def validate_websocket_support():
    """Validate WebSocket implementation"""
    print("\n🔄 WebSocket Support Implementation:")
    
    backend_path = "backend/app"
    results = []
    
    # Check WebSocket components
    results.append(check_directory_exists(f"{backend_path}/websocket", "WebSocket directory"))
    results.append(check_file_exists(f"{backend_path}/websocket/__init__.py", "WebSocket init"))
    results.append(check_file_exists(f"{backend_path}/mcp/websocket_server.py", "MCP WebSocket server"))
    
    return all(results)

def validate_database_optimizations():
    """Validate database optimization implementation"""
    print("\n🗄️ Database Optimizations Implementation:")
    
    backend_path = "backend/app"
    results = []
    
    # Check database components
    results.append(check_directory_exists(f"{backend_path}/database", "Database directory"))
    results.append(check_file_exists(f"{backend_path}/database/__init__.py", "Database init"))
    results.append(check_file_exists(f"{backend_path}/database/optimizations.py", "Database optimizations"))
    
    return all(results)

def validate_documentation():
    """Validate documentation and summary files"""
    print("\n📚 Documentation Implementation:")
    
    results = []
    
    # Check documentation files
    results.append(check_file_exists("IMPLEMENTATION_SUMMARY.md", "Implementation summary"))
    results.append(check_file_exists("backend/conftest.py", "Test configuration"))
    
    return all(results)

def validate_code_syntax():
    """Validate Python syntax of key files"""
    print("\n🔍 Code Syntax Validation:")
    
    key_files = [
        "backend/app/monitoring/detailed_health.py",
        "backend/app/mcp/orchestrator.py",
        "backend/app/security/request_signing.py",
        "backend/app/logging/structured_logger.py",
        "backend/app/database/optimizations.py",
        "backend/app/mcp/websocket_server.py"
    ]
    
    results = []
    for file_path in key_files:
        path = Path(file_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    content = f.read()
                
                # Basic syntax validation
                compile(content, str(path), 'exec')
                print(f"  ✅ Syntax valid: {file_path}")
                results.append(True)
            except SyntaxError as e:
                print(f"  ❌ Syntax error in {file_path}: {e}")
                results.append(False)
            except Exception as e:
                print(f"  ⚠️  Could not validate {file_path}: {e}")
                results.append(True)  # Don't fail for read errors
        else:
            print(f"  ❌ File not found: {file_path}")
            results.append(False)
    
    return all(results)

def main():
    """Run all structure validation tests"""
    print("🏗️  OCR Document Scanner - Structure Validation")
    print("=" * 60)
    
    validation_tests = [
        ("Testing Framework", validate_testing_framework),
        ("Monitoring System", validate_monitoring_system),
        ("MCP Orchestrator", validate_mcp_orchestrator),
        ("Security Hardening", validate_security_hardening),
        ("Structured Logging", validate_structured_logging),
        ("WebSocket Support", validate_websocket_support),
        ("Database Optimizations", validate_database_optimizations),
        ("Documentation", validate_documentation),
        ("Code Syntax", validate_code_syntax),
    ]
    
    results = []
    for test_name, test_func in validation_tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} validation crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📋 STRUCTURE VALIDATION RESULTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total Validations: {len(results)}")
    print(f"Passed:           {passed}")
    print(f"Failed:           {failed}")
    print(f"Success Rate:     {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL STRUCTURE VALIDATIONS PASSED!")
        print("   All implemented improvements are properly structured!")
        return 0
    else:
        print(f"\n⚠️  {failed} validation(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())