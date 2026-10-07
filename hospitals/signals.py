from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Hospital
from pratiraksha.utils import log_activity
from notifications.tasks import process_status_change_notification, broadcast_hospital_update, broadcast_hospital_critical

@receiver(pre_save, sender=Hospital)
def hospital_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Hospital.objects.get(pk=instance.pk)
            instance._original_status = old_instance.status
        except Hospital.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Hospital)
def hospital_post_save(sender, instance, created, update_fields, **kwargs):
    changes = {
        "status": instance.status,
        "total_capacity": instance.total_capacity,
        "current_occupancy": instance.current_occupancy
    }

    # Asynchronous broadcast of hospital updates
    broadcast_hospital_update.delay(str(instance.id), changes, instance.status, str(instance.tenant_id))

    old_status = getattr(instance, '_original_status', None)

    if instance.status == 'CRITICAL':
        # Asynchronous broadcast of hospital critical event
        broadcast_hospital_critical.delay(str(instance.id), instance.name, instance.current_occupancy, str(instance.tenant_id))

    # Process status change notification asynchronously
    if old_status != instance.status:
        process_status_change_notification.delay(
            str(instance.id),
            old_status,
            instance.status,
            instance.name,
            instance.current_occupancy,
            instance.total_capacity,
            str(instance.tenant_id)
        )

    # Log to ActivityLog
    log_activity(
        actor="system",
        action="hospital update",
        resource_type="hospital",
        resource_id=str(instance.id),
        extra_data={"new_status": instance.status}
    )
