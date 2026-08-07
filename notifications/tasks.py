from celery import shared_task
import logging
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client
from .models import Notification
from pratiraksha.utils import log_activity

logger = logging.getLogger(__name__)

@shared_task
def dispatch_notification(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.type == 'email':
            subject = notification.payload.get('subject', 'Pratiraksha Alert')
            message = notification.payload.get('message', '')
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [notification.recipient],
                    fail_silently=False,
                )
                notification.status = 'sent'
                notification.save(update_fields=['status'])
                
            except Exception as e:
                logger.error(f"Failed to send email to {notification.recipient}: {str(e)}")
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save(update_fields=['status', 'error_message'])
                
        elif notification.type == 'sms':
            message_body = notification.payload.get('message', '')
            
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=message_body,
                    from_=settings.TWILIO_FROM_NUMBER,
                    to=notification.recipient
                )
                notification.status = 'sent'
                notification.save(update_fields=['status'])
                
            except Exception as e:
                logger.error(f"Failed to send SMS to {notification.recipient}: {str(e)}")
                notification.status = 'failed'
                notification.error_message = str(e)
                notification.save(update_fields=['status', 'error_message'])
                
        elif notification.type == 'websocket':
            # Stubbed for now, or assumed handled by consumers
            notification.status = 'stubbed'
            notification.save(update_fields=['status'])
        
        # Log to ActivityLog
        log_activity(
            actor="system",
            action="notification triggered",
            resource_type="notification",
            resource_id=str(notification.id),
            extra_data={
                "type": notification.type,
                "recipient": notification.recipient,
                "trigger_event": notification.trigger_event,
                "final_status": notification.status
            }
        )
        
        return True
    except Notification.DoesNotExist:
        logger.error(f"Notification with id {notification_id} does not exist.")
        return False
    except Exception as e:
        logger.error(f"Failed to dispatch notification {notification_id}: {e}")
        return False
