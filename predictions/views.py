import uuid
import datetime
import requests
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from hospitals.models import Hospital
from pratiraksha.utils import get_mongo_db, log_activity


class PredictionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        data = request.data
        
        # 1. Parse Input
        event = data.get('event', '')
        pollution_level = float(data.get('pollution_level', 50))
        temperature = float(data.get('temperature', 25))
        humidity = float(data.get('humidity', 50))
        rainfall_val = data.get('rainfall')
        rainfall = float(rainfall_val) if rainfall_val is not None else 0.0
        city = data.get('city', 'Unknown')
        target_date = data.get('date', datetime.date.today().isoformat())
        hospital_id = data.get('hospital_id')
        
        prediction_id = str(uuid.uuid4())
        
        is_network_wide = not bool(hospital_id)
        
        if is_network_wide:
            print("Network-wide prediction requested. Bypassing ML service (single-hospital scale) and using heuristic.")
        else:
            try:
                hospital = Hospital.objects.get(id=hospital_id)
                # Compute proxy scoped strictly to THIS hospital's occupancy
                # 0.05 (5%) multiplier produces proxy values in the ~0-50 range expected by the model
                total_occupancy = hospital.current_occupancy
                prev_day_admissions = float(total_occupancy * 0.05)
                weekly_avg_admissions = float(total_occupancy * 0.05)
                
                # Try ML Service first
                ml_payload = {
                    "event": event,
                    "pollution_level": pollution_level,
                    "temperature": temperature,
                    "humidity": humidity,
                    "rainfall": rainfall,
                    "prev_day_admissions": prev_day_admissions,
                    "weekly_avg_admissions": weekly_avg_admissions,
                    "city": city,
                    "date": target_date
                }
                
                resp = requests.post("http://127.0.0.1:8001/predict", json=ml_payload, timeout=5)
                resp.raise_for_status()
                ml_data = resp.json()
                
                response_data = {
                    "id": prediction_id,
                    "risk_level": ml_data["risk_level"],
                    "risk_score": ml_data["risk_score"],
                    "predicted_surge": ml_data["predicted_surge"],
                    "confidence": ml_data.get("confidence", 85.0),
                    "affected_departments": ml_data.get("affected_departments", ["ER"]),
                    "recommended_actions": ml_data.get("recommended_actions", []),
                    "resource_requirements": ml_data.get("resource_requirements", {}),
                    "timeline": ml_data.get("timeline", target_date),
                    "model_version": ml_data.get("model_version", "surge-predictor-v1-733rows")
                }
            except Exception as e:
                print(f"ML Service failed or hospital invalid: {e}. Falling back to heuristic.")
        
        # 2. Heuristic Logic (Interim Model) Fallback
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
            
        if event and event.lower() not in ['none', 'null', '']:
            surge += 20
            
        predicted_surge = min(surge, 100)
        
        # 3. Banding
        if predicted_surge >= 60:
            risk_level = "HIGH"
        elif predicted_surge >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        # 4. Construct response shape per Section 6.3
        fallback_data = {
            "id": prediction_id,
            "risk_level": risk_level,
            "risk_score": predicted_surge,
            "predicted_surge": predicted_surge,
            "confidence": 60.0, # low-ish for heuristic
            "affected_departments": ["ER", "Pulmonology"] if pollution_level > 100 else ["ER"],
            "recommended_actions": [
                "Alert on-call staff" if risk_level == "HIGH" else "Monitor situation",
                "Check equipment inventory"
            ],
            "resource_requirements": {
                "beds": int(predicted_surge / 10) + 5,
                "ventilators": 5 if pollution_level > 100 else 0
            },
            "timeline": target_date,
            "model_version": "rule-based-interim-0.1"
        }
        
        # If response_data is not defined by ML service, use fallback
        if 'response_data' not in locals():
            response_data = fallback_data
            
        # 5. Log to MongoDB
        db = get_mongo_db()
        if db is not None:
            try:
                log_doc = {
                    **response_data,
                    "input_data": data,
                    "user_id": str(request.user.id),
                    "created_at": datetime.datetime.utcnow()
                }
                db.predictions.insert_one(log_doc)
            except Exception as e:
                print(f"MongoDB logging failed: {e}")
                
        log_activity(
            actor=str(request.user.id),
            action="prediction created",
            resource_type="prediction",
            resource_id=prediction_id,
            extra_data={"risk_level": response_data.get("risk_level", risk_level), "predicted_surge": response_data.get("predicted_surge", predicted_surge)}
        )
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    def list(self, request):
        db = get_mongo_db()
        if db is None:
            return Response({"results": []})
        
        try:
            # Sort by created_at desc
            cursor = db.predictions.find().sort("created_at", -1).limit(50)
            results = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                # Convert datetime to string
                if 'created_at' in doc:
                    doc['created_at'] = doc['created_at'].isoformat()
                results.append(doc)
            return Response({"results": results})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def accuracy(self, request):
        # Placeholder for accuracy metrics
        return Response({
            "overall_accuracy": 0.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
            "note": "Validation data unavailable for interim rule-based engine."
        })
