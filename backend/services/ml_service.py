import joblib
import tensorflow as tf
import numpy as np
import pandas as pd
from datetime import datetime
from config import Config
from utils.constants import REGION_MAP
from services.api_service import APIService

class MLService:
    def __init__(self):
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        self.feature_names = []
        self.load_artifacts()

    def load_artifacts(self):
        try:
            self.scaler_X = joblib.load(Config.SCALER_X_PATH)
            self.scaler_y = joblib.load(Config.SCALER_Y_PATH)
            self.feature_names = list(self.scaler_X.feature_names_in_)
            self.model = tf.keras.models.load_model(Config.MODEL_PATH, compile=False)
            print("Artifacts Loaded.")
        except Exception as e:
            print(f"Error loading ML artifacts: {e}")

    def predict_country(self, country):
        # 1. Fetch Features from APIs
        temp, precip, humidity = APIService.fetch_weather(country)  # Now returns humidity
        density = APIService.fetch_population_density(country)
        historical_data = APIService.fetch_historical_disease_data(country)  # Get proper lag data from WHO
        
        # Calculate derived features
        vector_index = APIService.calculate_vector_index(temp, humidity, precip)
        water_stagnation = APIService.calculate_water_stagnation_index(precip, temp)
        
        # 2. Build Feature Vector
        features = {name: 0.0 for name in self.feature_names}
        now = datetime.now()
        
        # Time-based features
        features['year'] = now.year
        features['month'] = now.month
        features['quarter'] = (now.month - 1) // 3 + 1
        features['month_sin'] = np.sin(2 * np.pi * now.month / 12)
        features['month_cos'] = np.cos(2 * np.pi * now.month / 12)
        
        # Weather features (now includes humidity from OpenWeatherMap)
        features['avg_temp_c'] = temp
        features['precipitation_mm'] = precip
        features['humidity_pct'] = humidity  # NEW: fetched from weather API
        
        # Derived environmental features
        features['vector_index'] = vector_index  # NEW: calculated from temp/humidity/precip
        features['water_stagnation_index'] = water_stagnation  # NEW: calculated from precip/temp
        
        # Population and health features
        features['population_density'] = density
        features['air_quality_index'] = 50.0  # Default moderate AQI
        features['uv_index'] = 6.0  # Default moderate UV
        features['healthcare_budget'] = 1e6
        
        # Lag features from WHO historical data (properly differentiated)
        features['malaria_cases_lag_1'] = historical_data['lag_1']
        features['malaria_cases_lag_2'] = historical_data['lag_2']
        features['malaria_cases_lag_3'] = historical_data['lag_3']
        features['malaria_cases_lag_6'] = historical_data['lag_6']
        features['malaria_cases_lag_12'] = historical_data['lag_12']
        
        # Rolling statistics from WHO historical data
        features['malaria_cases_roll_mean_3'] = historical_data['roll_mean_3']
        features['malaria_cases_roll_mean_6'] = historical_data['roll_mean_6']
        features['malaria_cases_roll_mean_12'] = historical_data['roll_mean_12']
        features['malaria_cases_roll_std_3'] = historical_data['roll_std_3']
        features['malaria_cases_roll_std_6'] = historical_data['roll_std_6']
        features['malaria_cases_roll_std_12'] = historical_data['roll_std_12']
        
        # Also set dengue lag features if they exist
        for key in ['lag_1', 'lag_2', 'lag_3', 'lag_6', 'lag_12']:
            dengue_key = f'dengue_cases_{key}'
            if dengue_key in features:
                features[dengue_key] = historical_data[key] * 0.3  # Dengue typically lower
        
        for key in ['roll_mean_3', 'roll_mean_6', 'roll_mean_12', 'roll_std_3', 'roll_std_6', 'roll_std_12']:
            dengue_key = f'dengue_cases_{key}'
            if dengue_key in features:
                features[dengue_key] = historical_data[key] * 0.3
        
        # Handle any generic lag columns that might exist with different naming
        for col in self.feature_names:
            if 'lag' in col.lower() and features[col] == 0.0:
                if '1' in col:
                    features[col] = historical_data['lag_1']
                elif '2' in col:
                    features[col] = historical_data['lag_2']
                elif '3' in col:
                    features[col] = historical_data['lag_3']
                elif '6' in col:
                    features[col] = historical_data['lag_6']
                elif '12' in col:
                    features[col] = historical_data['lag_12']
            elif 'roll' in col.lower() and features[col] == 0.0:
                if 'mean' in col.lower():
                    if '3' in col:
                        features[col] = historical_data['roll_mean_3']
                    elif '6' in col:
                        features[col] = historical_data['roll_mean_6']
                    elif '12' in col:
                        features[col] = historical_data['roll_mean_12']
                elif 'std' in col.lower():
                    if '3' in col:
                        features[col] = historical_data['roll_std_3']
                    elif '6' in col:
                        features[col] = historical_data['roll_std_6']
                    elif '12' in col:
                        features[col] = historical_data['roll_std_12']

        # One-hot Encodings for country and region
        if f"country_{country}" in features: features[f"country_{country}"] = 1.0
        reg = REGION_MAP.get(country)
        if reg and f"region_{reg}" in features: features[f"region_{reg}"] = 1.0

        # 3. Make Prediction
        df_in = pd.DataFrame([features])[self.feature_names]
        X_scaled = self.scaler_X.transform(df_in)
        preds_scaled = self.model.predict(X_scaled, verbose=0)
        preds = self.scaler_y.inverse_transform(preds_scaled)
        
        # Log prediction details for debugging
        print(f"Prediction for {country}: temp={temp:.1f}°C, humidity={humidity}%, precip={precip}mm")
        print(f"  Vector Index: {vector_index}, Water Stagnation: {water_stagnation}")
        print(f"  Lag Features: lag_1={historical_data['lag_1']:.1f}, lag_12={historical_data['lag_12']:.1f}")
        
        return {
            'malaria': max(0, int(preds[0][0])),
            'dengue': max(0, int(preds[0][1])),
            'risk_level': 'High' if preds[0][0] > 50000 else 'Medium' if preds[0][0] > 10000 else 'Low',
            'features_used': {
                'temperature': round(temp, 1),
                'humidity': humidity,
                'precipitation': precip,
                'vector_index': vector_index,
                'water_stagnation_index': water_stagnation,
                'population_density': round(density, 1)
            }
        }