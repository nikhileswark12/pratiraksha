import pandas as pd
import numpy as np
import holidays
import os

def prepare_data():
    aqi_path = 'datasets/Air_Quality_Data_in_India/city_day.csv'
    admissions_path = 'datasets/ADMISSIONS.csv'
    output_path = 'datasets/train_v1.parquet'
    
    # 1. Load India AQI Data
    df_aqi = pd.read_csv(aqi_path)
    df_aqi['Date'] = pd.to_datetime(df_aqi['Date'])
    df_aqi['AQI'] = df_aqi['AQI'].fillna(df_aqi['AQI'].mean())
    df_aqi = df_aqi.dropna(subset=['Date', 'City'])
    
    # 2. Load Real Admissions Data
    df_adm = pd.read_csv(admissions_path)
    df_adm['ADMITTIME'] = pd.to_datetime(df_adm['ADMITTIME'])
    
    # MIMIC-III dates are in the future (2100s). We will shift them to align with 2015-2020 AQI data.
    # Find the min date and shift it to 2015-01-01
    min_date = df_adm['ADMITTIME'].min()
    target_start = pd.to_datetime('2015-01-01')
    shift = target_start - min_date
    df_adm['Shifted_Date'] = (df_adm['ADMITTIME'] + shift).dt.date
    df_adm['Shifted_Date'] = pd.to_datetime(df_adm['Shifted_Date'])
    
    # Aggregate daily admissions
    daily_admissions = df_adm.groupby('Shifted_Date').size().reset_index(name='target_surge')
    
    # 3. Join AQI and Admissions
    df = pd.merge(df_aqi, daily_admissions, left_on='Date', right_on='Shifted_Date', how='left')
    
    # GAPS: For dates without admissions in the MIMIC dataset, we leave as NaN, but for training we drop rows without target
    # Documenting gaps: We do not synthesize the target.
    print(f'AQI rows: {len(df_aqi)}. After join: {len(df)}. Missing target_surge: {df["target_surge"].isna().sum()}')
    df = df.dropna(subset=['target_surge'])
    
    # 4. Feature Engineering
    df['day'] = df['Date'].dt.day
    df['month'] = df['Date'].dt.month
    df['hour'] = 12
    df['weekend_flag'] = df['Date'].dt.dayofweek.isin([5,6]).astype(int)
    
    def get_season(month):
        if month in [12, 1, 2]: return 1
        elif month in [3, 4, 5]: return 3
        elif month in [6, 7, 8, 9]: return 4
        else: return 5
    df['season'] = df['month'].apply(get_season)
    
    in_holidays = holidays.India()
    df['festival_flag'] = df['Date'].apply(lambda x: 1 if x in in_holidays else 0)
    
    # 5. Missing IMD Weather Data
    # We do NOT have the IMD rainfall/temperature data on disk.
    # We accept this gap and set them to NaN, removing them from the features array in training.
    df['temperature'] = np.nan
    df['humidity'] = np.nan
    df['rainfall'] = np.nan
    
    # 6. Historical features
    df = df.sort_values(by=['City', 'Date'])
    df['prev_day_admissions'] = df.groupby('City')['target_surge'].shift(1).fillna(df["target_surge"].mean())
    df['weekly_avg_admissions'] = df.groupby('City')['target_surge'].shift(1).rolling(window=7, min_periods=1).mean().fillna(df["target_surge"].mean())
    df['bed_capacity'] = 200
    
    columns_to_keep = ['Date', 'City', 'day', 'month', 'hour', 'weekend_flag', 'festival_flag', 
                       'prev_day_admissions', 'weekly_avg_admissions', 'bed_capacity', 'season', 
                       'AQI', 'temperature', 'humidity', 'rainfall', 'target_surge']
                       
    final_df = df[columns_to_keep]
    final_df.to_parquet(output_path, index=False)
    print(f'Successfully generated {len(final_df)} training rows with real admissions target.')
    
if __name__ == '__main__':
    prepare_data()


