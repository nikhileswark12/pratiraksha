from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import torch.nn as nn
import pickle
import pandas as pd
import datetime

app = FastAPI()

class SurgePredictorModel(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1)
        )
    def forward(self, x):
        return self.net(x)

# Load globals
try:
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    model = SurgePredictorModel(input_dim=13) # 14 features
    model.load_state_dict(torch.load('surge_predictor_best.pth'))
    model.eval()
    model_loaded = True
except Exception as e:
    print('Warning: Model weights not found. Ensure train_model.py ran successfully.')
    model_loaded = False

class PredictionRequest(BaseModel):
    event: str = ''
    pollution_level: float = 50.0
    temperature: float = 25.0
    humidity: float = 50.0
    city: str = 'Unknown'
    date: str = datetime.date.today().isoformat()

@app.post('/predict')
def predict_surge(req: PredictionRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail='Model not initialized')
        
    try:
        dt = pd.to_datetime(req.date)
        day = dt.day
        month = dt.month
        hour = 12
        weekend_flag = 1 if dt.dayofweek in [5, 6] else 0
        festival_flag = 1 if req.event and req.event.lower() not in ['none', 'null', ''] else 0
        
        if month in [12, 1, 2]: season = 1
        elif month in [3, 4, 5]: season = 3
        elif month in [6, 7, 8, 9]: season = 4
        else: season = 5
        
        features = [
            day, month, hour, weekend_flag, festival_flag,
            50, 50, 200, season, req.pollution_level,
            req.temperature, req.humidity, 0
        ]
        
        x_scaled = scaler.transform([features])
        with torch.no_grad():
            pred = model(torch.FloatTensor(x_scaled)).item()
            
        predicted_surge = max(min(int(pred), 100), 0)
        
        if predicted_surge >= 60: risk_level = 'HIGH'
        elif predicted_surge >= 30: risk_level = 'MEDIUM'
        else: risk_level = 'LOW'
        
        return {
            'risk_level': risk_level,
            'risk_score': predicted_surge,
            'predicted_surge': predicted_surge,
            'confidence': 85.0,
            'affected_departments': ['ER'],
            'recommended_actions': ['Monitor situation' if risk_level == 'LOW' else 'Alert on-call staff'],
            'resource_requirements': {'beds': int(predicted_surge/10)+5},
            'timeline': req.date,
            'model_version': 'surge-predictor-v1.0'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

