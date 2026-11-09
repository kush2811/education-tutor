"""Production Gunicorn configuration for FastAPI ASGI application."""

import multiprocessing
import os

# Server socket
bind = f"{os.getenv('BACKEND_HOST', '0.0.0.0')}:{os.getenv('BACKEND_PORT', '8000')}"
backlog = 2048

# Worker processes
# Standard calculation: 2 x CPU cores + 1, or override via env
default_workers = max(2, min(multiprocessing.cpu_count() * 2 + 1, 8))
workers = int(os.getenv("WEB_CONCURRENCY", default_workers))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5
graceful_timeout = 30

# Memory & Process hygiene
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" (%(L)ss)'
