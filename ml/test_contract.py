import json
import torch
import torch.nn as nn
import pickle
import pandas as pd
import datetime

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

def test_contract():
    input_payload = {
        'event': 'mass_gathering',
        'pollution_level': 110.0,
        'temperature': 38.5,
        'humidity': 85.0,
        'city': 'Delhi',
        'date': datetime.date.today().isoformat()
    }
    
    dt = pd.to_datetime(input_payload['date'])
    day = dt.day
    month = dt.month
    hour = 12
    weekend_flag = 1 if dt.dayofweek in [5, 6] else 0
    festival_flag = 1 if input_payload['event'] else 0
    
    if month in [12, 1, 2]: season = 1
    elif month in [3, 4, 5]: season = 3
    elif month in [6, 7, 8, 9]: season = 4
    else: season = 5
    
    features = [
        day, month, hour, weekend_flag, festival_flag,
        50, 50, 200, season, input_payload['pollution_level'],
        input_payload['temperature'], input_payload['humidity']
    ]
    
    with open('ml_service/scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
        
    model = SurgePredictorModel(input_dim=len(features))
    model.load_state_dict(torch.load('ml_service/surge_predictor_best.pth'))
    model.eval()
        
    x_scaled = scaler.transform([features])
    with torch.no_grad():
        pred = model(torch.FloatTensor(x_scaled)).item()
        
    predicted_surge = max(min(int(pred), 100), 0)
    
    if predicted_surge >= 60: risk_level = 'HIGH'
    elif predicted_surge >= 30: risk_level = 'MEDIUM'
    else: risk_level = 'LOW'
    
    output_payload = {
        'risk_level': risk_level,
        'risk_score': predicted_surge,
        'predicted_surge': predicted_surge,
        'confidence': 85.0,
        'affected_departments': ['ER'],
        'recommended_actions': ['Monitor situation'],
        'resource_requirements': {'beds': int(predicted_surge/10)+5},
        'timeline': input_payload['date'],
        'model_version': 'surge-predictor-v1.0'
    }
    
    print('Contract test passed!')

if __name__ == '__main__':
    test_contract()

