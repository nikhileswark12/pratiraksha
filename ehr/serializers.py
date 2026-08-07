from rest_framework import serializers
from .models import Patient, Encounter, Vital, Diagnosis, Prescription, LabResult, Allergy

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('hospital', 'mrn', 'created_at', 'updated_at')

class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        fields = '__all__'
        read_only_fields = ('hospital', 'status', 'admitted_at', 'discharged_at', 'created_at', 'updated_at')

class VitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vital
        fields = '__all__'
        read_only_fields = ('hospital', 'encounter', 'recorded_at', 'created_by')

class DiagnosisSerializer(serializers.ModelSerializer):
    supersedes_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Diagnosis
        fields = '__all__'
        read_only_fields = ('hospital', 'encounter', 'superseded_by', 'created_at', 'created_by')

class PrescriptionSerializer(serializers.ModelSerializer):
    supersedes_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ('hospital', 'encounter', 'superseded_by', 'created_at', 'created_by')

class LabResultSerializer(serializers.ModelSerializer):
    supersedes_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = LabResult
        fields = '__all__'
        read_only_fields = ('hospital', 'encounter', 'superseded_by', 'ordered_at', 'resulted_at', 'created_by')
