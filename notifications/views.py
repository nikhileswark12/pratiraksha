from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import InAppNotification
from .serializers import InAppNotificationSerializer
from django.db.models import Q
from hospitals.models import Hospital

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InAppNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'hospital_manager':
            # Manager sees notifications for their hospital or specifically assigned to them
            qs = InAppNotification.objects.filter(
                Q(hospital_id=user.hospital_id) | Q(user=user)
            )
        elif user.role == 'operator':
            # Operator sees notifications for their tenant, or their tenant's hospitals, or specifically assigned
            tenant_hospitals = Hospital.objects.filter(tenant_id=user.tenant_id).values_list('id', flat=True)
            qs = InAppNotification.objects.filter(
                Q(tenant_id=user.tenant_id) | 
                Q(hospital_id__in=tenant_hospitals) | 
                Q(user=user)
            )
        else:
            qs = InAppNotification.objects.none()
            
        return qs.order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        notification = self.get_object() # This automatically uses get_queryset, enforcing RBAC (404 if not found)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(is_read=False)
        updated = qs.update(is_read=True)
        return Response({'status': 'success', 'updated': updated})

