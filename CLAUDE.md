# OCR Document Scanner - Claude AI Assistant Context

## Project Overview
This is an advanced OCR (Optical Character Recognition) document scanner application that combines AI-powered document classification with specialized OCR processing for various document types. The project consists of a Flask backend API and a React frontend application.

## Architecture
- **Backend**: Flask Python API with SQLite database
- **Frontend**: React.js with Material-UI components
- **AI Components**: Document classification, quality assessment, batch processing
- **Database**: SQLite with analytics tracking
- **Cache**: Memory-based caching with Redis fallback

## Project Structure
```
ocr-document-scanner/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app factory
│   │   ├── routes.py                # Basic OCR endpoints
│   │   ├── routes_enhanced.py       # Enhanced OCR endpoints
│   │   ├── routes_enhanced_v2.py    # V2 enhanced endpoints
│   │   ├── database.py              # Database models and setup
│   │   ├── validation.py            # Input validation
│   │   ├── monitoring.py            # Performance monitoring
│   │   ├── quality.py               # Quality assessment
│   │   ├── classification.py        # Document classification
│   │   ├── processors/              # Document-specific processors
│   │   │   ├── __init__.py
│   │   │   ├── registry.py          # Processor registry
│   │   │   ├── aadhaar.py           # Aadhaar card processor
│   │   │   ├── emirates_id.py       # Emirates ID processor
│   │   │   ├── driving_license.py   # Driving license processor
│   │   │   ├── passport.py          # Passport processor
│   │   │   └── us_drivers_license.py # US driver's license processor
│   │   ├── auth/                    # Authentication module
│   │   │   ├── __init__.py
│   │   │   ├── jwt_utils.py         # JWT token management
│   │   │   └── routes.py            # Auth endpoints
│   │   ├── analytics/               # Analytics module
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py         # Analytics dashboard
│   │   │   └── routes.py            # Analytics endpoints
│   │   ├── ai/                      # AI modules
│   │   │   ├── __init__.py
│   │   │   ├── document_classifier.py # AI document classifier
│   │   │   └── routes.py            # AI endpoints
│   │   ├── batch/                   # Batch processing
│   │   │   ├── __init__.py
│   │   │   ├── processor.py         # Batch job manager
│   │   │   └── routes.py            # Batch endpoints
│   │   └── cache/                   # Caching system
│   │       ├── __init__.py
│   │       ├── memory_cache.py      # In-memory cache
│   │       └── redis_cache.py       # Redis cache
│   ├── requirements.txt             # Python dependencies
│   └── run.py                       # Application entry point
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Scanner.js           # Basic scanner component
│   │   │   ├── AIScanner.js         # AI-powered scanner
│   │   │   ├── AIDashboard.js       # Analytics dashboard
│   │   │   ├── BatchProcessor.js    # Batch processing UI
│   │   │   └── OfflineStatus.js     # Offline status indicator
│   │   ├── App.js                   # Main React app
│   │   └── index.js                 # React entry point
│   ├── package.json                 # Node.js dependencies
│   └── public/                      # Static assets
├── docker-compose.yml               # Docker setup
├── Dockerfile                       # Docker image
└── deploy.sh                        # Deployment script
```

## Key Features

### Document Processing
- **Supported Documents**: Emirates ID, Aadhaar Card, Indian Driving License, Passports, US Driver's License
- **AI Classification**: Automatic document type detection
- **Quality Assessment**: Image quality scoring and validation
- **Batch Processing**: Handle multiple documents simultaneously
- **Security Validation**: Document authenticity checks

### Backend Components
- **Enhanced OCR System**: Multi-engine OCR processing
- **ML Document Classifier**: AI-powered document classification
- **Analytics Dashboard**: Real-time processing statistics
- **Performance Optimizer**: System performance monitoring
- **Security Validator**: Document security validation
- **Batch Job Manager**: Queue management for bulk processing

