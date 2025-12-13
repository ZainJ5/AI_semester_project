import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    MODEL_PATH = os.path.join(DATA_DIR, 'best_ann_model (1).h5')
    SCALER_X_PATH = os.path.join(DATA_DIR, 'scaler_X (1).pkl')
    SCALER_Y_PATH = os.path.join(DATA_DIR, 'scaler_y (1).pkl')
    
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
    NINJA_API_KEY = os.getenv('NINJA_API_KEY', '')
    AVIATION_KEY = os.getenv('AVIATION_KEY', '')