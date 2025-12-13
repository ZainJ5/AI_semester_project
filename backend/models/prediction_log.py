"""
Database model for logging prediction features
"""
import sqlite3
import json
from datetime import datetime
import os

class PredictionLogger:
    def __init__(self, db_path='prediction_logs.db'):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize the database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                country TEXT NOT NULL,
                
                -- Environmental Features
                avg_temp_c REAL,
                precipitation_mm REAL,
                humidity_pct REAL,
                
                -- Derived Environmental
                vector_index REAL,
                water_stagnation_index REAL,
                air_quality_index REAL,
                uv_index REAL,
                
                -- Population & Health
                population_density REAL,
                healthcare_budget REAL,
                
                -- Time Features
                year INTEGER,
                month INTEGER,
                
                -- Lag Features (Malaria)
                malaria_lag_1 REAL,
                malaria_lag_2 REAL,
                malaria_lag_3 REAL,
                malaria_lag_6 REAL,
                malaria_lag_12 REAL,
                
                -- Rolling Statistics (Malaria)
                malaria_roll_mean_3 REAL,
                malaria_roll_mean_6 REAL,
                malaria_roll_mean_12 REAL,
                malaria_roll_std_3 REAL,
                malaria_roll_std_6 REAL,
                malaria_roll_std_12 REAL,
                
                -- Region & Country (stored as text for readability)
                region TEXT,
                country_encoded TEXT,
                
                -- Predictions
                predicted_malaria INTEGER,
                predicted_dengue INTEGER,
                risk_level TEXT,
                
                -- Complete feature vector (JSON)
                all_features_json TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_prediction(self, country, features_dict, predictions):
        """
        Log a prediction with all features
        
        Args:
            country: Country name
            features_dict: Dictionary of all features sent to model
            predictions: Dictionary with malaria, dengue, risk_level
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract region from features if available
        region = None
        for key in features_dict:
            if 'region_' in key.lower() and features_dict[key] == 1:
                region = key.replace('region_', '').replace('_', ' ')
                break
        
        # Extract country encoding
        country_encoded = None
        for key in features_dict:
            if 'country_' in key.lower() and features_dict[key] == 1:
                country_encoded = key.replace('country_', '').replace('_', ' ')
                break
        
        cursor.execute('''
            INSERT INTO prediction_logs (
                timestamp, country,
                avg_temp_c, precipitation_mm, humidity_pct,
                vector_index, water_stagnation_index, air_quality_index, uv_index,
                population_density, healthcare_budget,
                year, month,
                malaria_lag_1, malaria_lag_2, malaria_lag_3, malaria_lag_6, malaria_lag_12,
                malaria_roll_mean_3, malaria_roll_mean_6, malaria_roll_mean_12,
                malaria_roll_std_3, malaria_roll_std_6, malaria_roll_std_12,
                region, country_encoded,
                predicted_malaria, predicted_dengue, risk_level,
                all_features_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            country,
            features_dict.get('avg_temp_c', 0),
            features_dict.get('precipitation_mm', 0),
            features_dict.get('humidity_pct', 0) or features_dict.get('humidity', 0),
            features_dict.get('vector_index', 0),
            features_dict.get('water_stagnation_index', 0),
            features_dict.get('air_quality_index', 0),
            features_dict.get('uv_index', 0),
            features_dict.get('population_density', 0),
            features_dict.get('healthcare_budget', 0),
            features_dict.get('year', 0),
            features_dict.get('month', 0),
            features_dict.get('malaria_cases_lag_1', 0),
            features_dict.get('malaria_cases_lag_2', 0),
            features_dict.get('malaria_cases_lag_3', 0),
            features_dict.get('malaria_cases_lag_6', 0),
            features_dict.get('malaria_cases_lag_12', 0),
            features_dict.get('malaria_cases_roll_mean_3', 0),
            features_dict.get('malaria_cases_roll_mean_6', 0),
            features_dict.get('malaria_cases_roll_mean_12', 0),
            features_dict.get('malaria_cases_roll_std_3', 0),
            features_dict.get('malaria_cases_roll_std_6', 0),
            features_dict.get('malaria_cases_roll_std_12', 0),
            region,
            country_encoded,
            predictions.get('malaria', 0),
            predictions.get('dengue', 0),
            predictions.get('risk_level', 'Unknown'),
            json.dumps(features_dict, indent=2)
        ))
        
        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        
        return log_id
    
    def get_recent_logs(self, limit=50):
        """Get recent prediction logs"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prediction_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        
        conn.close()
        return logs
    
    def get_logs_by_country(self, country, limit=20):
        """Get logs for a specific country"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prediction_logs 
            WHERE country = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (country, limit))
        
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        
        conn.close()
        return logs
    
    def clear_logs(self):
        """Clear all logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM prediction_logs')
        conn.commit()
        conn.close()
