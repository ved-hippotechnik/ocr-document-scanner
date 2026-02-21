# OCR Document Scanner - Configuration Guide

## 🚀 Complete Configuration Reference

This guide provides comprehensive configuration instructions for the enhanced OCR Document Scanner with all implemented improvements.

## 📋 Table of Contents

- [Environment Variables](#environment-variables)
- [Database Configuration](#database-configuration)
- [Security Configuration](#security-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [WebSocket Configuration](#websocket-configuration)
- [MCP (Model Context Protocol)](#mcp-model-context-protocol)
- [Performance Tuning](#performance-tuning)
- [Production Deployment](#production-deployment)
- [Docker Configuration](#docker-configuration)
- [Testing Configuration](#testing-configuration)

## 🔧 Environment Variables

### Core Application Settings

```bash
# Basic Flask Configuration
SECRET_KEY="your-super-secure-secret-key-minimum-32-chars"
JWT_SECRET_KEY="separate-jwt-secret-key-for-token-signing"
FLASK_ENV="production"  # or "development"
FLASK_DEBUG="false"     # Set to "true" only in development

# Server Configuration
HOST="0.0.0.0"
PORT="5001"
MAX_CONTENT_LENGTH="16777216"  # 16MB in bytes
UPLOAD_FOLDER="uploads"

# JWT Token Configuration
JWT_ACCESS_TOKEN_EXPIRES="86400"   # 24 hours in seconds
JWT_REFRESH_TOKEN_EXPIRES="2592000"  # 30 days in seconds
```

### Database Configuration

```bash
# Production Database (PostgreSQL recommended)
DATABASE_URL="postgresql://username:password@localhost:5432/ocr_scanner"

# Development Database (SQLite fallback)
SQLALCHEMY_DATABASE_URI="sqlite:///ocr_scanner.db"

# Database Pool Settings
DB_POOL_SIZE="10"
DB_POOL_TIMEOUT="20"
DB_POOL_RECYCLE="-1"
DB_POOL_PRE_PING="true"
```

### Security Configuration

```bash
# Request Signing (for API security)
REQUIRE_REQUEST_SIGNING="false"  # Set to "true" for production
REQUEST_SIGNING_SECRET="your-request-signing-secret-key"

# API Key Authentication
VALID_API_KEYS="api-key-1,api-key-2,api-key-3"

# Rate Limiting
RATE_LIMIT_REQUESTS="1000"  # Requests per window
RATE_LIMIT_WINDOW="3600"    # Window size in seconds (1 hour)
RATE_LIMIT_STORAGE="redis://localhost:6379/2"

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

### Monitoring & Logging

```bash
# Logging Configuration
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE="app.log"
LOG_MAX_BYTES="10485760"  # 10MB
LOG_BACKUP_COUNT="5"

# Structured Logging
ENABLE_STRUCTURED_LOGGING="true"
ENABLE_REQUEST_ID_TRACKING="true"

# Prometheus Metrics
PROMETHEUS_METRICS_ENABLED="true"
PROMETHEUS_METRICS_PORT="9090"
METRICS_ENDPOINT="/metrics"

# Health Check Configuration
HEALTH_CHECK_TIMEOUT="30"  # seconds
ENABLE_DETAILED_HEALTH_CHECKS="true"
```

### Celery & Redis Configuration

```bash
# Redis Configuration
REDIS_URL="redis://localhost:6379/0"
REDIS_PASSWORD=""  # If Redis requires authentication

# Celery Configuration
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/1"
CELERY_TASK_SERIALIZER="json"
CELERY_RESULT_SERIALIZER="json"
CELERY_ACCEPT_CONTENT='["json"]'
CELERY_TASK_ROUTES='{"app.tasks.*": {"queue": "default"}}'

# Celery Worker Configuration
CELERY_WORKER_CONCURRENCY="4"
CELERY_WORKER_PREFETCH_MULTIPLIER="1"
CELERY_TASK_SOFT_TIME_LIMIT="300"  # 5 minutes
CELERY_TASK_TIME_LIMIT="600"       # 10 minutes
```

### WebSocket Configuration

```bash
# WebSocket Settings
WEBSOCKET_CORS_ORIGINS="*"  # Restrict in production
WEBSOCKET_ASYNC_MODE="threading"  # or "eventlet", "gevent"
WEBSOCKET_PING_TIMEOUT="60"
WEBSOCKET_PING_INTERVAL="25"

# WebSocket Authentication
WEBSOCKET_AUTH_REQUIRED="true"
WEBSOCKET_JWT_VERIFY="true"
```

### MCP Configuration

```bash
# MCP Storage Configuration
MCP_STORAGE_PATH="mcp_storage"
MCP_MAX_MEMORY_SIZE="10000"  # Maximum number of memory entries
MCP_MEMORY_PERSISTENCE_PATH="mcp_storage/memory.pkl"

# MCP Context Configuration
MCP_CONTEXT_LAYERS="request,session,user,global"
MCP_CONTEXT_TTL="3600"  # Context TTL in seconds

# MCP Workflow Configuration
MCP_MAX_WORKFLOW_STEPS="50"
MCP_WORKFLOW_TIMEOUT="1800"  # 30 minutes
MCP_ENABLE_WORKFLOW_PERSISTENCE="true"
```

### OCR Configuration

```bash
# OCR Engine Settings
OCR_TIMEOUT="60"  # OCR processing timeout in seconds
OCR_DPI="300"     # Image DPI for OCR processing
OCR_LANGUAGES="eng,ara,hin"  # Supported OCR languages

# Tesseract Configuration
TESSERACT_CONFIG="--oem 3 --psm 6"
TESSERACT_DATA_PATH="/usr/share/tesseract-ocr/tessdata"

# Image Processing
MAX_IMAGE_SIZE="5242880"  # 5MB in bytes
SUPPORTED_IMAGE_FORMATS="png,jpg,jpeg,gif,bmp,tiff,pdf"
IMAGE_QUALITY_THRESHOLD="0.7"  # Quality score threshold
```

## 🗄️ Database Configuration

### PostgreSQL (Production Recommended)

```bash
# PostgreSQL Configuration
DATABASE_URL="postgresql://ocr_user:secure_password@localhost:5432/ocr_scanner_db"

# Connection Pool Settings
SQLALCHEMY_ENGINE_OPTIONS='{
  "pool_size": 10,
  "pool_timeout": 20,
  "pool_recycle": -1,
  "pool_pre_ping": true,
  "max_overflow": 20
}'

# Database Optimizations
DB_ENABLE_QUERY_CACHE="true"
DB_QUERY_CACHE_SIZE="1000"
DB_ENABLE_AUTO_VACUUM="true"
```

### SQLite (Development)

```bash
# SQLite Configuration (Development Only)
SQLALCHEMY_DATABASE_URI="sqlite:///ocr_scanner.db"

# SQLite Optimizations (Applied automatically)
SQLITE_JOURNAL_MODE="WAL"
SQLITE_SYNCHRONOUS="NORMAL"
SQLITE_CACHE_SIZE="10000"
SQLITE_TEMP_STORE="MEMORY"
```

## 🔒 Security Configuration

### HTTPS & SSL

```bash
# SSL Configuration (Production)
SSL_CERT_PATH="/path/to/ssl/cert.pem"
SSL_KEY_PATH="/path/to/ssl/private.key"
SSL_VERIFY_MODE="CERT_REQUIRED"
FORCE_HTTPS="true"

# Security Headers
ENABLE_CSP="true"
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'"
ENABLE_HSTS="true"
HSTS_MAX_AGE="31536000"  # 1 year
```

### Authentication & Authorization

```bash
# Password Security
PASSWORD_MIN_LENGTH="8"
PASSWORD_REQUIRE_UPPERCASE="true"
PASSWORD_REQUIRE_LOWERCASE="true"
PASSWORD_REQUIRE_NUMBERS="true"
PASSWORD_REQUIRE_SPECIAL="true"

# Session Security
SESSION_COOKIE_SECURE="true"    # HTTPS only
SESSION_COOKIE_HTTPONLY="true"  # No JavaScript access
SESSION_COOKIE_SAMESITE="Lax"   # CSRF protection

# Account Security
MAX_LOGIN_ATTEMPTS="5"
ACCOUNT_LOCKOUT_DURATION="900"  # 15 minutes
ENABLE_2FA="false"  # Two-factor authentication
```

## 📊 Monitoring & Logging

### Prometheus Metrics

```bash
# Prometheus Configuration
PROMETHEUS_METRICS_ENABLED="true"
PROMETHEUS_METRICS_PREFIX="ocr_scanner"
PROMETHEUS_METRICS_INCLUDE_REQUEST_DETAILS="true"

# Custom Metrics
ENABLE_DOCUMENT_TYPE_METRICS="true"
ENABLE_PROCESSING_TIME_METRICS="true"
ENABLE_ERROR_RATE_METRICS="true"
ENABLE_QUEUE_METRICS="true"
```

### Structured Logging

```bash
# Log Output Format
LOG_FORMAT="json"  # or "text"
LOG_INCLUDE_REQUEST_ID="true"
LOG_INCLUDE_USER_INFO="true"
LOG_INCLUDE_PERFORMANCE_DATA="true"

# Log Rotation
LOG_ROTATION_ENABLED="true"
LOG_MAX_SIZE="100MB"
LOG_RETENTION_DAYS="30"

# External Log Shipping
ENABLE_LOG_SHIPPING="false"
LOG_SHIPPING_ENDPOINT="https://logs.example.com"
LOG_SHIPPING_API_KEY="your-log-shipping-api-key"
```

## 🔄 WebSocket Configuration

### Real-time Features

```bash
# WebSocket Server Settings
WEBSOCKET_MAX_CONNECTIONS="1000"
WEBSOCKET_MESSAGE_RATE_LIMIT="100"  # Messages per minute per connection
WEBSOCKET_ENABLE_COMPRESSION="true"

# MCP WebSocket Integration
ENABLE_MCP_WEBSOCKETS="true"
MCP_WEBSOCKET_NAMESPACES="thinking,memory,context,workflows"
MCP_WEBSOCKET_AUTH_REQUIRED="true"

# Real-time Streaming
ENABLE_PROGRESS_STREAMING="true"
ENABLE_METRICS_STREAMING="true"
METRICS_STREAM_INTERVAL="5"  # seconds
```

## ⚙️ Performance Tuning

### Application Performance

```bash
# Worker Configuration
GUNICORN_WORKERS="4"
GUNICORN_WORKER_CLASS="gevent"
GUNICORN_WORKER_CONNECTIONS="1000"
GUNICORN_MAX_REQUESTS="1000"
GUNICORN_MAX_REQUESTS_JITTER="100"

# Cache Configuration
ENABLE_CACHING="true"
CACHE_TYPE="redis"  # or "memory"
CACHE_DEFAULT_TIMEOUT="300"  # 5 minutes
CACHE_KEY_PREFIX="ocr_scanner:"

# Database Performance
ENABLE_DATABASE_OPTIMIZATIONS="true"
AUTO_CREATE_INDEXES="true"
ENABLE_QUERY_OPTIMIZATION="true"
DATABASE_MAINTENANCE_INTERVAL="86400"  # 24 hours
```

### Resource Limits

```bash
# Memory Limits
MAX_MEMORY_USAGE="1GB"
ENABLE_MEMORY_MONITORING="true"
MEMORY_WARNING_THRESHOLD="80"  # Percentage

# CPU Limits
MAX_CPU_USAGE="80"  # Percentage
CPU_MONITORING_INTERVAL="30"  # seconds

# Disk Usage
MAX_DISK_USAGE="10GB"
ENABLE_DISK_CLEANUP="true"
CLEANUP_INTERVAL="3600"  # 1 hour
```

## 🐳 Docker Configuration

### Docker Compose Environment

```yaml
# docker-compose.yml environment section
environment:
  - SECRET_KEY=${SECRET_KEY}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  - DATABASE_URL=postgresql://postgres:password@db:5432/ocr_scanner
  - REDIS_URL=redis://redis:6379/0
  - CELERY_BROKER_URL=redis://redis:6379/0
  - CELERY_RESULT_BACKEND=redis://redis:6379/1
  - LOG_LEVEL=INFO
  - PROMETHEUS_METRICS_ENABLED=true
  - ENABLE_STRUCTURED_LOGGING=true
```

### Docker Environment File (.env)

```bash
# Create .env file for Docker Compose
SECRET_KEY=your-super-secure-secret-key-for-production
JWT_SECRET_KEY=your-jwt-secret-key-different-from-secret-key
DATABASE_URL=postgresql://postgres:secure_password@db:5432/ocr_scanner
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
FLASK_ENV=production
```

## 🧪 Testing Configuration

### Test Environment

```bash
# Testing Configuration
FLASK_ENV="testing"
TESTING="true"
SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
CELERY_TASK_ALWAYS_EAGER="true"
CACHE_TYPE="null"
WTF_CSRF_ENABLED="false"

# Test Coverage
COVERAGE_THRESHOLD="90"
ENABLE_PERFORMANCE_TESTS="true"
LOAD_TEST_DURATION="60"  # seconds
LOAD_TEST_USERS="10"
```

### Test Database

```bash
# Separate test database
TEST_DATABASE_URL="postgresql://test_user:test_pass@localhost:5432/ocr_scanner_test"
TEST_REDIS_URL="redis://localhost:6379/15"  # Use database 15 for tests
```

## 🚀 Production Deployment Checklist

### Security Checklist

- [ ] Set secure `SECRET_KEY` (minimum 32 characters)
- [ ] Set separate `JWT_SECRET_KEY` 
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure CORS with specific origins (not *)
- [ ] Enable request signing if needed
- [ ] Set up rate limiting
- [ ] Configure proper authentication
- [ ] Enable security headers (CSP, HSTS)

### Performance Checklist

- [ ] Use PostgreSQL for production database
- [ ] Configure Redis for caching and Celery
- [ ] Set up Celery workers for async processing
- [ ] Enable database optimizations
- [ ] Configure proper logging
- [ ] Set up monitoring (Prometheus)
- [ ] Configure resource limits
- [ ] Enable WebSocket compression

### Monitoring Checklist

- [ ] Configure structured logging
- [ ] Set up log rotation
- [ ] Enable Prometheus metrics
- [ ] Configure health checks
- [ ] Set up alerting
- [ ] Monitor database performance
- [ ] Track application metrics
- [ ] Monitor resource usage

### Backup & Recovery

```bash
# Database Backup Configuration
BACKUP_ENABLED="true"
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS="7"
BACKUP_STORAGE_PATH="/backups"
BACKUP_ENCRYPTION_KEY="your-backup-encryption-key"

# Redis Backup
REDIS_BACKUP_ENABLED="true"
REDIS_BACKUP_INTERVAL="3600"  # 1 hour
```

## 🔧 Configuration Templates

### Development Configuration Template

```bash
# .env.development
SECRET_KEY="dev-secret-key-change-in-production"
JWT_SECRET_KEY="dev-jwt-secret-key"
FLASK_ENV="development"
FLASK_DEBUG="true"
DATABASE_URL="sqlite:///ocr_scanner_dev.db"
REDIS_URL="redis://localhost:6379/0"
LOG_LEVEL="DEBUG"
CORS_ORIGINS="http://localhost:3000"
ENABLE_STRUCTURED_LOGGING="true"
PROMETHEUS_METRICS_ENABLED="true"
```

### Production Configuration Template

```bash
# .env.production
SECRET_KEY="CHANGE-THIS-TO-A-SECURE-32-CHAR-SECRET"
JWT_SECRET_KEY="CHANGE-THIS-TO-A-DIFFERENT-32-CHAR-SECRET"
FLASK_ENV="production"
FLASK_DEBUG="false"
DATABASE_URL="postgresql://user:pass@prod-db:5432/ocr_scanner"
REDIS_URL="redis://prod-redis:6379/0"
LOG_LEVEL="INFO"
CORS_ORIGINS="https://yourdomain.com"
ENABLE_STRUCTURED_LOGGING="true"
PROMETHEUS_METRICS_ENABLED="true"
RATE_LIMIT_REQUESTS="1000"
ENABLE_REQUEST_SIGNING="true"
```

## 🆘 Troubleshooting

### Common Configuration Issues

1. **Database Connection Errors**
   - Check `DATABASE_URL` format
   - Verify database server is running
   - Check network connectivity
   - Validate credentials

2. **Redis Connection Issues**
   - Verify `REDIS_URL` configuration
   - Check Redis server status
   - Validate Redis password if set

3. **WebSocket Connection Problems**
   - Check CORS configuration
   - Verify WebSocket port accessibility
   - Check firewall settings

4. **Performance Issues**
   - Review database indexes
   - Check Celery worker status
   - Monitor resource usage
   - Validate cache configuration

### Configuration Validation Script

```bash
# Run configuration validation
python validate_configuration.py

# Check specific component
python validate_configuration.py --component database
python validate_configuration.py --component redis
python validate_configuration.py --component security
```

## 📚 Additional Resources

- [Flask Configuration Documentation](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Celery Configuration Reference](https://docs.celeryproject.org/en/stable/userguide/configuration.html)
- [Redis Configuration Guide](https://redis.io/topics/config)
- [PostgreSQL Configuration Tuning](https://www.postgresql.org/docs/current/runtime-config.html)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)

---

This configuration guide provides comprehensive settings for all implemented features including async processing, monitoring, security, WebSocket support, MCP integration, and database optimizations. Adjust values based on your specific deployment requirements and infrastructure capabilities.