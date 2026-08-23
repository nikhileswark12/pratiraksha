from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import os

class EncryptedCharField(models.CharField):
    description = "Encrypted CharField using Fernet"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure we have a valid Fernet key. Fernet keys must be 32 url-safe base64-encoded bytes.
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            # Fallback to a static dev key if none provided (for development only)
            key = base64.urlsafe_b64encode(b'secret_key_32_bytes_for_dev_env!')
        self.fernet = Fernet(key)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None:
            return value
        # Encrypt the string
        return self.fernet.encrypt(value.encode('utf-8')).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return self.fernet.decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            # Return raw if decryption fails (e.g. data before encryption was added)
            return value
