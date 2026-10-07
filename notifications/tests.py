import pytest
from rest_framework.test import APIClient
from accounts.models import User
from hospitals.models import Tenant, Hospital
from notifications.models import InAppNotification

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestInAppNotificationAPI:
    def setup_method(self):
        self.tenant1 = Tenant.objects.create(name="Tenant 1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2")
        
        self.h1 = Hospital.objects.create(name="H1", tenant=self.tenant1, status="NORMAL")
        self.h2 = Hospital.objects.create(name="H2", tenant=self.tenant1, status="NORMAL")
        self.h3 = Hospital.objects.create(name="H3", tenant=self.tenant2, status="NORMAL")

        self.op1 = User.objects.create_user(email="op1@test.com", password="pwd", role="operator", tenant=self.tenant1)
        self.hm1 = User.objects.create_user(email="hm1@test.com", password="pwd", role="hospital_manager", hospital=self.h1)
        self.hm2 = User.objects.create_user(email="hm2@test.com", password="pwd", role="hospital_manager", hospital=self.h2)
        
        self.n1 = InAppNotification.objects.create(hospital_id=self.h1.id, title="N1", severity="INFO")
        self.n2 = InAppNotification.objects.create(hospital_id=self.h2.id, title="N2", severity="INFO")
        self.n3 = InAppNotification.objects.create(hospital_id=self.h3.id, title="N3", severity="INFO")
        self.n_tenant = InAppNotification.objects.create(tenant_id=self.tenant1.id, title="NT1", severity="INFO")

    def test_manager_sees_only_own_hospital(self, api_client):
        api_client.force_authenticate(user=self.hm1)
        response = api_client.get('/api/v1/notifications/')
        assert response.status_code == 200
        titles = [n['title'] for n in response.json().get('results', response.json())]
        assert 'N1' in titles
        assert 'N2' not in titles
        assert 'N3' not in titles

    def test_operator_sees_tenant_hospitals(self, api_client):
        api_client.force_authenticate(user=self.op1)
        response = api_client.get('/api/v1/notifications/')
        assert response.status_code == 200
        titles = [n['title'] for n in response.json().get('results', response.json())]
        assert 'N1' in titles
        assert 'N2' in titles
        assert 'NT1' in titles
        assert 'N3' not in titles

    def test_mark_read_success(self, api_client):
        api_client.force_authenticate(user=self.hm1)
        response = api_client.patch(f'/api/v1/notifications/{self.n1.id}/read/')
        assert response.status_code == 200
        self.n1.refresh_from_db()
        assert self.n1.is_read is True

    def test_mark_read_out_of_scope_404(self, api_client):
        api_client.force_authenticate(user=self.hm1)
        response = api_client.patch(f'/api/v1/notifications/{self.n2.id}/read/')
        assert response.status_code == 404
        self.n2.refresh_from_db()
        assert self.n2.is_read is False

    def test_mark_all_read(self, api_client):
        api_client.force_authenticate(user=self.op1)
        response = api_client.post('/api/v1/notifications/mark-all-read/')
        assert response.status_code == 200
        self.n1.refresh_from_db()
        self.n2.refresh_from_db()
        self.n_tenant.refresh_from_db()
        assert self.n1.is_read is True
        assert self.n2.is_read is True
        assert self.n_tenant.is_read is True
        
        self.n3.refresh_from_db()
        assert self.n3.is_read is False # Not in their scope
