"""
Gunicorn configuration file for Django application deployment
"""
import multiprocessing

# Bind to 0.0.0.0:8000
bind = "0.0.0.0:8000"

# Number of worker processes
# A good rule of thumb is 2-4 x number of CPU cores
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = 'gevent'

# Timeout for worker processes
timeout = 120

# Maximum number of simultaneous clients
max_requests = 1000

# Maximum number of requests a worker will process before restarting
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'healthcare_app'
