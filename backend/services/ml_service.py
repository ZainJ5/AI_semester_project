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
        # 1. Fetch Features
        temp, precip = APIService.fetch_weather(country)
        density = APIService.fetch_population_density(country)
        baseline = APIService.fetch_disease_baseline(country)
        
        # 2. Build Vector
        features = {name: 0.0 for name in self.feature_names}
        now = datetime.now()
        features['year'] = now.year
        features['month'] = now.month
        features['quarter'] = (now.month - 1) // 3 + 1
        features['month_sin'] = np.sin(2 * np.pi * now.month / 12)
        features['month_cos'] = np.cos(2 * np.pi * now.month / 12)
        features['avg_temp_c'] = temp
        features['precipitation_mm'] = precip
        features['population_density'] = density
        features['air_quality_index'] = 50.0
        features['uv_index'] = 6.0
        features['healthcare_budget'] = 1e6
        
        # Lags
        lag_cols = [c for c in self.feature_names if 'lag' in c or 'roll' in c]
        for col in lag_cols: features[col] = baseline

        # Encodings
        if f"country_{country}" in features: features[f"country_{country}"] = 1.0
        reg = REGION_MAP.get(country)
        if reg and f"region_{reg}" in features: features[f"region_{reg}"] = 1.0

        # 3. Predict
        df_in = pd.DataFrame([features])[self.feature_names]
        X_scaled = self.scaler_X.transform(df_in)
        preds_scaled = self.model.predict(X_scaled, verbose=0)
        preds = self.scaler_y.inverse_transform(preds_scaled)
        
        return {
            'malaria': max(0, int(preds[0][0])),
            'dengue': max(0, int(preds[0][1])),
            'risk_level': 'High' if preds[0][0] > 50000 else 'Medium' if preds[0][0] > 10000 else 'Low'
        }