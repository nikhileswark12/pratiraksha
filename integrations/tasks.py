import json
import hmac
import hashlib
import requests
import logging
from celery import shared_task
from .models import WebhookEndpoint

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def dispatch_webhook_event(self, event_type, payload, hospital_id=None, tenant_id=None):
    """
    Finds all active WebhookEndpoints subscribed to `event_type` that match the given scoping.
    Signs the payload and dispatches an HTTP POST request.
    """
    # 1. Find matching endpoints
    qs = WebhookEndpoint.objects.filter(is_active=True, events__contains=event_type)
    
    # 2. Filter by scope if provided
    endpoints_to_notify = []
    for endpoint in qs:
        # If endpoint has a hospital set, only notify if the event is for that hospital
        if endpoint.hospital_id and str(endpoint.hospital_id) != str(hospital_id):
            continue
            
        # If endpoint has a tenant set, only notify if the event is for that tenant
        if endpoint.tenant_id and str(endpoint.tenant_id) != str(tenant_id):
            continue
            
        endpoints_to_notify.append(endpoint)
        
    if not endpoints_to_notify:
        return f"No matching webhooks for event {event_type}"

    # 3. Serialize payload
    data_str = json.dumps(payload, default=str)
    
    success_count = 0
    
    for endpoint in endpoints_to_notify:
        # 4. Generate signature
        signature = hmac.new(
            endpoint.secret.encode('utf-8'),
            data_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'X-Pratiraksha-Signature': f"sha256={signature}",
            'X-Pratiraksha-Event': event_type
        }
        
        try:
            # 5. Dispatch request
            response = requests.post(endpoint.url, data=data_str, headers=headers, timeout=10)
            response.raise_for_status()
            success_count += 1
            logger.info(f"Webhook {event_type} delivered to {endpoint.url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to deliver webhook {event_type} to {endpoint.url}: {str(e)}")
            # In a real system, we might retry per-endpoint, but for now we log the error
            # as required by rule 3: "Fail loud, don't fail silent."
            
    return f"Delivered to {success_count}/{len(endpoints_to_notify)} endpoints."
