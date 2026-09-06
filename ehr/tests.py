from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from hospitals.models import Hospital
from ehr.models import Patient, Encounter, Vital, Diagnosis, Prescription, LabResult
from unittest.mock import patch

User = get_user_model()

class EHRTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        
        from hospitals.models import Tenant
        t = Tenant.objects.create(name="Test Tenant")
        self.hospital1 = Hospital.objects.create(name="Hospital 1", total_capacity=100, tenant=t)
        self.hospital2 = Hospital.objects.create(name="Hospital 2", total_capacity=100, tenant=t)
        
        self.manager1 = User.objects.create_user(email="manager1@test.com", password="pass", role="hospital_manager", hospital=self.hospital1)
        self.manager2 = User.objects.create_user(email="manager2@test.com", password="pass", role="hospital_manager", hospital=self.hospital2)
        self.operator = User.objects.create_user(email="operator@test.com", password="pass", role="operator", tenant=t)
        
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.manager1)
        
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.manager2)
        
        self.operator_client = APIClient()
        self.operator_client.force_authenticate(user=self.operator)
        
    def test_create_patient(self):
        data = {
            "name": "John Doe",
            "dob": "1980-01-01",
            "gender": "Male",
            "blood_group": "O+",
            "contact_phone": "1234567890",
            "emergency_contact": "Jane Doe 0987654321"
        }
        
        # Operator cannot create patient
        res = self.operator_client.post('/api/v1/ehr/patients/', data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
        # Manager 1 can create patient
        res = self.client1.post('/api/v1/ehr/patients/', data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue('mrn' in res.data)
        
        # Verify it is in hospital 1
        patient = Patient.objects.get(id=res.data['id'])
        self.assertEqual(patient.hospital, self.hospital1)
        
    def test_create_encounter_and_clinical_data(self):
        patient = Patient.objects.create(hospital=self.hospital1, mrn="PRX-1-000001", name="Test", dob="1990-01-01", gender="M", blood_group="A+", contact_phone="1", emergency_contact="1")
        
        # Create encounter
        res = self.client1.post('/api/v1/ehr/encounters/', {"patient": patient.id, "encounter_type": "IPD"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        encounter_id = res.data['id']
        
        # Manager 2 cannot add to hospital 1's encounter
        res = self.client2.post(f'/api/v1/ehr/encounters/{encounter_id}/vitals/', {"heart_rate": 80})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        
        # Manager 1 adds vital
        res = self.client1.post(f'/api/v1/ehr/encounters/{encounter_id}/vitals/', {"heart_rate": 80})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Append only correction on diagnosis
        res = self.client1.post(f'/api/v1/ehr/encounters/{encounter_id}/diagnoses/', {"icd10_code": "R50.9", "description": "Fever"})
        diag_id = res.data.get('id')
        
        # Create correction
        res = self.client1.post(f'/api/v1/ehr/encounters/{encounter_id}/diagnoses/', {"icd10_code": "R50.9", "description": "High Fever", "supersedes_id": diag_id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        old_diag = Diagnosis.objects.get(id=diag_id)
        self.assertIsNotNone(old_diag.superseded_by)
        
    def test_timeline_filters_superseded(self):
        patient = Patient.objects.create(hospital=self.hospital1, mrn="PRX-1-001", name="Test", dob="1990-01-01", gender="M", blood_group="A+", contact_phone="1", emergency_contact="1")
        encounter = Encounter.objects.create(hospital=self.hospital1, patient=patient, encounter_type="IPD", status="OPEN")
        
        diag1 = Diagnosis.objects.create(hospital=self.hospital1, encounter=encounter, icd10_code="A", description="B")
        diag2 = Diagnosis.objects.create(hospital=self.hospital1, encounter=encounter, icd10_code="AA", description="C")
        diag1.superseded_by = diag2
        diag1.save()
        
        res = self.client1.get(f'/api/v1/ehr/patients/{patient.id}/timeline/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        timeline = res.data['timeline']
        diagnoses_in_timeline = [item for item in timeline if item['type'] == 'diagnosis']
        self.assertEqual(len(diagnoses_in_timeline), 1)
        self.assertEqual(diagnoses_in_timeline[0]['data']['icd10_code'], "AA")
        
    def test_capacity_feed_operator(self):
        res = self.operator_client.get('/api/v1/ehr/hospitals/capacity-feed/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['aggregate_metrics']), 2) # Should see both hospitals
        
    def test_capacity_feed_manager(self):
        res = self.client1.get('/api/v1/ehr/hospitals/capacity-feed/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['aggregate_metrics']), 1)
        self.assertEqual(res.data['aggregate_metrics'][0]['hospital_id'], str(self.hospital1.id))
