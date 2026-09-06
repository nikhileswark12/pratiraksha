import pytest
from rest_framework.test import APIClient
from accounts.models import User
from hospitals.models import Hospital, Department, Equipment

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def setup_data(db):
    from hospitals.models import Tenant
    t = Tenant.objects.create(name="Test Tenant")
    h1 = Hospital.objects.create(name="Hospital 1", address="123", zip_code="111", tenant=t)
    h2 = Hospital.objects.create(name="Hospital 2", address="456", zip_code="222", tenant=t)
    Department.objects.create(hospital=h1, name="Cardiology")
    op = User.objects.create_user(email="op@test.com", password="Password1!", role="operator", tenant=t)
    hm1 = User.objects.create_user(email="hm1@test.com", password="Password1!", role="hospital_manager", hospital=h1)
    hm2 = User.objects.create_user(email="hm2@test.com", password="Password1!", role="hospital_manager", hospital=h2)
    return h1, h2, op, hm1, hm2

def get_token(client, email):
    resp = client.post('/api/v1/auth/login/', {"email": email, "password": "Password1!"}, format="json")
    return resp.json()['access']

@pytest.mark.django_db
class TestHospitals:
    def test_operator_read_only(self, api_client, setup_data):
        h1, h2, op, hm1, hm2 = setup_data
        token = get_token(api_client, op.email)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # GET
        assert api_client.get('/api/v1/hospitals/').status_code == 200
        assert api_client.get(f'/api/v1/hospitals/{h1.id}/').status_code == 200
        
        # PUT should fail
        assert api_client.put(f'/api/v1/hospitals/{h1.id}/', {"name": "Hacked"}, format="json").status_code == 403

    def test_hospital_manager_scope(self, api_client, setup_data):
        h1, h2, op, hm1, hm2 = setup_data
        token = get_token(api_client, hm1.email)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # GET list
        assert api_client.get('/api/v1/hospitals/').status_code == 200
        
        # PATCH own hospital
        assert api_client.patch(f'/api/v1/hospitals/{h1.id}/', {"name": "H1 Updated"}, format="json").status_code == 200
        
        # PATCH other hospital
        assert api_client.patch(f'/api/v1/hospitals/{h2.id}/', {"name": "Hacked"}, format="json").status_code == 404

    def test_missing_methods(self, api_client, setup_data):
        h1, h2, op, hm1, hm2 = setup_data
        token = get_token(api_client, hm1.email)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        assert api_client.post('/api/v1/hospitals/', {"name": "New"}, format="json").status_code == 405
        assert api_client.delete(f'/api/v1/hospitals/{h1.id}/').status_code == 405

    def test_extra_endpoints(self, api_client, setup_data):
        h1, h2, op, hm1, hm2 = setup_data
        token = get_token(api_client, op.email)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        assert api_client.get(f'/api/v1/hospitals/{h1.id}/departments/').status_code == 200
        assert api_client.get(f'/api/v1/hospitals/{h1.id}/equipment/').status_code == 200
        assert api_client.get(f'/api/v1/hospitals/{h1.id}/occupancy-trend/').status_code == 200
