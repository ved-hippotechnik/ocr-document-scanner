# OCR Document Scanner

A production-ready, enterprise-grade document scanning and information extraction platform with advanced OCR capabilities, document classification, quality assessment, and monitoring.

## ✨ Key Features

### 🔍 Advanced Document Processing
- **Multi-Document Support**: 5+ document types with extensible architecture
- **Smart Classification**: AI-powered document type detection
- **Quality Assessment**: Real-time image quality analysis and recommendations
- **High Accuracy OCR**: Multiple OCR engines with preprocessing optimization
- **Multi-language Support**: 15+ languages including Arabic, Hindi, and European languages

### 🏗️ Production-Ready Architecture
- **Modular Processor System**: Easy addition of new document types
- **Enhanced API**: RESTful API with v2 endpoints and comprehensive validation
- **Monitoring & Analytics**: Prometheus metrics, performance tracking, and health checks
- **Security**: Rate limiting, input validation, and security headers
- **Scalable Deployment**: Docker, Docker Compose, and cloud deployment ready

### 📊 Quality & Monitoring
- **Quality Scoring**: Automatic assessment of document image quality
- **Performance Metrics**: Real-time processing statistics and monitoring
- **Error Handling**: Comprehensive error tracking and user-friendly messages
- **Rate Limiting**: Configurable API rate limiting and quotas

### 🎨 Enhanced User Experience
- **Modern UI**: React-based dashboard with Material-UI components
- **Real-time Feedback**: Quality assessments and processing confidence
- **Camera Integration**: Live document capture with preview
- **Responsive Design**: Mobile-friendly interface

## 🌍 Supported Documents

### Production Ready
- ✅ **India**: Aadhaar Card, Driving License, Passport
- ✅ **UAE**: Emirates ID
- ✅ **United States**: Driver's License (All States)

### Document Capabilities
| Document Type | Country | Extraction Fields | Confidence |
|---------------|---------|-------------------|------------|
| Aadhaar Card | India | Name, Number, DOB, Gender, Address, Father's Name | 95%+ |
| Driving License | India | Name, DL Number, DOB, Address, Validity, Class | 92%+ |
| Passport | India | Name, Number, DOB, Nationality, Issue/Expiry | 90%+ |
| Emirates ID | UAE | Name, ID Number, Nationality, DOB, Expiry | 94%+ |
| Driver's License | USA | Name, Number, DOB, Address, State, Expiry | 88%+ |

### Coming Soon (Framework Ready)
- 🔄 **United Kingdom**: Driving Licence, Biometric Residence Permit
- 🔄 **Germany**: Personalausweis, Führerschein
- 🔄 **Canada**: Driver's License (English/French)
- 🔄 **Singapore**: NRIC
- 🔄 **Japan**: My Number Card

*[View complete API documentation](API_DOCUMENTATION.md)*

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
git clone https://github.com/ved-hippotechnik/ocr-document-scanner.git
cd ocr-document-scanner

# Development environment
docker-compose up -d

# Production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Access Points:**
- 🌐 Frontend: http://localhost:3000
- 🔧 Backend API: http://localhost:5002
- 📊 Metrics: http://localhost:5002/metrics

### Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the Flask server:
```bash
python run.py
```

The backend server will start at http://localhost:5002

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies and start:
```bash
npm install
npm start
```

The frontend will be available at http://localhost:3000

## 🏗️ Architecture Overview

### Modular Processor System
```python
# Example: Adding a new document processor
class NewDocumentProcessor(DocumentProcessor):
    def __init__(self):
        super().__init__('Country', 'document_type')
    
    def detect(self, text, image=None):
        # Document detection logic
        return True
    
    def extract_info(self, text_results):
        # Information extraction logic
        return {'field1': 'value1'}
```

### API Endpoints

#### Enhanced API v2 (Recommended)
- `POST /api/v2/scan` - Enhanced document scanning with quality assessment
- `POST /api/v2/classify` - Document classification only
- `POST /api/v2/quality` - Image quality assessment
- `GET /api/v2/stats` - Performance statistics
- `GET /api/v2/health` - Health check with component status

#### Legacy API v1
- `POST /api/scan` - Basic document scanning
- `GET /health` - Simple health check

*[Complete API Documentation](API_DOCUMENTATION.md)*

### Quality Assessment System
The system provides real-time quality feedback:

```json
{
  "quality_score": 0.87,
  "issues": [
    {
      "type": "low_resolution",
      "severity": "medium",
      "description": "Image resolution could be higher"
    }
  ],
  "recommendations": [
    "Take photo in better lighting",
    "Hold camera steady to avoid blur"
  ]
}
```

## 📊 Monitoring & Analytics

### Prometheus Metrics
- Request rate and response times
- Document type distribution
- Quality score distribution
- Error rates and types

