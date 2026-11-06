from rest_framework import serializers
from .models import Patient, Encounter, Vital, Diagnosis, Prescription, LabResult
import re
from django.utils import timezone


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('id', 'mrn', 'name', 'dob', 'gender', 'blood_group', 'contact_phone', 'emergency_contact', 'created_at', 'updated_at')
        read_only_fields = ('id', 'mrn', 'created_at', 'updated_at')

    def validate_dob(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_blood_group(self, value):
        normalized = value.strip().upper()
        if normalized not in {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNKNOWN'}:
            raise serializers.ValidationError("Enter a valid blood group.")
        return normalized


class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        fields = ('id', 'patient', 'encounter_type', 'status', 'admitted_at', 'discharged_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'admitted_at', 'discharged_at', 'created_at', 'updated_at')


class VitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vital
        fields = ('id', 'heart_rate', 'blood_pressure', 'temperature', 'respiratory_rate', 'spo2', 'recorded_at', 'created_by')
        read_only_fields = ('id', 'recorded_at', 'created_by')

    def validate_heart_rate(self, value):
        if value is not None and not 20 <= value <= 300:
            raise serializers.ValidationError("Heart rate must be between 20 and 300 bpm.")
        return value

    def validate_blood_pressure(self, value):
        if value is not None and not re.fullmatch(r'\s*\d{2,3}\s*/\s*\d{2,3}\s*', value):
            raise serializers.ValidationError("Blood pressure must use systolic/diastolic format.")
        return value

    def validate_temperature(self, value):
        if value is not None and not 25 <= value <= 45:
            raise serializers.ValidationError("Temperature must be between 25 and 45 °C.")
        return value

    def validate_respiratory_rate(self, value):
        if value is not None and not 1 <= value <= 80:
            raise serializers.ValidationError("Respiratory rate must be between 1 and 80 breaths per minute.")
        return value

    def validate_spo2(self, value):
        if value is not None and not 0 <= value <= 100:
            raise serializers.ValidationError("SpO2 must be between 0 and 100 percent.")
        return value


class DiagnosisSerializer(serializers.ModelSerializer):
    supersedes_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Diagnosis
        fields = ('id', 'icd10_code', 'description', 'is_primary', 'supersedes_id', 'superseded_by', 'created_at', 'created_by')
        read_only_fields = ('id', 'superseded_by', 'created_at', 'created_by')


class PrescriptionSerializer(serializers.ModelSerializer):
    supersedes_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Prescription
        fields = ('id', 'medication_name', 'dosage', 'frequency', 'duration_days', 'supersedes_id', 'superseded_by', 'created_at', 'created_by')
        read_only_fields = ('id', 'superseded_by', 'created_at', 'created_by')

    def validate_duration_days(self, value):
        if value < 1 or value > 3650:
            raise serializers.ValidationError("Prescription duration must be between 1 and 3650 days.")
        return value


class LabResultSerializer(serializers.ModelSerializer):
    supersedes_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = LabResult
        fields = ('id', 'test_name', 'status', 'result_value', 'reference_range', 'supersedes_id', 'superseded_by', 'ordered_at', 'resulted_at', 'created_by')
        read_only_fields = ('id', 'superseded_by', 'ordered_at', 'resulted_at', 'created_by')
