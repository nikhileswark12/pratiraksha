import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os

df = pd.read_parquet('datasets/train_v1.parquet')

# Include weather features (HDHI Pollution Data)
features = ['day', 'month', 'hour', 'weekend_flag', 'festival_flag',
            'prev_day_admissions', 'weekly_avg_admissions', 'bed_capacity', 
            'season', 'AQI', 'temperature', 'humidity']
target = 'target_surge'

# Handle NaNs for PyTorch
df['AQI'] = df['AQI'].fillna(df['AQI'].median()).fillna(50)
df['temperature'] = df['temperature'].fillna(df['temperature'].median()).fillna(0)
df['humidity'] = df['humidity'].fillna(df['humidity'].median()).fillna(0)

X = df[features].values
y = df[target].values.reshape(-1, 1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

scaler_X = StandardScaler()
X_train_scaled = scaler_X.fit_transform(X_train)
X_val_scaled = scaler_X.transform(X_val)
X_test_scaled = scaler_X.transform(X_test)

os.makedirs('ml_service', exist_ok=True)
with open('ml_service/scaler.pkl', 'wb') as f:
    pickle.dump(scaler_X, f)

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

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = SurgePredictorModel(input_dim=len(features)).to(device)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

train_dataset = TensorDataset(torch.FloatTensor(X_train_scaled), torch.FloatTensor(y_train))
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
val_dataset = TensorDataset(torch.FloatTensor(X_val_scaled), torch.FloatTensor(y_val))
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

epochs = 15
best_val_loss = float('inf')

for epoch in range(epochs):
    model.train()
    train_loss = 0
    for batch_X, batch_y in train_loader:
        batch_X, batch_y = batch_X.to(device), batch_y.to(device)
        optimizer.zero_grad()
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
        
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for batch_X, batch_y in val_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            val_loss += loss.item()
            
    train_loss /= len(train_loader)
    val_loss /= len(val_loader)
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), 'ml_service/surge_predictor_best.pth')

model.load_state_dict(torch.load('ml_service/surge_predictor_best.pth'))
model.eval()
test_inputs = torch.FloatTensor(X_test_scaled).to(device)
test_targets = torch.FloatTensor(y_test).to(device)

with torch.no_grad():
    predictions = model(test_inputs)
    test_mse = criterion(predictions, test_targets).item()
    test_mae = torch.mean(torch.abs(predictions - test_targets)).item()

print(f'\nTraining Complete. Best Model Test MSE: {test_mse:.4f} | MAE: {test_mae:.4f}')

