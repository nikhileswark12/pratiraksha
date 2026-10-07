from celery import shared_task
import logging
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client
from exponent_server_sdk import (
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
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
            
        elif notification.type == 'push':
            try:
                title = notification.payload.get('subject', 'Pratiraksha Alert')
                body = notification.payload.get('message', '')
                
                response = PushClient().publish(
                    PushMessage(
                        to=notification.recipient,
                        title=title,
                        body=body,
                        data=notification.payload.get('data', {})
                    )
                )
                
                response.validate_response()
                notification.status = 'sent'
                notification.save(update_fields=['status'])
                
            except PushServerError as exc:
                logger.error(f"PushServerError while sending to {notification.recipient}: {exc.errors}")
                notification.status = 'failed'
                notification.error_message = str(exc.errors)
                notification.save(update_fields=['status', 'error_message'])
            except (PushTicketError, Exception) as exc:
                logger.error(f"Failed to send Push to {notification.recipient}: {str(exc)}")
                notification.status = 'failed'
                notification.error_message = str(exc)
                notification.save(update_fields=['status', 'error_message'])
        
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

@shared_task
def process_status_change_notification(hospital_id, old_status, new_status, hospital_name, current_occupancy, total_capacity, tenant_id):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from notifications.models import Notification, InAppNotification
    
    channel_layer = get_channel_layer()
    tenant_group = f'hospital_updates_tenant_{tenant_id}'
    manager_group = f'hospital_updates_{hospital_id}'

    # In-App Notifications for status changes
    if old_status != new_status:
        in_app_notif = None
        if new_status == 'CRITICAL':
            in_app_notif = InAppNotification.objects.create(
                hospital_id=hospital_id,
                severity='CRITICAL',
                title='Capacity Critical',
                message=f"{hospital_name} is now CRITICAL ({current_occupancy}/{total_capacity} beds)."
            )
            # Create SMS/Email Notification for admins
            notif = Notification.objects.create(
                type='email',
                recipient='system_admin@test.com',
                hospital_id=hospital_id,
                trigger_event='hospital_critical',
                payload={
                    "hospital_name": hospital_name,
                    "occupancy": current_occupancy
                }
            )
            dispatch_notification.delay(notif.id)
            
            # Create SMS Notification
            sms_notif = Notification.objects.create(
                type='sms',
                recipient='+1234567890', # Stub for emergency contacts
                hospital_id=hospital_id,
                trigger_event='hospital_critical',
                payload={
                    "message": f"CRITICAL: {hospital_name} occupancy is {current_occupancy}."
                }
            )
            dispatch_notification.delay(sms_notif.id)
            
        elif new_status == 'MODERATE' and old_status == 'NORMAL':
            in_app_notif = InAppNotification.objects.create(
                hospital_id=hospital_id,
                severity='WARNING',
                title='Capacity Warning',
                message=f"{hospital_name} is experiencing moderate surge ({current_occupancy}/{total_capacity} beds)."
            )
        elif new_status == 'NORMAL' and old_status in ['MODERATE', 'CRITICAL']:
            in_app_notif = InAppNotification.objects.create(
                hospital_id=hospital_id,
                severity='INFO',
                title='Capacity Normalised',
                message=f"{hospital_name} has recovered to NORMAL capacity."
            )
            
        if in_app_notif:
            notif_event = {
                'type': 'notification.new',
                'notification_id': str(in_app_notif.id),
                'severity': in_app_notif.severity,
                'title': in_app_notif.title,
                'message': in_app_notif.message
            }
            async_to_sync(channel_layer.group_send)(tenant_group, notif_event)
            async_to_sync(channel_layer.group_send)(manager_group, notif_event)

@shared_task
def broadcast_hospital_update(hospital_id, changes, new_status, tenant_id):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    tenant_group = f'hospital_updates_tenant_{tenant_id}'
    manager_group = f'hospital_updates_{hospital_id}'
    
    update_event = {
        'type': 'hospital.updated',
        'hospital_id': str(hospital_id),
        'changes': changes,
        'new_status': new_status
    }
    async_to_sync(channel_layer.group_send)(tenant_group, update_event)
    async_to_sync(channel_layer.group_send)(manager_group, update_event)

@shared_task
def broadcast_hospital_critical(hospital_id, hospital_name, occupancy, tenant_id):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    tenant_group = f'hospital_updates_tenant_{tenant_id}'
    manager_group = f'hospital_updates_{hospital_id}'
    
    critical_event = {
        'type': 'hospital.critical',
        'hospital_id': str(hospital_id),
        'hospital_name': hospital_name,
        'occupancy': occupancy
    }
    async_to_sync(channel_layer.group_send)(tenant_group, critical_event)
    async_to_sync(channel_layer.group_send)(manager_group, critical_event)

@shared_task
def process_crisis_notification(affected_hospitals, scenario, estimated_patient_surge, tenant_id):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from notifications.models import InAppNotification
    
    channel_layer = get_channel_layer()
    
    notif_msg = f"A {scenario} simulation predicts a surge of {estimated_patient_surge} patients."
    if affected_hospitals == ["all_network"]:
        notif = InAppNotification.objects.create(
            tenant_id=tenant_id,
            severity='CRITICAL',
            title='Network-wide Crisis Simulation',
            message=notif_msg
        )
        async_to_sync(channel_layer.group_send)(
            f'hospital_updates_tenant_{tenant_id}', 
            {
                'type': 'notification.new',
                'notification_id': str(notif.id),
                'severity': notif.severity,
                'title': notif.title,
                'message': notif.message
            }
        )
    else:
        for hid in affected_hospitals:
            notif = InAppNotification.objects.create(
                hospital_id=hid,
                severity='CRITICAL',
                title='Hospital Crisis Simulation',
                message=notif_msg
            )
            async_to_sync(channel_layer.group_send)(
                f'hospital_updates_{hid}', 
                {
                    'type': 'notification.new',
                    'notification_id': str(notif.id),
                    'severity': notif.severity,
                    'title': notif.title,
                    'message': notif.message
                }
            )
