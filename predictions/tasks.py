import os
import uuid
import datetime
import requests
from celery import shared_task
from hospitals.models import Hospital
from pratiraksha.utils import get_mongo_db

@shared_task
def generate_daily_predictions():
    """
    Day 13: Celery task for bulk prediction updates.
    Runs daily to generate predictions for all active hospitals.
    """
    hospitals = Hospital.objects.filter(status__in=['NORMAL', 'MODERATE', 'CRITICAL'])
    db = get_mongo_db()
    count = 0
    
    if db is None:
        return "MongoDB unavailable"

    target_date = datetime.date.today().isoformat()
    dt_obj = datetime.date.today()
    day_of_week = dt_obj.weekday()
    month = dt_obj.month
    
    ml_url = os.environ.get("ML_SERVICE_URL", "http://localhost:8001/predict")
    
    for hospital in hospitals:
        total_occupancy = hospital.current_occupancy
        
        ml_payload = {
            "event": "None",
            "pollution_level": 50,
            "temperature": 25.0,
            "humidity": 50.0,
            "date": target_date,
            "city": "Default",
            "day_of_week": day_of_week,
            "month": month
        }
        
        try:
            resp = requests.post(ml_url, json=ml_payload, timeout=5)
            if resp.ok:
                ml_data = resp.json()
                
                prediction_id = str(uuid.uuid4())
                log_doc = {
                    "id": prediction_id,
                    "hospital_id": str(hospital.id),
                    "risk_level": ml_data.get("risk_level", "LOW"),
                    "risk_score": ml_data.get("predicted_surge", 0),
                    "predicted_surge": ml_data.get("predicted_surge", 0),
                    "confidence": ml_data.get("confidence", 85.0),
                    "timeline": target_date,
                    "model_version": ml_data.get("model_version", "1.0.0"),
                    "created_at": datetime.datetime.utcnow(),
                    "source": "bulk_celery_task"
                }
                db.predictions.insert_one(log_doc)
                count += 1
        except Exception as e:
            print(f"Failed prediction for {hospital.id}: {e}")

    return f"Generated predictions for {count} hospitals"
