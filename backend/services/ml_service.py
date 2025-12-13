import joblib
import tensorflow as tf
import numpy as np
import pandas as pd
from datetime import datetime
from config import Config
from utils.constants import REGION_MAP
from services.api_service import APIService
from models.prediction_log import PredictionLogger

class MLService:
    def __init__(self):
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        self.feature_names = []
        self.logger = PredictionLogger()
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
        # NOTE: Training data is 2000-2023, so cap year at 2023 to match training distribution
        features['year'] = min(now.year, 2023)
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
        # Healthcare budget: training range is 205-4969, use median value
        features['healthcare_budget'] = 2750.0  # Approximate median from training data
        
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
        
        # Prepare comprehensive prediction results
        predictions = {
            'malaria': max(0, int(preds[0][0])),
            'dengue': max(0, int(preds[0][1])),
            'risk_level': 'High' if preds[0][0] > 50000 else 'Medium' if preds[0][0] > 10000 else 'Low',
            'features_used': {
                # Environmental Features
                'temperature': round(temp, 1),
                'humidity': humidity,
                'precipitation': precip,
                'vector_index': round(vector_index, 2),
                'water_stagnation_index': round(water_stagnation, 2),
                
                # Population & Healthcare
                'population_density': round(density, 1),
                'healthcare_budget': round(features['healthcare_budget'], 1),
                
                # Time Features
                'year': int(features['year']),
                'month': int(features['month']),
                
                # Historical Data (WHO)
                'malaria_lag_1': round(historical_data['lag_1'], 2),
                'malaria_lag_12': round(historical_data['lag_12'], 2),
                'malaria_rolling_mean_3': round(historical_data['roll_mean_3'], 2),
                
                # Region
                'region': REGION_MAP.get(country, 'Unknown')
            },
            'explanation': {
                'environmental_impact': self._get_environmental_impact(temp, humidity, precip),
                'historical_trend': self._get_historical_trend(historical_data),
                'risk_factors': self._identify_risk_factors(temp, humidity, precip, vector_index, historical_data)
            }
        }
        
        # Log all features to database
        try:
            self.logger.log_prediction(country, features, predictions)
        except Exception as e:
            print(f"Warning: Failed to log prediction: {e}")
        
        # Console log for debugging
        print(f"Prediction for {country}: temp={temp:.1f}°C, humidity={humidity}%, precip={precip}mm")
        print(f"  Vector Index: {vector_index}, Water Stagnation: {water_stagnation}")
        print(f"  Lag Features: lag_1={historical_data['lag_1']:.1f}, lag_12={historical_data['lag_12']:.1f}")
        print(f"  Year: {features['year']}, Month: {features['month']}, Healthcare: ${features['healthcare_budget']}")
        print(f"  Region: {REGION_MAP.get(country, 'Unknown')}")
        
        return predictions
    
    def _get_environmental_impact(self, temp, humidity, precip):
        """Analyze environmental conditions impact"""
        impacts = []
        
        # Temperature analysis
        if 20 <= temp <= 35:
            impacts.append("Optimal temperature for mosquito breeding (20-35°C)")
        elif temp < 20:
            impacts.append("Cold temperature suppresses mosquito activity")
        else:
            impacts.append("High temperature reduces mosquito survival")
        
        # Humidity analysis
        if humidity > 60:
            impacts.append("High humidity favorable for mosquito survival")
        elif humidity < 40:
            impacts.append("Low humidity unfavorable for mosquitos")
        else:
            impacts.append("Moderate humidity conditions")
        
        # Precipitation analysis
        if precip > 10:
            impacts.append("Recent rainfall creates breeding sites")
        elif precip > 0:
            impacts.append("Light precipitation present")
        else:
            impacts.append("No recent rainfall - fewer breeding sites")
        
        return impacts
    
    def _get_historical_trend(self, historical_data):
        """Analyze historical case trends"""
        lag_1 = historical_data['lag_1']
        lag_12 = historical_data['lag_12']
        roll_mean = historical_data['roll_mean_3']
        
        if lag_1 > 100:
            trend = "Very high historical malaria burden in this region"
        elif lag_1 > 50:
            trend = "Moderate to high historical cases"
        elif lag_1 > 20:
            trend = "Low to moderate historical cases"
        else:
            trend = "Very low historical malaria presence"
        
        # Trend direction
        if lag_1 > lag_12 * 1.2:
            direction = "increasing trend"
        elif lag_1 < lag_12 * 0.8:
            direction = "decreasing trend"
        else:
            direction = "stable trend"
        
        return f"{trend} with {direction}"
    
    def _identify_risk_factors(self, temp, humidity, precip, vector_index, historical_data):
        """Identify key risk factors"""
        factors = []
        
        # High vector index
        if vector_index > 60:
            factors.append("High mosquito activity index (vector_index > 60)")
        
        # Favorable climate
        if 25 <= temp <= 30 and humidity > 70:
            factors.append("Ideal climate conditions for malaria transmission")
        
        # Historical presence
        if historical_data['lag_1'] > 50:
            factors.append("Significant historical malaria cases in region")
        
        # Recent rainfall
        if precip > 15:
            factors.append("Heavy rainfall creating standing water")
        
        # Low risk indicators
        if temp < 15 or humidity < 30:
            factors.append("Environmental conditions suppress transmission")
        
        if not factors:
            factors.append("No significant risk factors identified")
        
        return factors