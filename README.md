# OCR Document Scanner

An advanced OCR (Optical Character Recognition) document scanner application that combines AI-powered document classification with specialized OCR processing for various document types. Features asynchronous processing with Celery, comprehensive API documentation, and Model Context Protocol (MCP) integration.

## 🚀 Features

### Core Features
- **Multi-Document Support**: Emirates ID, Aadhaar Card, Indian Driving License, Passports, US Driver's License
- **AI-Powered Classification**: Automatic document type detection using machine learning
- **Quality Assessment**: Image quality scoring and enhancement
- **Batch Processing**: Handle multiple documents simultaneously with Celery
- **Security Validation**: Document authenticity checks
- **Real-time Processing**: WebSocket support for live updates
- **Analytics Dashboard**: Comprehensive processing statistics and insights

### Recent Enhancements
- **Asynchronous Processing**: Celery integration for handling heavy workloads
- **OpenAPI Documentation**: Interactive Swagger UI at `/api/v2/docs`
- **MCP Integration**: Model Context Protocol servers for advanced AI capabilities
  - Sequential Thinking MCP for step-by-step reasoning
  - Memory MCP for persistent context storage
  - Context7 MCP for multi-layered contextual understanding
  - Filesystem MCP for document management

## 🛠️ Technology Stack

### Backend
- **Flask**: Python web framework with factory pattern
- **SQLAlchemy**: Database ORM with migrations
- **Celery**: Distributed task queue for async processing
- **Redis**: Message broker and caching
- **OpenCV**: Computer vision and image processing
- **Tesseract**: OCR engine
- **scikit-learn**: Machine learning for document classification
- **Flask-RESTX**: API documentation with Swagger

### Frontend
- **React.js**: Modern JavaScript UI library
- **Material-UI**: React component library
- **Recharts**: Data visualization
- **React-Dropzone**: Drag & drop file uploads

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- Redis Server
- Tesseract OCR
- PostgreSQL (for production)
- Docker & Docker Compose (optional)

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/vedthampi/ocr-document-scanner.git
cd ocr-document-scanner

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

The application will be available at:
- Frontend: http://localhost:3001
- Backend API: http://localhost:5001
- API Documentation: http://localhost:5001/api/v2/docs
- Flower (Celery monitoring): http://localhost:5555

### Manual Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export SECRET_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret
export CELERY_BROKER_URL=redis://localhost:6379/0

# Initialize database
python -c "from app import create_app; from app.database import db; app, _ = create_app(); app.app_context().push(); db.create_all()"

# Start Redis server (in a separate terminal)
redis-server

# Start Celery worker (in a separate terminal)
celery -A app.celery_app:celery_app worker --loglevel=info

# Start Celery beat scheduler (in a separate terminal)
celery -A app.celery_app:celery_app beat --loglevel=info

# Run the Flask application
python run.py
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📚 API Documentation

Interactive API documentation is available at `/api/v2/docs` when the backend is running.

### Key Endpoints

- `POST /api/v2/scan` - Synchronous document processing
- `POST /api/v2/async/scan` - Asynchronous document processing
- `GET /api/v2/async/status/{task_id}` - Check async task status
- `POST /api/v2/batch` - Batch document processing
- `GET /api/v2/analytics/dashboard` - Analytics dashboard data
- `POST /api/v2/auth/login` - User authentication
- `GET /api/v2/health` - Service health check

### Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test

# Integration tests
./run_integration_tests.sh
```

## 📊 Performance Optimization

- **Redis Caching**: Frequently accessed data is cached
- **Image Preprocessing**: Automatic optimization before OCR
- **Parallel Processing**: Celery workers for concurrent tasks
- **Database Indexing**: Optimized queries for large datasets

## 🔒 Security

- JWT token authentication with refresh tokens
- Input validation and sanitization
- Rate limiting on API endpoints
- CORS configuration
- Secure file upload handling
- Document authenticity validation

## 🚀 Deployment

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# OCR Settings
OCR_TIMEOUT=60
OCR_DPI=300
OCR_LANGUAGES=eng,ara,hin

# MCP Configuration
MCP_STORAGE_PATH=/var/lib/ocr-scanner/mcp
MCP_MAX_MEMORY_SIZE=10000
```

### Production Deployment

1. Set up PostgreSQL database
2. Configure Redis for caching and Celery
3. Set secure environment variables
4. Use Gunicorn for Flask deployment
5. Set up Nginx as reverse proxy
6. Configure SSL certificates
7. Set up monitoring with Prometheus/Grafana

## 📈 Monitoring

- **Flower**: Celery task monitoring at `/flower`
- **Health Checks**: `/api/v2/health` endpoint
- **Prometheus Metrics**: `/metrics` endpoint
- **Application Logs**: Structured JSON logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Tesseract OCR community
- OpenCV contributors
- Flask and React communities
- All contributors to this project

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation at `/api/v2/docs`
- Review application logs for debugging

---

Built with ❤️ by the OCR Scanner Team
