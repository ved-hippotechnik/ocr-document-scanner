"""
Gunicorn configuration file for OCR Scanner API
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
graceful_timeout = 30
keepalive = 2

# Connection pooling
# These settings help prevent connection pool exhaustion
worker_tmp_dir = "/dev/shm"
preload_app = True

# Threads
threads = 4

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'ocr-scanner-api'

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment for HTTPS)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Environment
raw_env = [
    f"DATABASE_URL={os.environ.get('DATABASE_URL', 'sqlite:///ocr_scanner.db')}",
    f"REDIS_URL={os.environ.get('REDIS_URL', 'redis://localhost:6379/0')}",
    f"SECRET_KEY={os.environ.get('SECRET_KEY', 'dev-key-change-in-production')}",
    f"JWT_SECRET_KEY={os.environ.get('JWT_SECRET_KEY', 'jwt-key-change-in-production')}",
]

# Hooks
def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawning (pid: %s)", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("worker received INT or QUIT signal")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Server is shutting down")

# Development vs Production settings
if os.environ.get('FLASK_ENV') == 'development':
    reload = True
    workers = 2
    threads = 2
else:
    reload = False
    
# Memory optimization
max_worker_memory_usage = 512 * 1024 * 1024  # 512MB per worker

# Request handling
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190