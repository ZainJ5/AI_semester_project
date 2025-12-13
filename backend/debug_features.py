"""
Compare our feature vector against actual training data to find mismatches
"""
import pandas as pd
import numpy as np
import joblib
from services.ml_service import MLService

# Load training dataset
df_train = pd.read_csv('C:/Users/DELL/OneDrive/Desktop/ai/climate_disease_dataset.csv')

# Load scaler to see expected features
scaler_X = joblib.load('data/scaler_X (1).pkl')
expected_features = list(scaler_X.feature_names_in_)

# Initialize ML service
ml_service = MLService()

# Test with Brazil (exists in training data)
print("=" * 80)
print("FEATURE COMPARISON: Brazil")
print("=" * 80)

# Get one sample from training data for Brazil
brazil_train = df_train[df_train['country'] == 'Brazil'].iloc[100]  # Random sample
print("\nTRAINING DATA SAMPLE:")
print(brazil_train)

# Get prediction features from ML service
print("\n" + "=" * 80)
print("CREATING INFERENCE FEATURES...")
print("=" * 80)

# Manually build features like ML service does
from services.api_service import APIService
from datetime import datetime
from utils.constants import REGION_MAP

country = "Brazil"
temp, precip, humidity = APIService.fetch_weather(country)
density = APIService.fetch_population_density(country)
historical_data = APIService.fetch_historical_disease_data(country)

features = {name: 0.0 for name in expected_features}
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

# Lag features
for key in ['lag_1', 'lag_2', 'lag_3', 'lag_6', 'lag_12']:
    features[f'malaria_cases_{key}'] = historical_data[key]
    features[f'dengue_cases_{key}'] = historical_data[key] * 0.3

# Rolling features
for key in ['roll_mean_3', 'roll_mean_6', 'roll_std_3', 'roll_std_6']:
    features[f'malaria_cases_{key}'] = historical_data[key]
    features[f'dengue_cases_{key}'] = historical_data[key] * 0.3

# One-hot encoding
if f"country_{country}" in features:
    features[f"country_{country}"] = 1.0
reg = REGION_MAP.get(country)
if reg and f"region_{reg}" in features:
    features[f"region_{reg}"] = 1.0

print("\nINFERENCE FEATURES (non-zero values):")
for name, value in features.items():
    if value != 0.0:
        # Find corresponding training value
        train_val = "N/A"
        if name in brazil_train.index:
            train_val = brazil_train[name]
        print(f"{name:40} = {value:12.4f}  (train: {train_val})")

print("\n" + "=" * 80)
print("FEATURE STATISTICS COMPARISON")
print("=" * 80)

numeric_features = ['year', 'month', 'avg_temp_c', 'precipitation_mm', 'air_quality_index', 
                    'uv_index', 'population_density', 'healthcare_budget']

for feat in numeric_features:
    if feat in df_train.columns:
        train_min = df_train[feat].min()
        train_max = df_train[feat].max()
        train_mean = df_train[feat].mean()
        our_value = features.get(feat, 0)
        
        in_range = "✓" if train_min <= our_value <= train_max else "✗"
        print(f"\n{feat}:")
        print(f"  Training range: [{train_min:10.2f}, {train_max:10.2f}], mean: {train_mean:10.2f}")
        print(f"  Our value:      {our_value:10.2f} {in_range}")

print("\n" + "=" * 80)
print("CHECKING FOR MISSING FEATURES")
print("=" * 80)

# Check if we're missing any features that exist in training
missing_in_inference = []
for feat in expected_features:
    if feat not in features or features[feat] == 0.0:
        if not feat.startswith('country_') and not feat.startswith('region_'):
            missing_in_inference.append(feat)

if missing_in_inference:
    print(f"\n⚠️  Features that are 0 in inference but might be important:")
    for feat in missing_in_inference[:20]:  # Show first 20
        print(f"  - {feat}")
else:
    print("✓ All expected features are populated")
