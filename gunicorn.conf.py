# Gunicorn configuration file: gunicorn.conf.py
loglevel = 'error'

# Access log - requests
accesslog = '-'  # Writes access logs to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Error log - server errors
errorlog = '-'  # Writes error logs to stderr
log_format = '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s'

# Date format
log_date_format = '%Y-%m-%d %H:%M:%S'

timeout = 120
