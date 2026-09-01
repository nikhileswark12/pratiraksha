from locust import HttpUser, task, between

class PratirakshaUser_1K(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post("/api/v1/auth/login/", json={
            "email": "operator@example.com",
            "password": "Password123!"
        })
        if response.status_code == 200:
            token = response.json().get('access')
            if token:
                self.client.headers.update({"Authorization": f"Bearer {token}"})
    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/hospitals/", name="/hospitals (Dashboard view)")

    @task(1)
    def view_hospital_detail(self):
        # We assume a valid hospital ID exists. If not, it will 404 which still tests stack throughput.
        self.client.get("/api/v1/hospitals/cc5c4696-4de0-44ee-8a0f-ecfe169cb286/", name="/hospitals/{id} (Detail)")
