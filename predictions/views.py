import datetime
import logging
import os
import uuid

import requests
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from hospitals.models import Hospital
from pratiraksha.utils import get_mongo_db, log_activity
from .serializers import PredictionRequestSerializer

logger = logging.getLogger(__name__)


class PredictionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        serializer = PredictionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        hospital_id = data.get("hospital_id")
        hospital = None
        if hospital_id is None:
            if request.user.role != "operator":
                return Response(
                    {"error": "Only operators can request network-wide predictions."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not request.user.tenant_id:
                return Response({"error": "Operator has no assigned tenant."}, status=status.HTTP_403_FORBIDDEN)
        else:
            try:
                hospital = Hospital.objects.get(pk=hospital_id)
            except Hospital.DoesNotExist:
                return Response({"error": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

            if request.user.role == "hospital_manager":
                allowed = str(hospital.id) == str(request.user.hospital_id)
            elif request.user.role == "operator":
                allowed = bool(request.user.tenant_id) and str(hospital.tenant_id) == str(request.user.tenant_id)
            else:
                allowed = False
            if not allowed:
                return Response({"error": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

        target_date = data["date"]
        prediction_id = str(uuid.uuid4())
        event = data["event"]
        pollution_level = data["pollution_level"]
        temperature = data["temperature"]
        humidity = data["humidity"]
        rainfall = data["rainfall"]

        response_data = None
        inference_reason = None
        has_real_admissions = (
            "prev_day_admissions" in data and "weekly_avg_admissions" in data
        )
        if hospital is not None and has_real_admissions:
            ml_payload = {
                "event": event,
                "pollution_level": pollution_level,
                "temperature": temperature,
                "humidity": humidity,
                "rainfall": rainfall,
                "prev_day_admissions": data["prev_day_admissions"],
                "weekly_avg_admissions": data["weekly_avg_admissions"],
                "date": target_date.isoformat(),
                "city": data["city"],
                "day_of_week": target_date.weekday(),
                "month": target_date.month,
            }
            ml_url = os.environ.get("ML_SERVICE_URL", "http://ml_service:8001/predict")
            try:
                ml_response = requests.post(ml_url, json=ml_payload, timeout=5)
                ml_response.raise_for_status()
                ml_data = ml_response.json()
                if not isinstance(ml_data, dict):
                    raise ValueError("Model response must be a JSON object.")
                predicted_surge = ml_data.get("predicted_surge")
                risk_level = ml_data.get("risk_level")
                if (
                    isinstance(predicted_surge, bool)
                    or not isinstance(predicted_surge, (int, float))
                    or not 0 <= predicted_surge <= 100
                    or risk_level not in ("LOW", "MEDIUM", "HIGH")
                ):
                    raise ValueError("Model response contains invalid risk fields.")
                model_confidence = ml_data.get("confidence")
                if model_confidence is not None and (
                    isinstance(model_confidence, bool)
                    or not isinstance(model_confidence, (int, float))
                    or not 0 <= model_confidence <= 100
                ):
                    raise ValueError("Model confidence must be between 0 and 100.")
                response_data = {
                    "id": prediction_id,
                    "risk_level": risk_level,
                    "risk_score": predicted_surge,
                    "predicted_surge": predicted_surge,
                    "affected_departments": ["ER"],
                    "recommended_actions": [
                        "Alert on-call staff" if risk_level == "HIGH" else "Monitor situation"
                    ],
                    "resource_requirements": {"beds": int(predicted_surge / 10) + 5},
                    "timeline": target_date.isoformat(),
                    "model_version": str(ml_data.get("model_version", "unspecified")),
                    "prediction_source": "ml_service",
                }
                if model_confidence is not None:
                    response_data["confidence"] = model_confidence
            except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
                inference_reason = "Model inference unavailable or returned an invalid response."
                logger.warning("%s Detail: %s", inference_reason, exc)
        elif hospital is None:
            inference_reason = "Network-wide model inference is not configured."
        else:
            inference_reason = "Actual admission history was not supplied; fabricated occupancy proxies are not used."

        if response_data is None:
            surge = 0
            if pollution_level > 150:
                surge += 30
            elif pollution_level > 100:
                surge += 15
            if temperature > 40 or temperature < 5:
                surge += 25
            elif temperature > 35 or temperature < 10:
                surge += 10
            if humidity > 80:
                surge += 10
            if event.strip() and event.lower() not in ("none", "null"):
                surge += 20

            predicted_surge = min(surge, 100)
            risk_level = "HIGH" if predicted_surge >= 60 else "MEDIUM" if predicted_surge >= 30 else "LOW"
            response_data = {
                "id": prediction_id,
                "risk_level": risk_level,
                "risk_score": predicted_surge,
                "predicted_surge": predicted_surge,
                "affected_departments": ["ER", "Pulmonology"] if pollution_level > 100 else ["ER"],
                "recommended_actions": [
                    "Alert on-call staff" if risk_level == "HIGH" else "Monitor situation",
                    "Check equipment inventory",
                ],
                "resource_requirements": {
                    "beds": int(predicted_surge / 10) + 5,
                    "ventilators": 5 if pollution_level > 100 else 0,
                },
                "timeline": target_date.isoformat(),
                "model_version": "rule-based-interim-0.2",
                "prediction_source": "rule_based_interim",
                "confidence": None,
                "inference_note": inference_reason,
            }

        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Prediction could not be persisted because the audit database is unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        log_doc = {
            **response_data,
            "input_data": {
                key: value.isoformat() if hasattr(value, "isoformat") else str(value) if key == "hospital_id" else value
                for key, value in data.items()
            },
            "user_id": str(request.user.id),
            "tenant_id": str(request.user.tenant_id) if request.user.tenant_id else None,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        }
        try:
            db.predictions.insert_one(log_doc)
        except Exception:
            logger.exception("Failed to persist prediction %s", prediction_id)
            return Response(
                {"error": "Prediction could not be persisted. Please retry after the audit database recovers."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        log_activity(
            actor=str(request.user.id),
            action="prediction created",
            resource_type="prediction",
            resource_id=prediction_id,
            extra_data={
                "risk_level": response_data["risk_level"],
                "predicted_surge": response_data["predicted_surge"],
                "prediction_source": response_data["prediction_source"],
            },
        )
        return Response(response_data, status=status.HTTP_201_CREATED)

    def list(self, request):
        db = get_mongo_db()
        if db is None:
            return Response(
                {"error": "Prediction history is unavailable because the audit database is unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            if request.user.role == "hospital_manager":
                if not request.user.hospital_id:
                    return Response({"results": []})
                allowed_ids = [str(request.user.hospital_id)]
                scope_query = {"input_data.hospital_id": {"$in": allowed_ids}}
            elif request.user.role == "operator" and request.user.tenant_id:
                allowed_ids = [
                    str(hid) for hid in Hospital.objects.filter(
                        tenant_id=request.user.tenant_id
                    ).values_list("id", flat=True)
                ]
                scope_query = {"$or": [
                    {"tenant_id": str(request.user.tenant_id)},
                    {"input_data.hospital_id": {"$in": allowed_ids}},
                ]}
            else:
                return Response({"results": []})
            cursor = db.predictions.find(scope_query).sort("created_at", -1).limit(50)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                if hasattr(doc.get("created_at"), "isoformat"):
                    doc["created_at"] = doc["created_at"].isoformat()
                results.append(doc)
            return Response({"results": results})
        except Exception:
            logger.exception("Failed to retrieve prediction history")
            return Response(
                {"error": "Prediction history is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    @action(detail=False, methods=["get"])
    def accuracy(self, request):
        return Response({
            "overall_accuracy": None,
            "false_positive_rate": None,
            "false_negative_rate": None,
            "note": "Accuracy metrics are unavailable until predictions can be evaluated against verified outcomes.",
        })
