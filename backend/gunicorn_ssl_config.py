"""
Gunicorn configuration for production with SSL support
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5001"
backlog = 2048

# SSL Configuration
if os.getenv('FORCE_HTTPS', 'false').lower() == 'true':
    keyfile = os.getenv('SSL_KEY_PATH', '/etc/ssl/private/server.key')
    certfile = os.getenv('SSL_CERT_PATH', '/etc/ssl/certs/server.crt')
    ssl_version = 'TLSv1_2'
    cert_reqs = 0
    ca_certs = None
    suppress_ragged_eofs = True
    do_handshake_on_connect = False
    ciphers = 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv('WORKER_CLASS', 'gevent')
worker_connections = int(os.getenv('WORKER_CONNECTIONS', 1000))
max_requests = 1000
max_requests_jitter = 50
timeout = int(os.getenv('WORKER_TIMEOUT', 120))
graceful_timeout = 30
keepalive = 5

# Thread settings (for threaded workers)
threads = int(os.getenv('THREADS_PER_WORKER', 2))

# Restart workers after this many requests, to help limit memory leaks
max_requests = 1000
max_requests_jitter = 50

# Preload application
preload_app = True

# Enable stats
statsd_host = os.getenv('STATSD_HOST', 'localhost:8125')
statsd_prefix = 'ocr_scanner'

# Access log - to STDOUT
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Error log - to STDERR
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# Process naming
proc_name = 'ocr-scanner-api'

# Server mechanics
daemon = False
pidfile = '/var/run/gunicorn.pid'
user = None
group = None
tmp_upload_dir = '/tmp'

# SSL Redirect middleware
def when_ready(server):
    """Called just after the server is started"""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT"""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked"""
    server.log.info(f"Forking worker {worker.pid}")

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("Forking new master process")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal"""
    worker.log.info(f"Worker aborted (pid: {worker.pid})")

# StatsD configuration for monitoring
def post_request(worker, req, environ, resp):
    """Called after a worker processes the request"""
    # Log request metrics
    worker.log.debug(f"{req.method} {req.path} - {resp.status_code}")