import datetime
import logging
import uuid

from rest_framework import permissions, status, views
from rest_framework.response import Response

from hospitals.models import Hospital
from integrations.tasks import dispatch_webhook_event
from notifications.tasks import process_crisis_notification
from pratiraksha.utils import get_mongo_db, log_activity
from .serializers import CrisisSimulationRequestSerializer

logger = logging.getLogger(__name__)


class CrisisSimulationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CrisisSimulationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        data = serializer.validated_data
        scenario = data["scenario"]
        parameters = data["parameters"]
        requested_hospital_ids = [str(value) for value in data["hospital_ids"]]

        if user.role == "hospital_manager":
            if not user.hospital_id:
                return Response({"error": "Manager has no assigned hospital."}, status=status.HTTP_400_BAD_REQUEST)
            own_hospital_id = str(user.hospital_id)
            if requested_hospital_ids and requested_hospital_ids != [own_hospital_id]:
                return Response({"error": "One or more requested hospitals not found."}, status=status.HTTP_404_NOT_FOUND)
            affected_hospitals = [own_hospital_id]
        elif user.role == "operator":
            if not user.tenant_id:
                return Response({"error": "Operator has no assigned tenant."}, status=status.HTTP_403_FORBIDDEN)
            allowed_ids = [
                str(hospital_id) for hospital_id in Hospital.objects.filter(
                    tenant_id=user.tenant_id
                ).values_list("id", flat=True)
            ]
            if requested_hospital_ids and any(hospital_id not in set(allowed_ids) for hospital_id in requested_hospital_ids):
                return Response({"error": "One or more requested hospitals not found."}, status=status.HTTP_404_NOT_FOUND)
            affected_hospitals = requested_hospital_ids or allowed_ids
        else:
            return Response({"error": "Unauthorized role for simulation."}, status=status.HTTP_403_FORBIDDEN)

        if scenario == "smog_alert":
            aqi = parameters["aqi"]
            radius = parameters["radius"]
            surge_base = 20 if aqi > 300 else 10 if aqi > 150 else 0
            estimated_patient_surge = int(surge_base * (radius / 10.0))
            department_breakdown = {"Pulmonology": 60, "ER": 30, "Pediatrics": 10}
            recommended_actions = [
                "Stock up on oxygen cylinders",
                "Alert Pulmonologists on call",
                "Prepare nebulizers in ER",
            ]
            resource_reallocation = [{"from": "General Ward", "to": "ER", "item": "Staff Nurses", "count": 2}]
        elif scenario == "heatwave":
            temperature = parameters["temperature"]
            duration_days = parameters["duration"]
            humidity = parameters["humidity"]
            heat_index = temperature + humidity * 0.1
            surge_base = 30 if heat_index > 45 else 15 if heat_index > 40 else 0
            estimated_patient_surge = int(surge_base * duration_days)
            department_breakdown = {"ER": 70, "Internal Medicine": 20, "Geriatrics": 10}
            recommended_actions = [
                "Ensure ACs in all wards are functional",
                "Stock IV fluids",
                "Setup triage for heat stroke",
            ]
            resource_reallocation = [{"from": "Surgery", "to": "ER", "item": "IV Stands", "count": 10}]
        else:
            event_size = parameters["event_size"]
            duration_hours = parameters["duration"]
            estimated_patient_surge = int((event_size / 1000) * duration_hours)
            department_breakdown = {"ER": 50, "Trauma": 40, "General": 10}
            recommended_actions = [
                "Clear ER beds",
                "Cancel elective surgeries",
                "Recall trauma surgeons",
            ]
            resource_reallocation = [{
                "from": "General Ward",
                "to": "Trauma",
                "item": "Beds",
                "count": int(estimated_patient_surge * 0.1),
            }]

        simulation_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.timezone.utc)
        response_data = {
            "simulation_id": simulation_id,
            "scenario": scenario,
            "simulation_source": "rule_based_interim",
            "impact_assessment": {
                "affected_hospitals": affected_hospitals,
                "estimated_patient_surge": estimated_patient_surge,
                "department_breakdown": department_breakdown,
            },
            "response_plan": {
                "recommended_actions": recommended_actions,
                "resource_reallocation_suggestions": resource_reallocation,
            },
            "timestamp": created_at.isoformat(),
        }

        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Simulation was not run because the audit database is unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        log_doc = {
            **response_data,
            "parameters": parameters,
            "user_id": str(user.id),
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "created_at": created_at,
        }
        try:
            db.crisis_simulation.insert_one(log_doc)
        except Exception:
            logger.exception("Failed to persist crisis simulation %s", simulation_id)
            return Response(
                {"error": "Simulation could not be persisted. Please retry after the audit database recovers."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        log_activity(
            actor=str(user.id),
            action="crisis simulation run",
            resource_type="simulation",
            resource_id=simulation_id,
            extra_data={"scenario": scenario, "simulation_source": "rule_based_interim"},
        )

        tenant_id = user.tenant_id
        if tenant_id is None and user.hospital_id:
            tenant_id = Hospital.objects.filter(pk=user.hospital_id).values_list("tenant_id", flat=True).first()
        tenant_id = str(tenant_id) if tenant_id else None
        dispatch_status = {"webhook": "queued", "notification": "queued"}
        try:
            dispatch_webhook_event.delay(
                event_type="crisis.alert_created",
                payload=response_data,
                hospital_id=affected_hospitals[0] if len(affected_hospitals) == 1 else None,
                tenant_id=tenant_id,
            )
        except Exception:
            logger.exception("Failed to enqueue crisis webhook for %s", simulation_id)
            dispatch_status["webhook"] = "queue_failed"
        try:
            process_crisis_notification.delay(
                affected_hospitals,
                scenario,
                estimated_patient_surge,
                tenant_id,
            )
        except Exception:
            logger.exception("Failed to enqueue crisis notification for %s", simulation_id)
            dispatch_status["notification"] = "queue_failed"

        response_data["dispatch_status"] = dispatch_status
        return Response(response_data, status=status.HTTP_201_CREATED)
