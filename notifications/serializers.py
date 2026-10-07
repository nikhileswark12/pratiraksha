from rest_framework import serializers
from .models import InAppNotification

class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = ['id', 'user', 'tenant_id', 'hospital_id', 'severity', 'title', 'message', 'is_read', 'created_at']
