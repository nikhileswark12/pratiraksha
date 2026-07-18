import os
import django
import asyncio
import json
from channels.testing import WebsocketCommunicator
from django.test import Client

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratiraksha.settings.dev')
django.setup()

from pratiraksha.asgi import application
from hospitals.models import Hospital
from accounts.models import User

def setup_db():
    User.objects.all().delete()
    Hospital.objects.all().delete()
    
    h1 = Hospital.objects.create(name="Hospital 1", address="123", zip_code="111")
    h2 = Hospital.objects.create(name="Hospital 2", address="456", zip_code="222")
    
    op_user = User.objects.create_user(email="op@test.com", password="Password1!", name="Op", role="operator")
    hm1_user = User.objects.create_user(email="hm1@test.com", password="Password1!", name="HM1", role="hospital_manager", hospital_id=h1.id)
    hm2_user = User.objects.create_user(email="hm2@test.com", password="Password1!", name="HM2", role="hospital_manager", hospital_id=h2.id)
    return h1, h2

async def run_ws_tests():
    print("--- Setting up test data ---")
    
    from asgiref.sync import sync_to_async
    h1, h2 = await sync_to_async(setup_db)()

    @sync_to_async
    def get_token(email):
        c = Client()
        resp = c.post('/api/v1/auth/login/', {"email": email, "password": "Password1!"}, content_type="application/json")
        return resp.json()['access']

    op_token = await get_token("op@test.com")
    hm1_token = await get_token("hm1@test.com")
    hm2_token = await get_token("hm2@test.com")

    print("\n--- Testing Connections ---")
    # 1. No token (should disconnect)
    comm_invalid = WebsocketCommunicator(application, "/ws/hospitals/")
    connected, subprotocol = await comm_invalid.connect()
    print(f"No token connected: {connected} [EXPECTED: False]")

    # 2. Operator Connection
    comm_op = WebsocketCommunicator(application, f"/ws/hospitals/?token={op_token}")
    connected_op, _ = await comm_op.connect()
    print(f"Operator connected: {connected_op} [EXPECTED: True]")

    # 3. HM1 Connection (owns H1)
    comm_hm1 = WebsocketCommunicator(application, f"/ws/hospitals/?token={hm1_token}")
    connected_hm1, _ = await comm_hm1.connect()
    print(f"HM1 connected: {connected_hm1} [EXPECTED: True]")

    # 4. HM2 Connection (owns H2)
    comm_hm2 = WebsocketCommunicator(application, f"/ws/hospitals/?token={hm2_token}")
    connected_hm2, _ = await comm_hm2.connect()
    print(f"HM2 connected: {connected_hm2} [EXPECTED: True]")


    print("\n--- Testing Events ---")
    # Trigger an update on H1 via API
    @sync_to_async
    def trigger_h1_critical():
        c = Client()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {hm1_token}"}
        resp = c.patch(f'/api/v1/hospitals/{h1.id}/', {"status": "CRITICAL", "current_occupancy": 95}, content_type="application/json", **headers)
        return resp.status_code

    status_code = await trigger_h1_critical()
    print(f"H1 PATCH API response: {status_code}")

    # The signal will be fired. Let's receive from OP
    op_response_1 = await comm_op.receive_json_from(timeout=2)
    print(f"Operator received: {op_response_1}")
    op_response_2 = await comm_op.receive_json_from(timeout=2)
    print(f"Operator received: {op_response_2}")
    
    # HM1 should receive
    hm1_response_1 = await comm_hm1.receive_json_from(timeout=2)
    print(f"HM1 received: {hm1_response_1}")
    hm1_response_2 = await comm_hm1.receive_json_from(timeout=2)
    print(f"HM1 received: {hm1_response_2}")

    # HM2 should NOT receive anything
    try:
        hm2_response = await comm_hm2.receive_json_from(timeout=1)
        print(f"HM2 received: {hm2_response} [FAILED - SHOULD BE EMPTY]")
    except asyncio.TimeoutError:
        print("HM2 received nothing [PASS]")


    # Disconnect
    await comm_op.disconnect()
    await comm_hm1.disconnect()
    await comm_hm2.disconnect()
    
if __name__ == "__main__":
    asyncio.run(run_ws_tests())
