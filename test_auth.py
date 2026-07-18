import os
import django
from django.test import Client
import json
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratiraksha.settings.dev')
django.setup()

from hospitals.models import Hospital
from accounts.models import User

# Clean up previous data
User.objects.all().delete()
Hospital.objects.all().delete()

# Create a test hospital
hospital = Hospital.objects.create(name="Test Hospital", address="123 Main St", zip_code="12345")

client = Client()

print("--- Testing Registration ---")
# 1. Register Operator
resp = client.post('/api/v1/auth/register/', {
    "name": "Op User",
    "email": "operator@test.com",
    "password": "Password1!",
    "role": "operator"
}, content_type="application/json")
print(f"Register Operator: {resp.status_code} - {resp.json().keys() if resp.status_code == 201 else resp.json()}")

# 2. Register Hospital Manager (missing hospital_id)
resp = client.post('/api/v1/auth/register/', {
    "name": "HM User",
    "email": "hm@test.com",
    "password": "Password1!",
    "role": "hospital_manager"
}, content_type="application/json")
print(f"Register HM (missing hospitalId): {resp.status_code} - {resp.json()}")

# 3. Register Hospital Manager (success)
resp = client.post('/api/v1/auth/register/', {
    "name": "HM User",
    "email": "hm@test.com",
    "password": "Password1!",
    "role": "hospital_manager",
    "hospitalId": str(hospital.id)
}, content_type="application/json")
print(f"Register HM (success): {resp.status_code} - {resp.json().keys() if resp.status_code == 201 else resp.json()}")

# 4. Register Admin (should fail)
resp = client.post('/api/v1/auth/register/', {
    "name": "Admin User",
    "email": "admin@test.com",
    "password": "Password1!",
    "role": "admin"
}, content_type="application/json")
print(f"Register Admin: {resp.status_code} - {resp.json()}")


print("\n--- Testing Login & Lockout ---")
# 1. Failed logins -> Lockout
for i in range(5):
    resp = client.post('/api/v1/auth/login/', {
        "email": "operator@test.com",
        "password": "WrongPassword!"
    }, content_type="application/json")
    print(f"Failed Login {i+1}: {resp.status_code} - {resp.json()}")

# 6th attempt should hit lockout
resp = client.post('/api/v1/auth/login/', {
    "email": "operator@test.com",
    "password": "Password1!"
}, content_type="application/json")
print(f"Login during lockout: {resp.status_code} - {resp.json()}")

# Fix lockout for testing
u = User.objects.get(email="operator@test.com")
u.account_locked_until = None
u.failed_login_attempts = 0
u.save()

# 2. Successful Login
resp = client.post('/api/v1/auth/login/', {
    "email": "operator@test.com",
    "password": "Password1!"
}, content_type="application/json")
print(f"Successful Login: {resp.status_code} - {resp.json().keys() if resp.status_code == 200 else resp.json()}")
access_token = resp.json()['access']
refresh_token = resp.json()['refresh']


print("\n--- Testing /me Endpoint ---")
resp = client.get('/api/v1/auth/me/', HTTP_AUTHORIZATION=f"Bearer {access_token}")
print(f"Me Endpoint: {resp.status_code} - {resp.json()}")


print("\n--- Testing Refresh ---")
resp = client.post('/api/v1/auth/refresh/', {
    "refresh": refresh_token
}, content_type="application/json")
print(f"Refresh Token: {resp.status_code} - {resp.json().keys() if resp.status_code == 200 else resp.json()}")
