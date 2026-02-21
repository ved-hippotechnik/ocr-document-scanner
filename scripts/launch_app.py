#!/usr/bin/env python3
"""
OCR Document Scanner - Application Launcher
Launches the enhanced OCR Document Scanner with all implemented improvements
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up environment variables"""
    print("🔧 Setting up environment...")
    
    # Load development environment
    env_file = Path(".env.dev")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✅ Loaded development environment variables")
    else:
        # Set basic environment variables
        os.environ.setdefault('FLASK_ENV', 'development')
        os.environ.setdefault('FLASK_DEBUG', 'true')
        os.environ.setdefault('SECRET_KEY', 'dev-secret-key-for-local-testing-only')
        os.environ.setdefault('JWT_SECRET_KEY', 'dev-jwt-secret-key-different-from-secret')
        os.environ.setdefault('DATABASE_URL', 'sqlite:///ocr_scanner_dev.db')
        os.environ.setdefault('LOG_LEVEL', 'INFO')
        print("✅ Set default environment variables")

def initialize_database():
    """Initialize the database with optimizations"""
    print("🗄️ Initializing database...")
    
    try:
        # Add the backend directory to Python path
        backend_path = Path("backend")
        sys.path.insert(0, str(backend_path.absolute()))
        
        # Import and initialize the database
        from app.database import db, init_db
        from app import create_app
        
        app, socketio = create_app()
        
        with app.app_context():
            # Create tables
            db.create_all()
            print("✅ Database tables created")
            
            # Apply database optimizations if available
            try:
                if hasattr(app, 'database_optimizer') and app.database_optimizer:
                    print("✅ Database optimizations applied")
                else:
                    print("ℹ️ Database optimizations not available (normal for first run)")
            except Exception as e:
                print(f"⚠️ Database optimization warning: {e}")
        
        return app, socketio
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("ℹ️ This is normal if this is the first run or if some components are not available")
        return None, None

def check_dependencies():
    """Check if required dependencies are available"""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy', 
        'flask_cors',
        'requests',
        'PyJWT'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        print("Run: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All core dependencies available")
    return True

def start_application():
    """Start the Flask application"""
    print("🚀 Starting OCR Document Scanner...")
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Initialize database
    app, socketio = initialize_database()
    
    # Try to import and start the app
    try:
        backend_path = Path("backend")
        sys.path.insert(0, str(backend_path.absolute()))
        
        # Import the run script
        if not app:
            from app import create_app
            app, socketio = create_app()
        
        print("\n🎉 OCR Document Scanner is starting!")
        print("=" * 50)
        print("📍 Application URL: http://localhost:5001")
        print("📚 API Documentation: http://localhost:5001/api/v2/docs")
        print("❤️ Health Check: http://localhost:5001/api/v2/health")
        print("📊 Basic Health: http://localhost:5001/health")
        print("=" * 50)
        print("\n🔄 Starting server...")
        
        # Start the application
        if socketio:
            print("✅ Starting with WebSocket support")
            socketio.run(app, host='0.0.0.0', port=5001, debug=True)
        else:
            print("ℹ️ Starting without WebSocket (basic mode)")
            app.run(host='0.0.0.0', port=5001, debug=True)
            
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        print("\nTrying alternative startup method...")
        
        # Alternative startup
        try:
            os.chdir("backend")
            subprocess.run([sys.executable, "run.py"], check=True)
        except Exception as e2:
            print(f"❌ Alternative startup also failed: {e2}")
            return False
    
    return True

def main():
    """Main launcher function"""
    print("🚀 OCR Document Scanner - Enhanced Edition")
    print("=" * 50)
    print("Starting application with all implemented improvements:")
    print("• ⚡ Async Processing")
    print("• 📊 Performance Monitoring") 
    print("• 🔒 Security Hardening")
    print("• 📝 Structured Logging")
    print("• 🔄 WebSocket Support")
    print("• 🗄️ Database Optimizations")
    print("• 🧪 Testing Framework")
    print("• 🎯 MCP Orchestrator")
    print("• ❤️ Health Checks")
    print("• 📚 API Documentation")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Start the application
    success = start_application()
    
    if success:
        print("\n✅ Application launched successfully!")
    else:
        print("\n❌ Failed to launch application")
        print("\nTroubleshooting:")
        print("1. Check that you're in the correct directory")
        print("2. Ensure Python dependencies are installed")
        print("3. Check the logs above for specific errors")
        print("4. Try running: cd backend && python run.py")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())