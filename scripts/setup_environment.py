#!/usr/bin/env python3
"""
Environment setup script for OCR Document Scanner
Installs missing dependencies and sets up the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        else:
            print(f"✅ {description} completed successfully")
            return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        return False
    elif version < (3, 10):
        print("⚠️  Python 3.10+ is recommended for best performance")
    else:
        print("✅ Python version is compatible")
    
    return True

def setup_virtual_environment():
    """Set up virtual environment"""
    venv_path = Path("backend/venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    print("🔧 Creating virtual environment...")
    return run_command(
        f"{sys.executable} -m venv backend/venv",
        "Creating virtual environment"
    )

def install_python_dependencies():
    """Install Python dependencies"""
    print("🔧 Installing Python dependencies...")
    
    # Determine the correct pip path
    if os.name == 'nt':  # Windows
        pip_path = "backend/venv/Scripts/pip"
        python_path = "backend/venv/Scripts/python"
    else:  # Unix/Linux/macOS
        pip_path = "backend/venv/bin/pip"
        python_path = "backend/venv/bin/python"
    
    # Upgrade pip first
    run_command(f"{python_path} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install backend dependencies
    return run_command(
        f"{pip_path} install -r backend/requirements.txt",
        "Installing backend dependencies"
    )

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print("🔧 Installing frontend dependencies...")
    
    # Check if npm is available
    result = subprocess.run("npm --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ npm is not installed. Please install Node.js and npm first.")
        return False
    
    # Install dependencies
    return run_command(
        "cd frontend && npm install",
        "Installing frontend dependencies"
    )

def install_system_dependencies():
    """Install system dependencies"""
    print("🔧 Checking system dependencies...")
    
    # Check if tesseract is installed
    result = subprocess.run("tesseract --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("⚠️  Tesseract OCR not found. Installing...")
        
        # Detect OS and install tesseract
        if sys.platform == "darwin":  # macOS
            return run_command("brew install tesseract", "Installing Tesseract on macOS")
        elif sys.platform.startswith("linux"):  # Linux
            return run_command("sudo apt-get update && sudo apt-get install -y tesseract-ocr", "Installing Tesseract on Linux")
        else:
            print("❌ Please install Tesseract OCR manually for your operating system")
            return False
    else:
        print("✅ Tesseract OCR is already installed")
        return True

def create_directories():
    """Create necessary directories"""
    print("🔧 Creating necessary directories...")
    
    directories = [
        "uploads",
        "logs", 
        "models",
        "analytics_charts",
        "backend/uploads",
        "backend/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created successfully")
    return True

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_template.exists():
        print("🔧 Creating .env file from template...")
        with open(env_template, 'r') as template:
            content = template.read()
        
        with open(env_file, 'w') as env:
            env.write(content)
        
        print("✅ .env file created successfully")
        print("⚠️  Please edit .env file with your configuration")
        return True
    else:
        print("⚠️  .env.template not found, creating basic .env file...")
        basic_env = """# Basic environment configuration
FLASK_ENV=development
SECRET_KEY=dev-key-change-in-production
JWT_SECRET_KEY=jwt-dev-key-change-in-production
DATABASE_URL=sqlite:///ocr_scanner.db
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000
"""
        with open(env_file, 'w') as env:
            env.write(basic_env)
        
        print("✅ Basic .env file created")
        return True

def run_health_check():
    """Run deployment health check"""
    print("🔧 Running health check...")
    
    health_check_script = Path("deployment_health_check.py")
    if health_check_script.exists():
        # Use virtual environment python
        if os.name == 'nt':  # Windows
            python_path = "backend/venv/Scripts/python"
        else:  # Unix/Linux/macOS
            python_path = "backend/venv/bin/python"
        
        return run_command(
            f"{python_path} deployment_health_check.py",
            "Running deployment health check"
        )
    else:
        print("⚠️  Health check script not found, skipping...")
        return True

def main():
    """Main setup function"""
    print("🚀 Setting up OCR Document Scanner environment...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("❌ Failed to create .env file")
        sys.exit(1)
    
    # Set up virtual environment
    if not setup_virtual_environment():
        print("❌ Failed to set up virtual environment")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Install system dependencies
    if not install_system_dependencies():
        print("⚠️  System dependencies installation had issues")
    
    # Install frontend dependencies
    if not install_frontend_dependencies():
        print("⚠️  Frontend dependencies installation had issues")
    
    # Run health check
    if not run_health_check():
        print("⚠️  Health check had issues")
    
    print("\n" + "=" * 50)
    print("🎉 Environment setup completed!")
    print("\nNext steps:")
    print("1. Review and edit .env file with your configuration")
    print("2. For development: python backend/run.py")
    print("3. For production: docker-compose up -d")
    print("4. Access the application at http://localhost:5000")
    print("\nFor detailed documentation, see README.md")

if __name__ == "__main__":
    main()