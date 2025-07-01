# 🚀 OCR Document Scanner - Deployment Guide

This guide covers multiple deployment options for the OCR Document Scanner, from local development to production cloud deployment.

## 📋 Prerequisites

- Docker & Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

## 🐳 Quick Start with Docker

### 1. Clone and Build
```bash
git clone https://github.com/ved-hippotechnik/ocr-document-scanner.git
cd ocr-document-scanner

# Production deployment
docker-compose up -d

# Development mode (with hot reload)
docker-compose --profile dev up
```

### 2. Access the Application
- **Production**: http://localhost:5000
- **Development**: Frontend at http://localhost:3000, Backend at http://localhost:5001

## ☁️ Cloud Deployment Options

### Option 1: Railway (Recommended)

Railway provides the easiest deployment experience:

1. **Connect Repository**:
   - Fork the repository to your GitHub account
   - Connect your GitHub to [Railway](https://railway.app)
   - Create new project from your forked repository

2. **Environment Variables**:
   ```bash
   FLASK_ENV=production
   SECRET_KEY=your-super-secure-secret-key
   TESSERACT_CMD=/usr/bin/tesseract
   LOG_LEVEL=INFO
   ```

3. **Deploy**:
   - Railway will automatically detect the Dockerfile
   - Deployment happens automatically on git push

## 🔧 Enhanced Features

### New API Endpoints (v2)

The enhanced system includes new endpoints with advanced features:

- `POST /api/v2/scan` - Enhanced scanning with quality assessment
- `POST /api/v2/quality-check` - Standalone image quality analysis
- `POST /api/v2/classify` - Document classification only
- `GET /api/v2/stats` - Enhanced statistics with performance metrics
- `GET /metrics` - Prometheus metrics endpoint

### Quality Assessment Features

- **Image Quality Analysis**: Blur detection, brightness, contrast analysis
- **Processing Confidence**: High/Medium/Low confidence scoring
- **Enhancement Suggestions**: Specific recommendations for better results
- **Real-time Feedback**: Quality metrics with each scan

### Advanced Classification

- **Multi-strategy Detection**: Text patterns, number formats, visual features
- **Confidence Scoring**: Detailed confidence metrics for each classification
- **Feature Detection**: Security features, color analysis, document dimensions

---

**Happy Deploying! 🎉**
