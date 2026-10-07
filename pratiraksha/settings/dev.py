from .base import *

# Override dev settings here
DEBUG = True
ALLOWED_HOSTS = ['*']

import sys
if 'pytest' in sys.argv[0] or 'test' in sys.argv:
    CELERY_TASK_ALWAYS_EAGER = True
