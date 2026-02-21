#!/bin/bash

# OCR Scanner API - Gunicorn startup script

# Set environment variables if not already set
export FLASK_ENV=${FLASK_ENV:-"production"}
export SECRET_KEY=${SECRET_KEY:-"your-secret-key-here"}
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-"your-jwt-secret-key-here"}

# Database connection pooling settings
export DATABASE_POOL_SIZE=${DATABASE_POOL_SIZE:-10}
export DATABASE_POOL_RECYCLE=${DATABASE_POOL_RECYCLE:-3600}
export DATABASE_POOL_PRE_PING=${DATABASE_POOL_PRE_PING:-true}

# Redis settings for caching and rate limiting
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379/0"}
export RATE_LIMIT_STORAGE_URI=${RATE_LIMIT_STORAGE_URI:-"redis://localhost:6379/1"}

# OCR settings
export OCR_TIMEOUT=${OCR_TIMEOUT:-60}
export MAX_CONTENT_LENGTH=${MAX_CONTENT_LENGTH:-16777216}  # 16MB

# Logging
export LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "Starting OCR Scanner API with Gunicorn..."
echo "Environment: $FLASK_ENV"
echo "Workers: $(python -c 'import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)')"
echo "Bind: 0.0.0.0:5001"

# Run Gunicorn with the configuration file
exec gunicorn \
    --config gunicorn_config.py \
    "app:create_app()" \
    --log-level $LOG_LEVEL