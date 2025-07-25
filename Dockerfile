# Enhanced OCR Document Scanner - Multi-stage Dockerfile

# Base stage with common dependencies
FROM python:3.10-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libgthread-2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-hin \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-por \
    tesseract-ocr-rus \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend builder stage
FROM base AS backend-builder

# Copy backend application code
COPY backend/ /app/backend/
COPY *.py /app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs /app/models /app/analytics_charts

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=backend/run.py \
    TESSERACT_CMD=/usr/bin/tesseract

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Development stage
FROM backend-builder AS development

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

CMD ["python", "backend/run.py"]

# Production stage
FROM backend-builder AS production

ENV FLASK_ENV=production

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "sync", "--timeout", "120", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "100", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "--log-level", "info", "backend.run:app"]

# Frontend stage
FROM node:18-alpine AS frontend

WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .

# Build frontend
RUN npm run build

# Expose port
EXPOSE 3000

# Development command
CMD ["npm", "start"]

# Default stage (production)
FROM production AS default
