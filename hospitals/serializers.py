from rest_framework import serializers
from .models import Hospital, Department, Equipment

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'contact_number', 'total_capacity', 'current_occupancy', 'created_at', 'updated_at')

class EquipmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Equipment
        fields = ('id', 'name', 'equipment_type', 'status', 'department', 'department_name', 'quantity_total', 'quantity_available', 'quantity_in_use', 'quantity_maintenance', 'created_at', 'updated_at')

class HospitalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ('id', 'name', 'address', 'zip_code', 'contact_number', 'email', 'status', 'total_capacity', 'current_occupancy', 'created_at', 'updated_at')

class HospitalDetailSerializer(serializers.ModelSerializer):
    departments = DepartmentSerializer(many=True, read_only=True)
    equipment = EquipmentSerializer(many=True, read_only=True)

    class Meta:
        model = Hospital
        fields = ('id', 'name', 'address', 'zip_code', 'contact_number', 'email', 'status', 'total_capacity', 'current_occupancy', 'departments', 'equipment', 'created_at', 'updated_at')

class HospitalUpdateSerializer(serializers.ModelSerializer):
    # Managers might update contact info, but id and created_at are naturally read-only.
    # We explicitly restrict what can be updated via API.
    class Meta:
        model = Hospital
        fields = ('name', 'address', 'zip_code', 'contact_number', 'email', 'status', 'total_capacity', 'current_occupancy')