### Performance Monitoring
- Processing time tracking
- Accuracy metrics per document type
- System resource utilization

Access metrics at: `http://localhost:5002/metrics`

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Run all tests
python comprehensive_test_enhanced.py

# Test specific URL
python comprehensive_test_enhanced.py --url http://localhost:5002

# Save results
python comprehensive_test_enhanced.py --save-results my_results.json
```

### Test Coverage
- ✅ All document processors
- ✅ API validation and error handling
- ✅ Quality assessment
- ✅ Rate limiting
- ✅ Performance monitoring
- ✅ Health checks

## 🚀 Deployment

### Production Deployment Options

#### 1. Docker Compose (Local/Server)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

#### 2. Railway (Cloud)
```bash
railway up
```

#### 3. AWS/GCP/Azure
Use the provided `Dockerfile` and deployment configurations.

*[Detailed Deployment Guide](ENHANCED_DEPLOYMENT.md)*

### Environment Configuration
```bash
# Backend (.env)
FLASK_ENV=production
SECRET_KEY=your-secret-key
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=10485760

# Frontend (.env)
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production
```

## 🔧 Configuration

### Document Processor Configuration
```python
# backend/app/config.py
PROCESSORS_CONFIG = {
    'confidence_threshold': 0.7,
    'quality_threshold': 0.5,
    'max_processing_time': 30,
    'enable_caching': True
}
```

### OCR Configuration
```python
OCR_CONFIG = {
    'languages': ['eng', 'hin', 'ara'],
    'dpi': 300,
    'preprocessing': {
        'denoise': True,
        'deskew': True,
        'enhance_contrast': True
    }
}
```

## 📈 Performance

### Benchmark Results
| Document Type | Avg Processing Time | Accuracy | Confidence |
|---------------|-------------------|----------|------------|
| Aadhaar Card | 2.1s | 95.2% | 0.94 |
| Driving License | 2.3s | 92.8% | 0.91 |
| Passport | 1.9s | 90.5% | 0.89 |
| Emirates ID | 2.0s | 94.1% | 0.93 |

### Optimization Features
- Multi-threaded processing
- Image preprocessing pipeline
- Intelligent OCR configuration selection
- Caching for repeated requests
- Memory-efficient image handling

## 🤝 Contributing

### Adding New Document Types

1. **Create Processor**:
```python
# backend/app/processors/new_document.py
class NewDocumentProcessor(DocumentProcessor):
    # Implementation
```

2. **Register Processor**:
```python
# backend/app/processors/registry.py
processor_registry.register(NewDocumentProcessor())
```

3. **Add Tests**:
```python
# Test the new processor
def test_new_document_processor():
    # Test implementation
```

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

*[Development Guidelines](CONTRIBUTING.md)*

## 📚 Documentation

- [📖 Complete API Documentation](API_DOCUMENTATION.md)
- [🚀 Enhanced Deployment Guide](ENHANCED_DEPLOYMENT.md)
- [🔧 Configuration Reference](CONFIG.md)
- [🧪 Testing Guide](TESTING.md)
- [📊 Monitoring Setup](MONITORING.md)

## 🛣️ Roadmap

### Version 2.1 (Next Release)
- [ ] Advanced ML-based document classification
- [ ] Batch processing capabilities
- [ ] User authentication and API keys
- [ ] Document template management
- [ ] Advanced analytics dashboard

### Version 3.0 (Future)
- [ ] Real-time document streaming
- [ ] Multi-language UI
- [ ] Document verification against databases
- [ ] Mobile SDK for native apps
- [ ] Enterprise SSO integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: [API Docs](API_DOCUMENTATION.md)
- **Issues**: [GitHub Issues](https://github.com/ved-hippotechnik/ocr-document-scanner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ved-hippotechnik/ocr-document-scanner/discussions)
- **Email**: support@hippotechnik.com

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ved-hippotechnik/ocr-document-scanner&type=Date)](https://star-history.com/#ved-hippotechnik/ocr-document-scanner&Date)

---

**Built with ❤️ by [Hippotechnik](https://hippotechnik.com)**
        # Detection logic
        return True/False
    
    def preprocess(self, image):
        # Image enhancement
        return processed_images
    
    def extract_info(self, text_results):
        # Information extraction
        return structured_data
```

## 📊 API Endpoints

- `POST /api/scan` - Process document image
- `GET /api/stats` - Get processing statistics  
- `GET /health` - Health check
- `GET /api/processors` - List supported processors

## 🌐 Deployment

**Production-ready deployment options:**

- **Railway**: [One-click deploy](https://railway.app) *(Recommended)*
- **Docker**: Full containerization support
- **Traditional**: Manual deployment guide

*[View detailed deployment guide](DEPLOYMENT.md)*

## License

MIT
