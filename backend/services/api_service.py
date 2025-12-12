import requests
from config import Config
from utils.constants import AREA_MAP, DENSITY_BASELINE_MAP, MALARIA_BASELINE_MAP, COUNTRY_CODE_MAP

class APIService:
    
    @staticmethod
    def fetch_weather(country):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={country}&appid={Config.WEATHER_API_KEY}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                temp_c = data['main']['temp'] - 273.15
                weather_main = data['weather'][0]['main'].lower()
                precip = 5.0 if 'rain' in weather_main else 0.0
                return temp_c, precip
        except Exception as e:
            print(f"Weather API Error: {e}")
        return 25.0, 0.0

    @staticmethod
    def fetch_population_density(country):
        # 1. Try Live API if we know the area
        if country in AREA_MAP:
            try:
                headers = {'X-Api-Key': Config.NINJA_API_KEY.strip()}
                url = f"https://api.api-ninjas.com/v1/population?country={country}"
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    latest = None
                    if isinstance(data, dict) and 'historical_population' in data:
                        if data['historical_population']: latest = data['historical_population'][0]['population']
                    elif isinstance(data, list) and data:
                        latest = data[0]['population']
                    
                    if latest: return latest / AREA_MAP[country]
            except Exception as e:
                print(f"Pop API Error: {e}")
        
        # 2. Fallback
        return DENSITY_BASELINE_MAP.get(country, 300.0)

    @staticmethod
    def fetch_disease_baseline(country):
        if country in COUNTRY_CODE_MAP:
            try:
                code = COUNTRY_CODE_MAP[country]
                url = f"https://ghoapi.azureedge.net/api/MALARIA_CONF_CASES?$filter=SpatialDim eq '{code}'&$format=json"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'value' in data and data['value']:
                        recs = sorted(data['value'], key=lambda x: x['TimeDim'], reverse=True)
                        return recs[0]['NumericValue'] / 12.0
            except Exception as e:
                print(f"WHO API Error: {e}")
        return MALARIA_BASELINE_MAP.get(country, 0.0)

    @staticmethod
    def fetch_flight_connections(country):
        """
        Mock flight connections restricted to countries appearing in the Training Dataset.
        This ensures every node in the graph gets a valid ML prediction.
        """
        # Graph optimized for the 120 countries in climate_disease_dataset.csv
        connections = {
            # --- SOUTH ASIA & MIDDLE EAST HUB ---
            'Pakistan': ['United Arab Emirates', 'Saudi Arabia', 'Iran', 'Bangladesh', 'Oman'],
            'Bangladesh': ['Pakistan', 'Myanmar', 'Nepal', 'India'], # India is missing, mapped to Nepal/Myanmar
            'Iran': ['Pakistan', 'Turkmenistan', 'Armenia', 'Azerbaijan'],
            'United Arab Emirates': ['Pakistan', 'Saudi Arabia', 'Egypt', 'Germany', 'Oman'],
            'Saudi Arabia': ['United Arab Emirates', 'Egypt', 'Sudan', 'Ethiopia', 'Pakistan'],
            'Oman': ['United Arab Emirates', 'Pakistan', 'Saudi Arabia'],

            # --- EUROPE HUB (Germany/Belgium/Sweden/Ireland) ---
            'Germany': ['United Arab Emirates', 'Belgium', 'Poland', 'Czech Republic', 'Denmark', 'Sweden'],
            'Belgium': ['Germany', 'France', 'Ireland', 'Netherlands'], # France missing? Use Ireland
            'Ireland': ['Belgium', 'Portugal', 'Brazil'], # Gateway to Americas
            'Sweden': ['Germany', 'Finland', 'Estonia', 'Denmark'],
            'Portugal': ['Ireland', 'Brazil', 'Morocco'],

            # --- EAST ASIA HUB (Japan/Korea/Philippines) ---
            'Japan': ['Korea', 'Philippines', 'Guam', 'United Arab Emirates'],
            'Korea': ['Japan', 'China', 'Philippines'], # China missing? Map to neighbors
            'Philippines': ['Japan', 'Korea', 'Palau', 'Singapore'],
            
            # --- AFRICA HUB ---
            'Egypt': ['Saudi Arabia', 'United Arab Emirates', 'Sudan', 'Ethiopia', 'Morocco'],
            'Ethiopia': ['Egypt', 'Kenya', 'Sudan', 'Saudi Arabia'],
            'Kenya': ['Ethiopia', 'Nigeria', 'South Africa'],
            'Nigeria': ['Kenya', 'Ghana', 'Togo', 'Benin'],
            'South Africa': ['Kenya', 'Mozambique', 'Namibia', 'Lesotho'],
            'Morocco': ['Portugal', 'Egypt', 'Mauritania'],

            # --- AMERICAS HUB (Brazil/Mexico/Colombia) ---
            'Brazil': ['Portugal', 'Colombia', 'Peru', 'Suriname', 'Mexico'],
            'Colombia': ['Brazil', 'Ecuador', 'Peru', 'Mexico'],
            'Mexico': ['Brazil', 'Colombia', 'Cuba', 'Guatemala'],
            'Cuba': ['Mexico', 'Bahamas', 'Dominican Republic'],
            'Peru': ['Brazil', 'Colombia', 'Ecuador', 'Chile']
        }
        return connections.get(country, [])