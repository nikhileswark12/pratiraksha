from django.db import models
from hospitals.models import Hospital
import uuid
import secrets

class WebhookEndpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    secret = models.CharField(max_length=64, default=secrets.token_urlsafe, help_text="Secret used to sign the payload via HMAC.")
    events = models.JSONField(default=list, help_text="List of events this webhook subscribes to, e.g., ['hospital.status_changed', 'crisis.alert_created'].")
    
    # Scoping
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True, related_name='webhooks', help_text="If set, this webhook only receives events for this hospital.")
    tenant_id = models.UUIDField(null=True, blank=True, help_text="If set, this webhook only receives events for this tenant's hospitals.")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.url} (Active: {self.is_active})"
        