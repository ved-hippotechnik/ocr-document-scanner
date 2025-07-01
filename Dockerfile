# Multi-stage build for OCR Document Scanner
FROM python:3.9-slim AS backend-builder

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-hin \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Frontend build stage
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

# Final production stage
FROM python:3.9-slim

# Install runtime dependencies and create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-hin \
    tesseract-ocr-jpn \
    tesseract-ocr-kor \
    tesseract-ocr-spa \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

WORKDIR /app

# Copy backend from builder
COPY --from=backend-builder /app/backend ./backend
COPY --from=backend-builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy frontend build
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create upload and logs directory with proper permissions
RUN mkdir -p /app/uploads /app/logs \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app \
    && chmod -R 777 /app/uploads /app/logs

# Set environment variables
ENV FLASK_APP=backend/run.py \
    FLASK_ENV=production \
    TESSERACT_CMD=/usr/bin/tesseract \
    PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

# Use gunicorn for production with better configuration
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "backend.run:app"]
