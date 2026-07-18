from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Hospital
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
    queryset = Hospital.objects.all()
    permission_classes = [permissions.IsAuthenticated, CombinedHospitalPermission]

    def get_serializer_class(self):
        if self.action == 'list':
            return HospitalListSerializer
        elif self.action in ['update', 'partial_update']:
            return HospitalUpdateSerializer
        return HospitalDetailSerializer

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
