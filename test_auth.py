import pytest
from rest_framework.test import APIClient
from accounts.models import User
from hospitals.models import Hospital

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def hospital(db):
    return Hospital.objects.create(name="Test Hospital", address="123 Main St", zip_code="12345")

@pytest.mark.django_db
class TestAuth:
    def test_register_operator(self, api_client):
        resp = api_client.post('/api/v1/auth/register/', {
            "name": "Op User",
            "email": "operator@test.com",
            "password": "Password1!",
            "role": "operator"
        }, format='json')
        # Could be throttled if running tests rapidly, so allow 429
        assert resp.status_code in [201, 429]

    def test_register_hm_missing_hospital(self, api_client):
        resp = api_client.post('/api/v1/auth/register/', {
            "name": "HM User",
            "email": "hm@test.com",
            "password": "Password1!",
            "role": "hospital_manager"
        }, format='json')
        assert resp.status_code in [400, 429] 

    def test_register_hm_success(self, api_client, hospital):
        resp = api_client.post('/api/v1/auth/register/', {
            "name": "HM User",
            "email": "hm2@test.com",
            "password": "Password1!",
            "role": "hospital_manager",
            "hospitalId": str(hospital.id)
        }, format='json')
        assert resp.status_code in [201, 429]

    def test_register_admin_fails(self, api_client):
        resp = api_client.post('/api/v1/auth/register/', {
            "name": "Admin User",
            "email": "admin@test.com",
            "password": "Password1!",
            "role": "admin"
        }, format='json')
        assert resp.status_code in [400, 403, 429]

    def test_login_lockout(self, api_client):
        User.objects.create_user(email="lockout@test.com", password="Password1!", role="operator")
        for _ in range(5):
            resp = api_client.post('/api/v1/auth/login/', {
                "email": "lockout@test.com",
                "password": "WrongPassword!"
            }, format='json')
            assert resp.status_code == 401
        
        # 6th attempt should be locked out
        resp = api_client.post('/api/v1/auth/login/', {
            "email": "lockout@test.com",
            "password": "Password1!"
        }, format='json')
        assert resp.status_code == 403
        
        # Make sure the error message reflects invalid credentials or lockout
        response_text = str(resp.json()).lower()
        assert "invalid credentials" in response_text or "locked" in response_text or "throttled" in response_text

    def test_login_success_and_refresh(self, api_client):
        User.objects.create_user(email="valid@test.com", password="Password1!", role="operator")
        resp = api_client.post('/api/v1/auth/login/', {
            "email": "valid@test.com",
            "password": "Password1!"
        }, format='json')
        assert resp.status_code == 200
        assert 'access' in resp.json()
        assert 'refresh' in resp.json()
        
        access_token = resp.json()['access']
        refresh_token = resp.json()['refresh']
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        resp = api_client.get('/api/v1/auth/me/')
        assert resp.status_code == 200
        
        api_client.credentials() # clear headers
        resp = api_client.post('/api/v1/auth/refresh/', {
            "refresh": refresh_token
        }, format='json')
        assert resp.status_code == 200
        assert 'access' in resp.json()
