from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Hospital
from notifications.models import Notification
from notifications.tasks import dispatch_notification
from pratiraksha.utils import log_activity

@receiver(post_save, sender=Hospital)
def hospital_post_save(sender, instance, created, update_fields, **kwargs):
    channel_layer = get_channel_layer()
    
    # In a real app we'd track original values to see what actually changed.
    # For now, we assume if it saved, it might have changed.
    changes = {
        "status": instance.status,
        "total_capacity": instance.total_capacity,
        "current_occupancy": instance.current_occupancy
    }

    # Group for operators
    global_group = 'hospital_updates'
    # Group for managers of this specific hospital
    manager_group = f'hospital_updates_{instance.id}'

    # Emit hospital.updated
    update_event = {
        'type': 'hospital.updated',
        'hospital_id': str(instance.id),
        'changes': changes,
        'new_status': instance.status
    }
    async_to_sync(channel_layer.group_send)(global_group, update_event)
    async_to_sync(channel_layer.group_send)(manager_group, update_event)

    # Emit hospital.critical if status is CRITICAL
    if instance.status == 'CRITICAL':
        critical_event = {
            'type': 'hospital.critical',
            'hospital_id': str(instance.id),
            'hospital_name': instance.name,
            'occupancy': instance.current_occupancy
        }
        async_to_sync(channel_layer.group_send)(global_group, critical_event)
        async_to_sync(channel_layer.group_send)(manager_group, critical_event)
        
        # Enqueue Notification
        notif = Notification.objects.create(
            type='email',
            recipient='system_admin@test.com',
            hospital_id=instance.id,
            trigger_event='hospital_critical',
            payload={
                "hospital_name": instance.name,
                "occupancy": instance.current_occupancy
            }
        )
        dispatch_notification.delay(notif.id)

    # Log to ActivityLog
    log_activity(
        actor="system",
        action="hospital update",
        resource_type="hospital",
        resource_id=str(instance.id),
        extra_data={"new_status": instance.status}
    )
