# Gunicorn configuration file: gunicorn.conf.py

# Access log - requests
accesslog = '/usr/local/var/log/gunicorn-access.log'  # use '-' for stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Error log - server errors
errorlog = '/usr/local/var/log/gunicorn-error.log'  # use '-' for stdout
log_format = '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s'

# Date format
log_date_format = '%Y-%m-%d %H:%M:%S'

timeout=120