### Frontend Features
- **Drag & Drop Upload**: Easy document upload interface
- **Real-time Processing**: Live progress tracking
- **Analytics Dashboard**: Interactive charts and metrics
- **Batch Processing UI**: Manage multiple document jobs
- **Offline Support**: Works without internet connection

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **OpenCV**: Computer vision library
- **Tesseract**: OCR engine
- **scikit-learn**: Machine learning library
- **Pillow**: Image processing
- **Flask-CORS**: Cross-origin resource sharing

### Frontend
- **React.js**: JavaScript UI library
- **Material-UI**: React component library
- **Recharts**: Data visualization
- **React-Dropzone**: File upload component
- **React-Toastify**: Notification system

## Database Schema

### Core Tables
- `scan_history`: OCR processing history
- `document_type_stats`: Document type statistics
- `user_sessions`: User session tracking
- `batch_processing_jobs`: Batch job management
- `login_attempts`: Authentication logging

### Analytics Tables
- Performance metrics
- Quality assessments
- Error tracking
- Usage statistics

## API Endpoints

### Core API
- `GET /health` - Health check
- `POST /api/scan` - Basic document processing
- `GET /api/processors` - Available processors
- `GET /api/stats` - Processing statistics

### Enhanced API (v2)
- `POST /api/v2/scan` - Enhanced document processing
- `GET /api/v2/health` - Detailed health check
- `POST /api/v2/batch` - Batch processing
- `GET /api/v2/analytics` - Analytics data

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/profile` - User profile

### Analytics
- `GET /api/analytics/dashboard` - Dashboard data
- `GET /api/analytics/trends` - Processing trends
- `GET /api/analytics/export` - Export reports

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- Tesseract OCR
- Git

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Docker Setup
```bash
docker-compose up -d
```

## Common Issues and Solutions

### Frontend Compilation Errors
- **JSX Syntax Errors**: Use `{'< text'}` instead of `< text` in JSX
- **Missing Dependencies**: Install with `npm install package-name`
- **Material-UI Icons**: Use existing icons like `CheckCircleOutline` instead of non-existent ones

### Backend Issues
- **OCR Engine**: Ensure Tesseract is installed and in PATH
- **Database**: SQLite file permissions and location
- **Dependencies**: Check Python package versions

### Performance Optimization
- **Image Processing**: Optimize image size before OCR
- **Caching**: Use Redis for better performance
- **Database**: Index frequently queried columns

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Test API endpoints
curl -X POST -F "image=@test_document.jpg" http://localhost:5001/api/scan
```

## Deployment

### Production Environment
- Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
- Use PostgreSQL instead of SQLite
- Configure Redis for caching
- Set up proper logging
- Use HTTPS in production

### Environment Variables
```bash
# Backend
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-secret"
export DATABASE_URL="postgresql://..."
export REDIS_URL="redis://..."

# Frontend
export REACT_APP_API_URL="https://api.yourdomain.com"
```

## Security Considerations
- JWT token authentication
- Input validation and sanitization
- Rate limiting
- CORS configuration
- Secure file upload handling
- Document authenticity validation

## Future Enhancements
- WebSocket real-time updates
- Advanced ML models
- Multi-language support
- Mobile app integration
- Cloud storage integration
- Advanced analytics

## Troubleshooting

### Common Commands
```bash
# Check running services
lsof -i :5001  # Backend
lsof -i :3001  # Frontend

# View logs
tail -f backend/logs/app.log

# Database operations
sqlite3 backend/ocr_scanner.db

# Clear cache
rm -rf frontend/node_modules/.cache
```

### Debug Mode
- Backend: Set `FLASK_ENV=development`
- Frontend: Runs in development mode by default

## Contact and Support
For issues or questions, check:
1. Application logs
2. Network connectivity
3. Service dependencies
4. Environment variables
5. Database permissions

## Version History
- v1.0: Basic OCR functionality
- v1.1: AI-powered classification
- v1.2: Batch processing
- v2.0: Enhanced analytics and security
- v2.1: Performance optimizations

---

This document should be updated as the project evolves. Keep it current with architectural changes, new features, and important configuration updates.