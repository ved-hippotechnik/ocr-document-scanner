# OCR Document Scanner - Quick Start Instructions

## Compilation Errors Fixed

The following compilation errors have been addressed:

### 1. Docker Compose YAML Syntax
- Fixed malformed YAML structure
- Added proper multi-stage build targets
- Created simplified docker-compose.simple.yml

### 2. Python Import Errors
- Commented out problematic imports
- Created missing __init__.py files
- Added simplified requirements.txt

### 3. Missing Dependencies
- Created requirements_minimal.txt with core dependencies
- Added setup_environment.py for automated setup

## Quick Start Options

### Option 1: Local Development (Recommended)
```bash
# Run the setup script
python3 setup_environment.py

# Activate virtual environment
source backend/venv/bin/activate

# Start the application
python backend/run.py
```

### Option 2: Docker Simple
```bash
# Use the simplified docker-compose
docker-compose -f docker-compose.simple.yml up -d
```

### Option 3: Docker Full (After fixing dependencies)
```bash
# Use the full docker-compose
docker-compose up -d
```

## Accessing the Application

- Backend API: http://localhost:5000
- Health Check: http://localhost:5000/health
- API Documentation: http://localhost:5000/docs (if available)

## Next Steps

1. Install missing Python packages:
   ```bash
   pip install -r requirements_minimal.txt
   ```

2. Install system dependencies:
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   ```

3. Configure environment variables in .env file

4. Run the deployment health check:
   ```bash
   python deployment_health_check.py
   ```

## Troubleshooting

- If you get import errors, use requirements_minimal.txt first
- If Docker fails, use docker-compose.simple.yml
- Check logs in ./logs/ directory
- Run health check for detailed diagnostics

## Support

For more detailed documentation, see README.md
