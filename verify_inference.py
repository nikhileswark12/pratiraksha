import requests

try:
    resp = requests.post("http://localhost:8001/predict", json={
        "event": "None",
        "pollution_level": 50,
        "temperature": 35.0,
        "humidity": 60.0,
        "date": "2023-01-01",
        "city": "Mumbai",
        "day_of_week": 6,
        "month": 1
    })
    print("Status:", resp.status_code)
    print("Response:", resp.json())
except Exception as e:
    print("Error:", e)
