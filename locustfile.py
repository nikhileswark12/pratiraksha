from locust import HttpUser, task, between
import random

class PratirakshaUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Simulate login for 200 concurrent hospitals (simulated by random accounts)"""
        # We assume operator or hospital manager
        response = self.client.post("/api/v1/auth/login/", json={
            "email": "operator@example.com",
            "password": "Password123!"
        })
        if response.status_code == 200:
            token = response.json().get('access')
            if token:
                self.client.headers.update({"Authorization": f"Bearer {token}"})
        
    @task(3)
    def view_capacity_feed(self):
        self.client.get("/api/v1/ehr/hospitals/capacity-feed/")
        
    @task(2)
    def view_dashboard(self):
        self.client.get("/api/v1/analytics/overview/")
        self.client.get("/api/v1/analytics/trends/")
        
    @task(1)
    def list_hospitals(self):
        self.client.get("/api/v1/hospitals/")
