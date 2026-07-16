from .base import *

# Override dev settings here
DEBUG = True
ALLOWED_HOSTS = ['*']

# Optional: Load DATABASE_URL from .env here if you're using python-dotenv,
# but for now default sqlite3 is in base.py and can be overridden.
