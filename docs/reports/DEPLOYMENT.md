# Deployment Guide

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended)
1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Select your forked repository
4. Railway will automatically detect the Dockerfile and deploy

### Option 2: Docker Compose (Local/VPS)
```bash
# Clone repository
git clone https://github.com/ved-hippotechnik/ocr-document-scanner.git
cd ocr-document-scanner

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 3: Manual Deployment

#### Backend
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key
export TESSERACT_CMD=/usr/bin/tesseract

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 run:app
```

#### Frontend
```bash
cd frontend
npm install
npm run build

# Serve with nginx or host static files
```

## 🔧 Environment Variables

### Backend (.env)
```env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-here
TESSERACT_CMD=/usr/bin/tesseract
MAX_CONTENT_LENGTH=16777216
OCR_TIMEOUT=60
CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
```

### Frontend (.env)
```env
REACT_APP_API_URL=https://your-backend-domain.com
REACT_APP_ENVIRONMENT=production
```

## 📋 Pre-deployment Checklist

- [ ] Update SECRET_KEY with secure random string
- [ ] Configure CORS_ORIGINS for your domain
- [ ] Install Tesseract OCR on deployment server
- [ ] Set up SSL certificates
- [ ] Configure domain DNS
- [ ] Test all document types post-deployment
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│   Flask Backend │────│ Tesseract OCR   │
│   (Port 3000)    │    │   (Port 5000)   │    │   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │ Document        │    │ Language Packs  │
│   (Build Output)│    │ Processors      │    │ (Multiple)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔍 Supported Platforms

- **Railway**: ✅ Recommended (Dockerfile)
- **Render**: ✅ Good alternative
- **Heroku**: ✅ Classic choice (requires build pack)
- **DigitalOcean**: ✅ App Platform or Droplet
- **AWS**: ✅ Elastic Beanstalk or ECS
- **Google Cloud**: ✅ Cloud Run
- **Azure**: ✅ Container Instances

## 📊 Performance Optimization

### Production Settings
- Use `gunicorn` with multiple workers
- Enable gzip compression
- Configure CDN for static assets
- Set up Redis caching (optional)
- Monitor memory usage (OCR is memory-intensive)

### Scaling Considerations
- Vertical scaling for OCR processing
- Horizontal scaling for API requests
- Load balancer for multiple instances
- Queue system for batch processing

## 🚨 Security

- Generate secure SECRET_KEY (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- Configure CORS properly
- Use HTTPS in production
- Regular security updates
- Input validation and sanitization
- Rate limiting (consider nginx or cloudflare)

## 📝 Monitoring

### Health Checks
- `/health` - Basic health check
- `/api/processors` - Processor status

### Logging
- Application logs in `logs/app.log`
- Error tracking recommended
- Performance monitoring

## 🔄 CI/CD

GitHub Actions workflow included:
- Automated testing
- Security scanning
- Docker build and push
- Deployment hooks

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify environment variables
3. Test Tesseract installation
4. Check file permissions
5. Review network/firewall settings
