bind = "0.0.0.0:8000"
workers = 2  # Reduced from 4
worker_class = "gevent"  
worker_connections = 750  
timeout = 60 
keepalive = 2

# Log settings remain the same
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Worker recycling settings (good to keep)
max_requests = 1000
max_requests_jitter = 50

# Server mechanics remain the same
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None