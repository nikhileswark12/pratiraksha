import uuid
import datetime
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
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
        city = data.get('city', 'Unknown')
        target_date = data.get('date', datetime.date.today().isoformat())
        
        # ML Service temporarily disabled - reverting to heuristic fallback
        prediction_id = str(uuid.uuid4())
        
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
