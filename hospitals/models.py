from django.db import models
import uuid

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Hospital(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='hospitals', null=True, blank=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    zip_code = models.CharField(max_length=20)
    contact_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    
    # Capacity and Status (added Day 5)
    STATUS_CHOICES = [
        ('NORMAL', 'Normal'),
        ('MODERATE', 'Moderate'),
        ('CRITICAL', 'Critical'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='NORMAL')
    total_capacity = models.IntegerField(default=0)
    current_occupancy = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=50, blank=True)
    total_capacity = models.IntegerField(default=0)
    current_occupancy = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.hospital.name}"

class Equipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='equipment')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment')
    name = models.CharField(max_length=255)
    equipment_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='Available')
    quantity_total = models.IntegerField(default=1)
    quantity_available = models.IntegerField(default=1)
    quantity_in_use = models.IntegerField(default=0)
    quantity_maintenance = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.hospital.name})"
