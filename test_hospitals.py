import os
import django
from django.test import Client

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratiraksha.settings.dev')
django.setup()

from hospitals.models import Hospital, Department, Equipment
from accounts.models import User

# Clean up previous data
User.objects.all().delete()
Hospital.objects.all().delete()

# Setup test data
h1 = Hospital.objects.create(name="Hospital 1", address="123", zip_code="111")
h2 = Hospital.objects.create(name="Hospital 2", address="456", zip_code="222")

d1 = Department.objects.create(hospital=h1, name="Cardiology")
e1 = Equipment.objects.create(hospital=h1, department=d1, name="ECG", equipment_type="Monitor")

op_user = User.objects.create_user(email="op@test.com", password="Password1!", name="Op", role="operator")
hm_user1 = User.objects.create_user(email="hm1@test.com", password="Password1!", name="HM1", role="hospital_manager", hospital_id=h1.id)
hm_user2 = User.objects.create_user(email="hm2@test.com", password="Password1!", name="HM2", role="hospital_manager", hospital_id=h2.id)

# Login and get tokens
def get_token(email):
    c = Client()
    resp = c.post('/api/v1/auth/login/', {"email": email, "password": "Password1!"}, content_type="application/json")
    return resp.json()['access']

op_token = get_token("op@test.com")
hm1_token = get_token("hm1@test.com")
hm2_token = get_token("hm2@test.com")

def test_endpoint(client, method, url, token, data=None, expected_status=None):
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    if method == "GET":
        resp = client.get(url, **headers)
    elif method == "PUT":
        resp = client.put(url, data, content_type="application/json", **headers)
    elif method == "PATCH":
        resp = client.patch(url, data, content_type="application/json", **headers)
    elif method == "POST":
        resp = client.post(url, data, content_type="application/json", **headers)
    elif method == "DELETE":
        resp = client.delete(url, **headers)
    
    status_match = "PASS" if not expected_status or resp.status_code == expected_status else f"FAIL (Got {resp.status_code})"
    print(f"{method} {url} -> {resp.status_code} [{status_match}]")
    return resp

c = Client()

print("--- 1. Testing Operator Read-Only Access ---")
test_endpoint(c, "GET", "/api/v1/hospitals/", op_token, expected_status=200)
test_endpoint(c, "GET", f"/api/v1/hospitals/{h1.id}/", op_token, expected_status=200)
test_endpoint(c, "PUT", f"/api/v1/hospitals/{h1.id}/", op_token, {"name": "Hacked"}, expected_status=403)

print("\n--- 2. Testing Hospital Manager Scope ---")
# HM1 (owns H1)
test_endpoint(c, "GET", "/api/v1/hospitals/", hm1_token, expected_status=200) # Can read all list
test_endpoint(c, "PATCH", f"/api/v1/hospitals/{h1.id}/", hm1_token, {"name": "H1 Updated"}, expected_status=200) # Can update own
test_endpoint(c, "PATCH", f"/api/v1/hospitals/{h2.id}/", hm1_token, {"name": "Hacked"}, expected_status=403) # Cannot update others

print("\n--- 3. Testing POST/DELETE Missing ---")
test_endpoint(c, "POST", "/api/v1/hospitals/", hm1_token, {"name": "New"}, expected_status=405)
test_endpoint(c, "DELETE", f"/api/v1/hospitals/{h1.id}/", hm1_token, expected_status=405)

print("\n--- 4. Testing Extra Endpoints ---")
test_endpoint(c, "GET", f"/api/v1/hospitals/{h1.id}/departments/", op_token, expected_status=200)
test_endpoint(c, "GET", f"/api/v1/hospitals/{h1.id}/equipment/", op_token, expected_status=200)
resp = test_endpoint(c, "GET", f"/api/v1/hospitals/{h1.id}/occupancy-trend/", op_token, expected_status=200)
print(f"Occupancy Output: {resp.json()}")
