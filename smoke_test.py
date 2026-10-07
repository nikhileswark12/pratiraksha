import requests
import sys

API_URL = "http://localhost:8000/api/v1"
EMAIL = "hm1@test.com"
PASSWORD = "Password123!"

print(f"Testing with user: {EMAIL}")

# 1. Auth Login
print("\n--- 1. AUTHENTICATION ---")
resp = requests.post(f"{API_URL}/auth/login/", json={
    "email": EMAIL,
    "password": PASSWORD
})
if resp.status_code != 200:
    print("Login failed!", resp.status_code, resp.text)
    sys.exit(1)

token = resp.json().get('access')
headers = {"Authorization": f"Bearer {token}"}
print("Login successful. JWT obtained.")

# 2. Update Hospital Capacity
print("\n--- 2. HOSPITAL UPDATE ---")
resp = requests.get(f"{API_URL}/hospitals/", headers=headers)
print("Hospitals response:", resp.status_code, resp.json())
hospitals = resp.json().get('data', {}).get('hospitals', [])
if not hospitals:
    hospitals = resp.json().get('results', [])
if not hospitals:
    print("No hospitals found.")
    sys.exit(1)

hospital_id = hospitals[0]['id']
print(f"Updating hospital: {hospital_id}")
resp = requests.patch(f"{API_URL}/hospitals/{hospital_id}/", headers=headers, json={
    "total_capacity": 100,
    "current_occupancy": 95  # push to CRITICAL
})
print(f"Update response: {resp.status_code}")
print(resp.json())

# 3. Crisis Simulation
print("\n--- 3. CRISIS SIMULATION ---")
resp = requests.post(f"{API_URL}/crisis/simulate/", headers=headers, json={
    "scenario": "smog_alert",
    "parameters": {
        "severity": "HIGH",
        "radius": 20,
        "aqi": 350
    }
})
print(f"Crisis simulate response: {resp.status_code}")
print(resp.json())

# 4. Predictions
print("\n--- 4. PREDICTIONS ---")
resp = requests.post(f"{API_URL}/predictions/", headers=headers, json={
    "event": "Diwali",
    "pollution_level": 350,
    "temperature": 28,
    "humidity": 65,
    "date": "2026-11-05",
    "city": "Mumbai"
})
print(f"Prediction response: {resp.status_code}")
print(resp.json())
