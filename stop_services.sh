#!/bin/bash

# Stop OCR Document Scanner Services
echo "🛑 Stopping OCR Document Scanner Services..."

# Stop Flask application (if running in background)
if pgrep -f "python.*run.py" > /dev/null; then
    echo "🛑 Stopping Flask application..."
    pkill -f "python.*run.py"
    echo "✅ Flask application stopped"
else
    echo "ℹ️ Flask application not running in background"
fi

# Stop Celery worker (if running)
if pgrep -f "celery.*worker" > /dev/null; then
    echo "🛑 Stopping Celery worker..."
    pkill -f "celery.*worker"
    echo "✅ Celery worker stopped"
else
    echo "ℹ️ Celery worker not running"
fi

# Stop Redis server (if running and not system-wide)
if pgrep -f "redis-server" > /dev/null; then
    echo "ℹ️ Redis server is running (may be system-wide, not stopping automatically)"
else
    echo "ℹ️ Redis server not running"
fi

echo "✅ OCR Document Scanner services cleanup complete!"
echo "ℹ️ To manually stop the Flask app running in terminal, use Ctrl+C in the terminal"
