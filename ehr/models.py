import uuid
from django.db import models
from django.conf import settings
from hospitals.models import Hospital

class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='patients')
    mrn = models.CharField(max_length=50) # hospital-scoped uniqueness enforced in save/logic
    name = models.CharField(max_length=255)
    dob = models.DateField()
    gender = models.CharField(max_length=50)
    blood_group = models.CharField(max_length=10)
    contact_phone = models.CharField(max_length=50)
    emergency_contact = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hospital', 'mrn')

    def __str__(self):
        return f"{self.name} ({self.mrn})"

class Encounter(models.Model):
    TYPE_CHOICES = (
        ('OPD', 'OPD'),
        ('IPD', 'IPD'),
        ('EMERGENCY', 'EMERGENCY'),
    )
    STATUS_CHOICES = (
        ('OPEN', 'OPEN'),
        ('DISCHARGED', 'DISCHARGED'),
        ('CLOSED', 'CLOSED'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='encounters')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')
    encounter_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    admitted_at = models.DateTimeField(auto_now_add=True)
    discharged_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.encounter_type} - {self.patient.name}"

class Vital(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='vitals')
    
    heart_rate = models.IntegerField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True) # e.g. "120/80"
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    spo2 = models.IntegerField(null=True, blank=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class Diagnosis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='diagnoses')
    
    icd10_code = models.CharField(max_length=20)
    description = models.TextField()
    is_primary = models.BooleanField(default=False)
    
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='prescriptions')
    
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration_days = models.IntegerField()
    
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class LabResult(models.Model):
    STATUS_CHOICES = (
        ('ORDERED', 'ORDERED'),
        ('RESULTED', 'RESULTED'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='labs')
    
    test_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ORDERED')
    result_value = models.TextField(null=True, blank=True)
    reference_range = models.CharField(max_length=255, null=True, blank=True)
    
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    
    ordered_at = models.DateTimeField(auto_now_add=True)
    resulted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class Allergy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='allergies')
    
    allergen = models.CharField(max_length=255)
    severity = models.CharField(max_length=50)
    reaction = models.TextField()
    
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supersedes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

class EHRAccessLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    action = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255)
    
    timestamp = models.DateTimeField(auto_now_add=True)

class DischargeSummary(models.Model):
    STATUS_CHOICES = (
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='discharge_summaries')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    file = models.FileField(upload_to='discharge_summaries/', null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
