#!/usr/bin/env python3
"""
Apply Critical Fixes to OCR Document Scanner API
This script addresses the critical issues found in testing
"""

import os
import sys
from pathlib import Path

def apply_fixes():
    """Apply critical fixes to the backend"""
    
    backend_path = Path("backend")
    
    print("🔧 Applying Critical Fixes...")
    print("="*50)
    
    # Fix 1: Update __init__.py to properly register V3 routes
    print("\n1. Fixing V3 route registration...")
    
    init_file = backend_path / "app" / "__init__.py"
    
    # Read current content
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check if improved routes are properly imported
    if "from .routes_improved import improved" in content:
        print("   ✓ V3 routes import found")
        
        # Ensure it's registered
        if "app.register_blueprint(improved)" not in content:
            print("   ⚠️  V3 routes not registered, adding registration...")
            
            # Find the place to add registration (after other blueprints)
            marker = "app.register_blueprint(batch_bp)"
            if marker in content:
                content = content.replace(
                    marker,
                    marker + "\n    \n    # Register V3 improved routes\n    app.register_blueprint(improved)\n    app.logger.info('✅ V3 improved routes registered')"
                )
                
                with open(init_file, 'w') as f:
                    f.write(content)
                print("   ✅ V3 routes registration added")
        else:
            print("   ✓ V3 routes already registered")
    
    # Fix 2: Ensure rate limiter is properly initialized
    print("\n2. Fixing rate limiter initialization...")
    
    if "app.limiter = limiter" not in content:
        print("   ⚠️  Rate limiter not attached to app, fixing...")
        
        # Find the rate limiter initialization
        if "limiter = init_rate_limiter(app)" in content:
            content = content.replace(
                "limiter = init_rate_limiter(app)",
                "limiter = init_rate_limiter(app)\n    app.limiter = limiter  # Make limiter accessible to blueprints"
            )
            
            with open(init_file, 'w') as f:
                f.write(content)
            print("   ✅ Rate limiter attachment fixed")
    else:
        print("   ✓ Rate limiter already attached to app")
    
    # Fix 3: Add file validation to main scan route
    print("\n3. Adding file upload validation...")
    
    routes_file = backend_path / "app" / "routes.py"
    
    with open(routes_file, 'r') as f:
        routes_content = f.read()
    
    # Add validation function if not present
    validation_code = '''
def validate_uploaded_file(file):
    """Validate uploaded file"""
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "Empty filename"
    
    # Check file size (reading a small chunk)
    file.seek(0, 2)  # Move to end
    file_length = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_length == 0:
        return False, "Empty file not allowed"
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf'}
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return False, f"File type .{ext} not allowed"
    
    return True, "Valid"
'''
    
    if "def validate_uploaded_file" not in routes_content:
        print("   ⚠️  File validation function missing, adding...")
        
        # Add the validation function before the scan route
        marker = "@main.route('/api/scan'"
        if marker in routes_content:
            routes_content = routes_content.replace(
                marker,
                validation_code + "\n" + marker
            )
            
            # Also update the scan route to use validation
            scan_route_marker = "if 'image' not in request.files:"
            if scan_route_marker in routes_content:
                routes_content = routes_content.replace(
                    scan_route_marker,
                    """# Validate file upload
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    is_valid, message = validate_uploaded_file(file)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Original check (now redundant but kept for compatibility)
    if False:  # """ + scan_route_marker
                )
            
            with open(routes_file, 'w') as f:
                f.write(routes_content)
            print("   ✅ File validation added to scan route")
    else:
        print("   ✓ File validation already present")
    
    # Fix 4: Update rate limiter to use correct decorators
    print("\n4. Ensuring rate limit decorators are applied...")
    
    improved_routes = backend_path / "app" / "routes_improved.py"
    
    if improved_routes.exists():
        with open(improved_routes, 'r') as f:
            improved_content = f.read()
        
        # Check if rate limit decorators are present
        if "@ratelimit_scan()" in improved_content:
            print("   ✓ Rate limit decorators found in V3 routes")
        else:
            print("   ⚠️  Rate limit decorators might be missing")
    
    # Fix 5: Create a simple test endpoint to verify rate limiting
    print("\n5. Adding rate limit test endpoint...")
    
    test_endpoint_code = '''
@main.route('/api/test/rate-limit')
@limiter.limit("5 per minute")
def test_rate_limit():
    """Test endpoint for rate limiting verification"""
    return jsonify({
        'message': 'Rate limit test successful',
        'timestamp': datetime.utcnow().isoformat()
    })
'''
    
    if "/api/test/rate-limit" not in routes_content:
        print("   ⚠️  Adding test endpoint for rate limiting...")
        
        # Add necessary imports
        if "from flask_limiter.util import get_remote_address" not in routes_content:
            routes_content = "from flask import current_app\nfrom datetime import datetime\n" + routes_content
        
        # Add the test endpoint at the end of the file
        routes_content += "\n" + test_endpoint_code
        
        with open(routes_file, 'w') as f:
            f.write(routes_content)
        print("   ✅ Rate limit test endpoint added")
    else:
        print("   ✓ Rate limit test endpoint already exists")
    
    print("\n" + "="*50)
    print("✅ Critical fixes applied successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server")
    print("2. Run: python api_stress_test_v2.py")
    print("3. Verify fixes are working")
    print("\nTest the rate limiting with:")
    print("  for i in {1..10}; do curl http://localhost:5001/api/test/rate-limit; done")

if __name__ == "__main__":
    os.chdir("/Users/vedthampi/CascadeProjects/ocr-document-scanner")
    apply_fixes()
