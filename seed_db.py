import os
import django
import uuid
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratiraksha.settings.dev')
django.setup()

from hospitals.models import Tenant, Hospital, Department, Equipment
from ehr.models import Patient, Encounter
from accounts.models import User

def seed():
    # Create operator user
    if not User.objects.filter(email='operator@example.com').exists():
        User.objects.create_user(
            email='operator@example.com',
            password='Password123!',
            role='operator'
        )

    print("Creating Tenant...")
    tenant, _ = Tenant.objects.get_or_create(name='National Health Network')
    
    print("Creating Hospitals...")
    hospitals = []
    for i in range(50):
        h = Hospital.objects.create(
            tenant=tenant,
            name=f"General Hospital {i}",
            address=f"{i} Health Way",
            zip_code=f"100{i:02d}",
            total_capacity=random.randint(100, 500),
            current_occupancy=random.randint(50, 400),
            status=random.choice(['NORMAL', 'MODERATE', 'CRITICAL'])
        )
        hospitals.append(h)
    
    # Store first hospital ID for our load tests
    h_id = str(hospitals[0].id)
    print(f"First Hospital ID (for tests): {h_id}")
    
    if not User.objects.filter(email='manager@example.com').exists():
        User.objects.create_user(
            email='manager@example.com',
            password='Password123!',
            role='hospital_manager',
            hospital_id=h_id,
            tenant_id=str(tenant.id)
        )
    
    print("Creating Departments and Equipment...")
    for h in hospitals:
        for d_name in ['ER', 'ICU', 'Pediatrics', 'General']:
            d = Department.objects.create(
                hospital=h,
                name=d_name,
                total_capacity=random.randint(20, 100),
                current_occupancy=random.randint(10, 90)
            )
            for e_name in ['Ventilator', 'Defibrillator', 'Monitor']:
                Equipment.objects.create(
                    hospital=h,
                    department=d,
                    name=e_name,
                    equipment_type='Medical',
                    quantity_total=random.randint(5, 50),
                    quantity_available=random.randint(0, 40)
                )

    print("Creating EHR records...")
    # Seed 5,000 patients and 10,000 encounters to simulate real data volume
    patients = []
    for i in range(5000):
        if i % 1000 == 0:
            print(f"  ... {i} patients created")
        p = Patient(
            hospital=random.choice(hospitals),
            mrn=f"MRN{i}",
            name=f"Patient{i} Test",
            dob="1980-01-01",
            gender="M",
            blood_group="O+",
            contact_phone="555-0101",
            emergency_contact="555-0202",
        )
        patients.append(p)
    
    Patient.objects.bulk_create(patients, batch_size=1000)
    
    # Refetch patients to get IDs
    patients = list(Patient.objects.all())
    
    encounters = []
    for i in range(10000):
        if i % 2000 == 0:
            print(f"  ... {i} encounters created")
        e = Encounter(
            patient=random.choice(patients),
            hospital=random.choice(hospitals),
            encounter_type=random.choice(['OPD', 'IPD', 'EMERGENCY']),
            status=random.choice(['OPEN', 'DISCHARGED', 'CLOSED'])
        )
        encounters.append(e)
    
    Encounter.objects.bulk_create(encounters, batch_size=1000)
    print("Database seeding completed.")

if __name__ == '__main__':
    seed()
