#!/usr/bin/env python3
"""
Gunicorn configuration for the Loan Agent API
Optimized for AI/LLM workloads with longer processing times
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5500"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings - Critical for AI workloads
timeout = 120  # 2 minutes - increased for LLM processing
keepalive = 2
graceful_timeout = 30
worker_tmp_dir = "/dev/shm"  # Use RAM for temporary files

# Process naming
proc_name = "loan_agent_api"

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
sendfile = True
reuse_port = True

# Health checks
check_config = True

# Worker lifecycle
worker_exit_on_app_exit = True

# Environment variables
raw_env = [
    "PYTHONPATH=/app",
    "FLASK_ENV=production"
]

def when_ready(server):
    """Called just after the server is started"""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker has been initialized"""
    worker.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker has been forked"""
    server.log.info("Worker will be spawned")

def post_fork(server, worker):
    """Called just after a worker has been forked"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Called just after a worker has initialized the application"""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker received SIGABRT signal"""
    worker.log.info("Worker received SIGABRT")

def pre_exec(server):
    """Called just before a new master process is forked"""
    server.log.info("Forked child, re-executing.")

def on_starting(server):
    """Called just after the server is started"""
    server.log.info("Server is starting")

def on_reload(server):
    """Called to reload the server"""
    server.log.info("Server reloading")

def on_exit(server):
    """Called just before exiting"""
    server.log.info("Server exiting")

def child_exit(server, worker):
    """Called just after a worker has been exited"""
    server.log.info("Worker exited (pid: %s)", worker.pid)

def worker_exit(server, worker):
    """Called just after a worker has been exited"""
    server.log.info("Worker exited (pid: %s)", worker.pid)

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed"""
    server.log.info("Number of workers changed from %s to %s", old_value, new_value)

def on_exit(server):
    """Called just before exiting"""
    server.log.info("Server exiting")

# Custom error handling
def worker_int(worker):
    """Called when a worker receives SIGINT or SIGTERM"""
    worker.log.info("Worker received SIGINT or SIGTERM")

def pre_request(worker, req):
    """Called just before a worker processes the request"""
    worker.log.info("Processing request: %s", req.uri)

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request"""
    worker.log.info("Request processed: %s", req.uri) 