from .base import *
import os

DEBUG = False

# Strict host/origin settings for staging
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'staging.pratiraksha.com,127.0.0.1,localhost').split(',')
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://staging.pratiraksha.com').split(',')

# Ensure DB connection pool sizing matches production/staging targets
if 'default' in DATABASES and DATABASES['default']['ENGINE'] == 'dj_db_conn_pool.backends.postgresql':
    DATABASES['default']['POOL_OPTIONS'] = {
        'POOL_SIZE': int(os.environ.get('DB_POOL_SIZE', 10)),
        'MAX_OVERFLOW': int(os.environ.get('DB_MAX_OVERFLOW', 5)),
        'POOL_TIMEOUT': 5,
    }
