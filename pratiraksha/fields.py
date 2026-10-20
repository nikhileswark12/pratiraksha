from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
from django.core.exceptions import ImproperlyConfigured

class EncryptedCharField(models.CharField):
    description = "Encrypted CharField using Fernet"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure we have a valid Fernet key. Fernet keys must be 32 url-safe base64-encoded bytes.
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            if not settings.DEBUG:
                raise ImproperlyConfigured(
                    "ENCRYPTION_KEY must be configured when DEBUG is False."
                )
            # Development-only fallback. Never use this key for production data.
            key = base64.urlsafe_b64encode(b'secret_key_32_bytes_for_dev_env!')
        try:
            self.fernet = Fernet(key.encode("utf-8") if isinstance(key, str) else key)
        except (TypeError, ValueError) as exc:
            raise ImproperlyConfigured("ENCRYPTION_KEY must be a valid Fernet key.") from exc

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
