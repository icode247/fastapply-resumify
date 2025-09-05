import os

port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Increased timeout for AI processing
keepalive = 2

# Log settings
loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Worker settings
max_requests = 1000
max_requests_jitter = 50

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None
