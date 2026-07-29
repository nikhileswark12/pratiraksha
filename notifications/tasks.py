from celery import shared_task
import logging
from .models import Notification
from pratiraksha.utils import log_activity

logger = logging.getLogger(__name__)

@shared_task
def dispatch_notification(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        
        # Stub the sending process
        logger.info(f"Stub-sending notification {notification.id}")
        logger.info(f"Type: {notification.type}")
        logger.info(f"Recipient: {notification.recipient}")
        logger.info(f"Payload: {notification.payload}")
        
        # Mark as stubbed
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
                "trigger_event": notification.trigger_event
            }
        )
        
        return True
    except Notification.DoesNotExist:
        logger.error(f"Notification with id {notification_id} does not exist.")
        return False
    except Exception as e:
        logger.error(f"Failed to dispatch notification {notification_id}: {e}")
        return False

