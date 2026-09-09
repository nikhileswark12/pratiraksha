import uuid
import datetime
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.conf import settings
from pratiraksha.utils import get_mongo_db, log_activity
from integrations.tasks import dispatch_webhook_event

class CrisisSimulationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        scenario = request.data.get('scenario')
        parameters = request.data.get('parameters', {})
        
        # Access control
        # Hospital manager can only simulate their own hospital, operator can simulate whole network
        requested_hospital_ids = request.data.get('hospital_ids', [])
        affected_hospitals = []
        
        if user.role == 'hospital_manager':
            if not user.hospital_id:
                return Response({"error": "Manager has no assigned hospital."}, status=status.HTTP_400_BAD_REQUEST)
            if requested_hospital_ids and any(hid != str(user.hospital_id) for hid in requested_hospital_ids):
                return Response({"error": "One or more requested hospitals not found."}, status=status.HTTP_404_NOT_FOUND)
            affected_hospitals = [str(user.hospital_id)]
        elif user.role == 'operator':
            if requested_hospital_ids:
                affected_hospitals = requested_hospital_ids
            else:
                affected_hospitals = ["all_network"]
        else:
            return Response({"error": "Unauthorized role for simulation."}, status=status.HTTP_403_FORBIDDEN)
            
        if not scenario:
            return Response({"error": "Scenario type is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Simulation logic (heuristic)
        estimated_patient_surge = 0
        department_breakdown = {}
        recommended_actions = []
        resource_reallocation = []

        if scenario == 'smog_alert':
            aqi = float(parameters.get('aqi', 100))
            radius = float(parameters.get('radius', 10))
            
            surge_base = 20 if aqi > 300 else (10 if aqi > 150 else 0)
            estimated_patient_surge = int(surge_base * (radius / 10.0))
            department_breakdown = {"Pulmonology": 60, "ER": 30, "Pediatrics": 10}
            recommended_actions = [
                "Stock up on oxygen cylinders",
                "Alert Pulmonologists on call",
                "Prepare nebulizers in ER"
            ]
            resource_reallocation = [{"from": "General Ward", "to": "ER", "item": "Staff Nurses", "count": 2}]
            
        elif scenario == 'heatwave':
            temperature = float(parameters.get('temperature', 35))
            duration_days = int(parameters.get('duration', 1))
            humidity = float(parameters.get('humidity', 50))
            
            heat_index = temperature + (humidity * 0.1)
            surge_base = 30 if heat_index > 45 else (15 if heat_index > 40 else 0)
            estimated_patient_surge = int(surge_base * duration_days)
            department_breakdown = {"ER": 70, "Internal Medicine": 20, "Geriatrics": 10}
            recommended_actions = [
                "Ensure ACs in all wards are functional",
                "Stock IV fluids",
                "Setup triage for heat stroke"
            ]
            resource_reallocation = [{"from": "Surgery", "to": "ER", "item": "IV Stands", "count": 10}]
            
        elif scenario == 'mass_gathering':
            event_size = int(parameters.get('event_size', 1000))
            duration_hours = int(parameters.get('duration', 5))
            
            estimated_patient_surge = int((event_size / 1000) * 5 * (duration_hours / 5))
            department_breakdown = {"ER": 50, "Trauma": 40, "General": 10}
            recommended_actions = [
                "Clear ER beds",
                "Cancel elective surgeries",
                "Recall trauma surgeons"
            ]
            resource_reallocation = [{"from": "General Ward", "to": "Trauma", "item": "Beds", "count": int(estimated_patient_surge * 0.1)}]
            
        else:
            return Response({"error": "Unsupported scenario."}, status=status.HTTP_400_BAD_REQUEST)

        # Construct response
        simulation_id = str(uuid.uuid4())
        response_data = {
            "simulation_id": simulation_id,
            "scenario": scenario,
            "impact_assessment": {
                "affected_hospitals": affected_hospitals,
                "estimated_patient_surge": estimated_patient_surge,
                "department_breakdown": department_breakdown
            },
            "response_plan": {
                "recommended_actions": recommended_actions,
                "resource_reallocation_suggestions": resource_reallocation
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        # Log to MongoDB
        import logging
        logger = logging.getLogger(__name__)
        
        db = get_mongo_db()
        if db is not None:
            try:
                log_doc = {
                    **response_data,
                    "parameters": parameters,
                    "user_id": str(user.id),
                    "role": user.role
                }
                log_doc['timestamp'] = datetime.datetime.utcnow()
                db.crisis_simulation.insert_one(log_doc)
                response_data["logged"] = True
            except Exception as e:
                logger.error(f"Failed to log simulation to MongoDB: {e}")
                response_data["logged"] = False
        else:
            logger.error("Analytics database unavailable. Failed to log simulation to MongoDB.")
            response_data["logged"] = False

        log_activity(
            actor=str(user.id),
            action="crisis simulation run",
            resource_type="simulation",
            resource_id=simulation_id,
            extra_data={"scenario": scenario, "logged": response_data.get("logged", False)}
        )
        
        # Dispatch webhook for crisis simulation
        dispatch_webhook_event.delay(
            event_type='crisis.alert_created',
            payload=response_data
        )

        return Response(response_data, status=status.HTTP_200_OK)
