from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, mixins, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from integrations.tasks import dispatch_webhook_event
from .models import Hospital
from pratiraksha.utils import log_compliance_event
from .serializers import (
    HospitalListSerializer,
    HospitalDetailSerializer,
    HospitalUpdateSerializer,
    DepartmentSerializer,
    EquipmentSerializer
)
from .permissions import CombinedHospitalPermission

class HospitalViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for Hospital operations.
    Inherits Retrieve, Update, and List. 
    Explicitly omits Create and Destroy.
    """
    permission_classes = [permissions.IsAuthenticated, CombinedHospitalPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'address', 'zip_code']
    ordering_fields = ['name', 'current_occupancy', 'created_at']

    def get_queryset(self):
        qs = Hospital.objects.all()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return Hospital.objects.none()
            
        if user.role == 'operator':
            if user.tenant_id:
                qs = qs.filter(tenant_id=user.tenant_id)
            else:
                qs = Hospital.objects.none()
        elif user.role == 'hospital_manager':
            if user.hospital_id:
                qs = qs.filter(id=user.hospital_id)
            else:
                qs = Hospital.objects.none()
                
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return HospitalListSerializer
        elif self.action in ['update', 'partial_update']:
            return HospitalUpdateSerializer
        return HospitalDetailSerializer
        
    def perform_update(self, serializer):
        # Check if status is changing
        old_status = serializer.instance.status if serializer.instance else None
        
        instance = serializer.save()
        
        log_compliance_event(
            actor=str(self.request.user.id),
            action="hospital_updated",
            resource_type="hospital",
            resource_id=str(instance.id),
            extra_data={"tenant_id": str(instance.tenant_id) if instance.tenant_id else None}
        )
        
        # Dispatch webhook if status changed
        if old_status and old_status != instance.status:
            dispatch_webhook_event.delay(
                event_type='hospital.status_changed',
                payload={
                    "hospital_id": str(instance.id),
                    "old_status": old_status,
                    "new_status": instance.status,
                    "timestamp": str(instance.updated_at)
                },
                hospital_id=str(instance.id),
                tenant_id=str(instance.tenant_id) if instance.tenant_id else None
            )

    @action(detail=True, methods=['get'])
    def departments(self, request, pk=None):
        hospital = self.get_object()
        departments = hospital.departments.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def equipment(self, request, pk=None):
        hospital = self.get_object()
        equipment = hospital.equipment.all()
        serializer = EquipmentSerializer(equipment, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='occupancy-trend')
    def occupancy_trend(self, request, pk=None):
        # We still verify the object permissions
        hospital = self.get_object()
        
        # Stub response since predictions/EHR are Day 18+
        dummy_trend = [
            {"time": "08:00", "occupancy": 75},
            {"time": "12:00", "occupancy": 82},
            {"time": "16:00", "occupancy": 88},
            {"time": "20:00", "occupancy": 85},
        ]
        return Response({"hospital_id": hospital.id, "trend": dummy_trend})
