from rest_framework import serializers
from .models import Hospital, Department, Equipment


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'contact_number', 'total_capacity', 'current_occupancy', 'created_at', 'updated_at')

    def validate(self, attrs):
        capacity = attrs.get('total_capacity', getattr(self.instance, 'total_capacity', 0))
        occupancy = attrs.get('current_occupancy', getattr(self.instance, 'current_occupancy', 0))
        if capacity < 0 or occupancy < 0 or occupancy > capacity:
            raise serializers.ValidationError("Department occupancy must be non-negative and cannot exceed its capacity.")
        return attrs


class EquipmentSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Equipment
        fields = ('id', 'name', 'equipment_type', 'status', 'department', 'department_name', 'quantity_total', 'quantity_available', 'quantity_in_use', 'quantity_maintenance', 'created_at', 'updated_at')

    def validate(self, attrs):
        total = attrs.get('quantity_total', getattr(self.instance, 'quantity_total', 1))
        available = attrs.get('quantity_available', getattr(self.instance, 'quantity_available', 1))
        in_use = attrs.get('quantity_in_use', getattr(self.instance, 'quantity_in_use', 0))
        maintenance = attrs.get('quantity_maintenance', getattr(self.instance, 'quantity_maintenance', 0))
        values = (total, available, in_use, maintenance)
        if any(value < 0 for value in values) or available + in_use + maintenance > total:
            raise serializers.ValidationError("Equipment quantities must be non-negative and allocated quantities cannot exceed total quantity.")
        department = attrs.get('department', getattr(self.instance, 'department', None))
        hospital = attrs.get('hospital', getattr(self.instance, 'hospital', None))
        if department and hospital and department.hospital_id != hospital.id:
            raise serializers.ValidationError({"department": "Department must belong to the same hospital as the equipment."})
        return attrs


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
    class Meta:
        model = Hospital
        fields = ('name', 'address', 'zip_code', 'contact_number', 'email', 'status', 'total_capacity', 'current_occupancy')

    def validate(self, attrs):
        capacity = attrs.get('total_capacity', self.instance.total_capacity)
        occupancy = attrs.get('current_occupancy', self.instance.current_occupancy)
        if capacity < 0 or occupancy < 0 or occupancy > capacity:
            raise serializers.ValidationError("Hospital occupancy must be non-negative and cannot exceed total capacity.")
        return attrs
