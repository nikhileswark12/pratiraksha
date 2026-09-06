from .base import *
import os

DEBUG = False

# Strict host/origin settings for production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'pratiraksha.com,api.pratiraksha.com').split(',')
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://pratiraksha.com,https://app.pratiraksha.com').split(',')

# Ensure DB connection pool sizing matches production targets
if 'default' in DATABASES and DATABASES['default']['ENGINE'] == 'dj_db_conn_pool.backends.postgresql':
    DATABASES['default']['POOL_OPTIONS'] = {
        'POOL_SIZE': int(os.environ.get('DB_POOL_SIZE', 20)),
        'MAX_OVERFLOW': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
        'POOL_TIMEOUT': 5,
    }
