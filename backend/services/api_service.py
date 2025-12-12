import requests
from config import Config
from utils.constants import AREA_MAP, DENSITY_BASELINE_MAP, MALARIA_BASELINE_MAP, COUNTRY_CODE_MAP

class APIService:
    
    @staticmethod
    def fetch_weather(country):
        """
        Fetch weather data from OpenWeatherMap API.
        Returns: (temp_c, precip_mm, humidity_pct)
        """
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={country}&appid={Config.WEATHER_API_KEY}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                temp_c = data['main']['temp'] - 273.15
                humidity_pct = data['main'].get('humidity', 50.0)  # Get humidity from API
                weather_main = data['weather'][0]['main'].lower()
                
                # Estimate precipitation based on weather condition
                if 'rain' in weather_main or 'drizzle' in weather_main:
                    precip = 10.0
                elif 'thunderstorm' in weather_main:
                    precip = 20.0
                elif 'snow' in weather_main:
                    precip = 5.0
                elif 'mist' in weather_main or 'fog' in weather_main:
                    precip = 2.0
                else:
                    precip = 0.0
                
                return temp_c, precip, humidity_pct
        except Exception as e:
            print(f"Weather API Error: {e}")
        return 25.0, 0.0, 50.0  # Default values

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
    def fetch_historical_disease_data(country):
        """
        Fetch historical disease data from WHO API for calculating lag features.
        Returns dict with lag_1, lag_2, lag_3, lag_6, lag_12 (monthly case estimates)
        and rolling averages.
        """
        lag_data = {
            'lag_1': 0.0, 'lag_2': 0.0, 'lag_3': 0.0, 'lag_6': 0.0, 'lag_12': 0.0,
            'roll_mean_3': 0.0, 'roll_mean_6': 0.0, 'roll_mean_12': 0.0,
            'roll_std_3': 0.0, 'roll_std_6': 0.0, 'roll_std_12': 0.0
        }
        
        if country in COUNTRY_CODE_MAP:
            try:
                code = COUNTRY_CODE_MAP[country]
                url = f"https://ghoapi.azureedge.net/api/MALARIA_CONF_CASES?$filter=SpatialDim eq '{code}'&$format=json"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'value' in data and data['value']:
                        # Sort by year descending to get most recent data first
                        recs = sorted(data['value'], key=lambda x: x['TimeDim'], reverse=True)
                        
                        # Extract yearly values and convert to monthly estimates
                        yearly_values = []
                        for rec in recs[:12]:  # Get up to 12 years of data
                            if 'NumericValue' in rec and rec['NumericValue'] is not None:
                                monthly_estimate = rec['NumericValue'] / 12.0
                                yearly_values.append(monthly_estimate)
                        
                        if yearly_values:
                            # Calculate lag features (simulating monthly lags from yearly data)
                            # lag_1 = most recent year / 12 (approximate current month)
                            lag_data['lag_1'] = yearly_values[0] if len(yearly_values) > 0 else 0.0
                            lag_data['lag_2'] = yearly_values[0] * 0.95 if len(yearly_values) > 0 else 0.0
                            lag_data['lag_3'] = yearly_values[0] * 0.90 if len(yearly_values) > 0 else 0.0
                            lag_data['lag_6'] = (yearly_values[0] + yearly_values[1]) / 2 if len(yearly_values) > 1 else yearly_values[0] * 0.85
                            lag_data['lag_12'] = yearly_values[1] if len(yearly_values) > 1 else yearly_values[0] * 0.80
                            
                            # Calculate rolling means
                            if len(yearly_values) >= 3:
                                lag_data['roll_mean_3'] = sum(yearly_values[:3]) / 3
                                lag_data['roll_std_3'] = (sum((x - lag_data['roll_mean_3'])**2 for x in yearly_values[:3]) / 3) ** 0.5
                            else:
                                lag_data['roll_mean_3'] = sum(yearly_values) / len(yearly_values)
                                lag_data['roll_std_3'] = 0.0
                            
                            if len(yearly_values) >= 6:
                                lag_data['roll_mean_6'] = sum(yearly_values[:6]) / 6
                                lag_data['roll_std_6'] = (sum((x - lag_data['roll_mean_6'])**2 for x in yearly_values[:6]) / 6) ** 0.5
                            else:
                                lag_data['roll_mean_6'] = lag_data['roll_mean_3']
                                lag_data['roll_std_6'] = lag_data['roll_std_3']
                            
                            if len(yearly_values) >= 12:
                                lag_data['roll_mean_12'] = sum(yearly_values[:12]) / 12
                                lag_data['roll_std_12'] = (sum((x - lag_data['roll_mean_12'])**2 for x in yearly_values[:12]) / 12) ** 0.5
                            else:
                                lag_data['roll_mean_12'] = lag_data['roll_mean_6']
                                lag_data['roll_std_12'] = lag_data['roll_std_6']
                        
                        print(f"WHO Historical Data for {country}: lag_1={lag_data['lag_1']:.2f}, lag_12={lag_data['lag_12']:.2f}")
                        return lag_data
                        
            except Exception as e:
                print(f"WHO Historical API Error: {e}")
        
        # Fallback to baseline estimates if API fails
        baseline = MALARIA_BASELINE_MAP.get(country, 50.0)
        lag_data['lag_1'] = baseline
        lag_data['lag_2'] = baseline * 0.95
        lag_data['lag_3'] = baseline * 0.90
        lag_data['lag_6'] = baseline * 0.85
        lag_data['lag_12'] = baseline * 0.80
        lag_data['roll_mean_3'] = baseline * 0.95
        lag_data['roll_mean_6'] = baseline * 0.90
        lag_data['roll_mean_12'] = baseline * 0.85
        lag_data['roll_std_3'] = baseline * 0.1
        lag_data['roll_std_6'] = baseline * 0.15
        lag_data['roll_std_12'] = baseline * 0.2
        
        return lag_data

    @staticmethod
    def calculate_vector_index(temp_c, humidity_pct, precip_mm):
        """
        Estimate vector (mosquito) index based on environmental conditions.
        Mosquitoes thrive in warm (20-35°C), humid (>60%), wet conditions.
        Returns a value between 0-100.
        """
        # Temperature factor: optimal range 20-35°C
        if 20 <= temp_c <= 35:
            temp_factor = 1.0 - abs(temp_c - 27.5) / 15.0  # Peak at 27.5°C
        elif temp_c < 15 or temp_c > 40:
            temp_factor = 0.1  # Very low mosquito activity
        else:
            temp_factor = 0.5
        
        # Humidity factor: mosquitoes need humidity > 40%
        humidity_factor = min(1.0, humidity_pct / 80.0) if humidity_pct > 40 else 0.2
        
        # Precipitation factor: standing water promotes breeding
        precip_factor = min(1.0, precip_mm / 15.0) if precip_mm > 0 else 0.3
        
        # Combined vector index (0-100 scale)
        vector_index = (temp_factor * 0.4 + humidity_factor * 0.35 + precip_factor * 0.25) * 100
        return round(vector_index, 2)

    @staticmethod
    def calculate_water_stagnation_index(precip_mm, temp_c):
        """
        Estimate water stagnation index based on precipitation and temperature.
        High precipitation + warm temperature = more stagnant water breeding sites.
        Returns a value between 0-100.
        """
        # Precipitation contribution (more rain = more stagnant water potential)
        if precip_mm > 20:
            precip_factor = 1.0
        elif precip_mm > 10:
            precip_factor = 0.7
        elif precip_mm > 5:
            precip_factor = 0.5
        elif precip_mm > 0:
            precip_factor = 0.3
        else:
            precip_factor = 0.1
        
        # Temperature factor (warm weather = water doesn't evaporate ideally for mosquito breeding)
        if 25 <= temp_c <= 35:
            temp_factor = 0.9
        elif 20 <= temp_c < 25:
            temp_factor = 0.7
        elif temp_c > 35:
            temp_factor = 0.5  # Too hot, water evaporates
        else:
            temp_factor = 0.3  # Cold, less breeding
        
        water_stagnation_index = (precip_factor * 0.6 + temp_factor * 0.4) * 100
        return round(water_stagnation_index, 2)

    @staticmethod
    def fetch_flight_connections(country):
        """
        Flight connections STRICTLY limited to countries in the training dataset.
        All countries here exist in REGION_MAP/climate_disease_dataset.csv.
        This ensures every node in BFS gets a valid ML prediction.
        """
        from utils.constants import REGION_MAP
        
        # All connections use ONLY dataset countries (verified against REGION_MAP)
        connections = {
            # --- SOUTH ASIA & MIDDLE EAST HUB ---
            'Pakistan': ['United Arab Emirates', 'Saudi Arabia', 'Iran', 'Bangladesh', 'Oman'],
            'Bangladesh': ['Pakistan', 'Myanmar', 'Nepal'],  # All in dataset
            'Iran': ['Pakistan', 'Turkmenistan', 'Armenia', 'Azerbaijan'],
            'United Arab Emirates': ['Pakistan', 'Saudi Arabia', 'Egypt', 'Germany', 'Oman'],
            'Saudi Arabia': ['United Arab Emirates', 'Egypt', 'Ethiopia', 'Pakistan', 'Oman'],
            'Oman': ['United Arab Emirates', 'Pakistan', 'Saudi Arabia'],
            'Armenia': ['Iran', 'Azerbaijan'],
            'Azerbaijan': ['Iran', 'Armenia', 'Turkmenistan'],
            'Turkmenistan': ['Iran', 'Azerbaijan', 'Uzbekistan', 'Tajikistan'],
            'Uzbekistan': ['Turkmenistan', 'Tajikistan'],
            'Tajikistan': ['Turkmenistan', 'Uzbekistan'],
            'Nepal': ['Bangladesh', 'Myanmar'],
            'Myanmar': ['Bangladesh', 'Nepal', "Lao People's Democratic Republic", 'Cambodia'],
            'Cambodia': ['Myanmar', "Lao People's Democratic Republic", 'Singapore'],
            "Lao People's Democratic Republic": ['Myanmar', 'Cambodia'],

            # --- EUROPE HUB ---
            'Germany': ['United Arab Emirates', 'Belgium', 'Poland', 'Czech Republic', 'Denmark', 'Sweden', 'Netherlands'],
            'Belgium': ['Germany', 'Ireland', 'Netherlands', 'Poland'],
            'Ireland': ['Belgium', 'Portugal', 'Brazil'],
            'Sweden': ['Germany', 'Finland', 'Estonia', 'Denmark', 'Poland'],
            'Portugal': ['Ireland', 'Brazil', 'Morocco'],
            'Poland': ['Germany', 'Belgium', 'Sweden', 'Czech Republic', 'Hungary'],
            'Czech Republic': ['Germany', 'Poland', 'Hungary', 'Slovakia (Slovak Republic)'],
            'Hungary': ['Poland', 'Czech Republic', 'Serbia', 'Slovenia', 'Montenegro'],
            'Denmark': ['Germany', 'Sweden', 'Finland'],
            'Finland': ['Sweden', 'Denmark', 'Estonia'],
            'Estonia': ['Sweden', 'Finland'],
            'Netherlands': ['Germany', 'Belgium'],
            'Serbia': ['Hungary', 'Montenegro', 'Bulgaria'],
            'Montenegro': ['Hungary', 'Serbia'],
            'Slovenia': ['Hungary'],
            'Bulgaria': ['Serbia'],
            'Slovakia (Slovak Republic)': ['Czech Republic', 'Hungary'],
            'Cyprus': ['Egypt', 'Israel'],
            'Israel': ['Cyprus', 'Egypt'],
            'Malta': ['Egypt'],
            'Monaco': ['Belgium'],
            'Liechtenstein': ['Germany'],
            'San Marino': ['Hungary'],

            # --- EAST ASIA & PACIFIC HUB ---
            'Japan': ['Korea', 'Philippines', 'Guam', 'Hong Kong'],
            'Korea': ['Japan', 'Philippines', 'Hong Kong'],
            'Philippines': ['Japan', 'Korea', 'Palau', 'Singapore', 'Hong Kong'],
            'Hong Kong': ['Japan', 'Korea', 'Philippines', 'Macao', 'Singapore'],
            'Macao': ['Hong Kong', 'Philippines'],
            'Singapore': ['Philippines', 'Hong Kong', 'Cambodia'],
            'Guam': ['Japan', 'Palau', 'Micronesia', 'Northern Mariana Islands'],
            'Palau': ['Philippines', 'Guam', 'Micronesia'],
            'Micronesia': ['Guam', 'Palau', 'Marshall Islands'],
            'Marshall Islands': ['Micronesia', 'Kiribati'],
            'Kiribati': ['Marshall Islands', 'Fiji', 'Tuvalu'],
            'Fiji': ['Kiribati', 'Tonga', 'New Caledonia', 'Tuvalu'],
            'Tonga': ['Fiji', 'American Samoa'],
            'Tuvalu': ['Fiji', 'Kiribati'],
            'American Samoa': ['Tonga', 'French Polynesia'],
            'French Polynesia': ['American Samoa', 'New Caledonia'],
            'New Caledonia': ['Fiji', 'French Polynesia', 'Papua New Guinea'],
            'Papua New Guinea': ['New Caledonia'],
            'Northern Mariana Islands': ['Guam'],

            # --- AFRICA HUB ---
            'Egypt': ['Saudi Arabia', 'United Arab Emirates', 'Ethiopia', 'Morocco', 'Kenya', 'Nigeria', 'Cyprus', 'Israel', 'Malta'],
            'Ethiopia': ['Egypt', 'Kenya', 'Saudi Arabia', 'Djibouti'],
            'Kenya': ['Ethiopia', 'Nigeria', 'South Africa', 'Egypt', 'Rwanda', 'Mozambique'],
            'Nigeria': ['Kenya', 'Togo', 'Egypt', 'Morocco', 'Mali', 'Chad', 'Congo', 'Gabon'],
            'South Africa': ['Kenya', 'Mozambique', 'Namibia', 'Lesotho', 'Zimbabwe'],
            'Morocco': ['Portugal', 'Egypt', 'Mauritania', 'Mali', 'Nigeria'],
            'Djibouti': ['Ethiopia'],
            'Rwanda': ['Kenya', 'Congo'],
            'Togo': ['Nigeria', 'Burkina Faso', 'Mali', 'Gabon'],
            'Mali': ['Nigeria', 'Morocco', 'Mauritania', 'Burkina Faso', 'Togo'],
            'Mauritania': ['Morocco', 'Mali'],
            'Burkina Faso': ['Mali', 'Togo'],
            'Chad': ['Nigeria', 'Congo', 'Gabon'],
            'Congo': ['Nigeria', 'Chad', 'Gabon', 'Rwanda'],
            'Gabon': ['Nigeria', 'Togo', 'Congo', 'Chad', 'Sao Tome and Principe'],
            'Sao Tome and Principe': ['Gabon'],
            'Mozambique': ['South Africa', 'Kenya', 'Zimbabwe', 'Mauritius', 'Reunion', 'Mayotte'],
            'Namibia': ['South Africa'],
            'Lesotho': ['South Africa'],
            'Zimbabwe': ['South Africa', 'Mozambique'],
            'Mauritius': ['Mozambique', 'Reunion', 'Mayotte'],
            'Reunion': ['Mozambique', 'Mauritius', 'Mayotte'],
            'Mayotte': ['Mozambique', 'Mauritius', 'Reunion'],
            'Liberia': ['Guinea-Bissau'],
            'Guinea-Bissau': ['Liberia'],

            # --- AMERICAS HUB ---
            'Brazil': ['Portugal', 'Colombia', 'Peru', 'Suriname', 'Mexico', 'French Guiana', 'Guyana', 'Ireland'],
            'Colombia': ['Brazil', 'Ecuador', 'Peru', 'Mexico'],
            'Mexico': ['Brazil', 'Colombia', 'Cuba', 'El Salvador'],
            'Cuba': ['Mexico', 'Bahamas', 'Dominican Republic', 'Dominica'],
            'Peru': ['Brazil', 'Colombia', 'Ecuador', 'Chile'],
            'Ecuador': ['Colombia', 'Peru'],
            'Chile': ['Peru', 'Falkland Islands (Malvinas)'],
            'Bahamas': ['Cuba', 'Dominican Republic'],
            'Dominican Republic': ['Cuba', 'Bahamas', 'Barbados', 'Dominica', 'Grenada'],
            'Barbados': ['Dominican Republic', 'Grenada', 'Antigua and Barbuda', 'Saint Lucia'],
            'Dominica': ['Cuba', 'Dominican Republic', 'Guadeloupe', 'Martinique'],
            'Grenada': ['Dominican Republic', 'Barbados', 'Saint Vincent and the Grenadines'],
            'Antigua and Barbuda': ['Barbados', 'Saint Kitts and Nevis', 'Montserrat'],
            'Saint Kitts and Nevis': ['Antigua and Barbuda'],
            'Saint Lucia': ['Barbados', 'Saint Vincent and the Grenadines', 'Martinique'],
            'Saint Vincent and the Grenadines': ['Grenada', 'Saint Lucia'],
            'Guadeloupe': ['Dominica', 'Martinique'],
            'Martinique': ['Dominica', 'Guadeloupe', 'Saint Lucia'],
            'Montserrat': ['Antigua and Barbuda'],
            'Suriname': ['Brazil', 'French Guiana', 'Guyana'],
            'French Guiana': ['Brazil', 'Suriname'],
            'Guyana': ['Brazil', 'Suriname'],
            'El Salvador': ['Mexico'],
            'Aruba': ['Colombia'],
            'Falkland Islands (Malvinas)': ['Chile'],
            'Saint Pierre and Miquelon': ['Greenland'],
            'Greenland': ['Denmark', 'Saint Pierre and Miquelon'],

            # --- REMOTE/ISLAND TERRITORIES ---
            'Wallis and Futuna': ['Fiji'],
            'Pitcairn Islands': ['French Polynesia'],
            'Saint Helena': ['Namibia'],
            'Saint Barthelemy': ['Guadeloupe'],
            'Cocos (Keeling) Islands': ['Christmas Island'],
            'Christmas Island': ['Cocos (Keeling) Islands', 'Singapore'],
            'Isle of Man': ['Ireland'],
            'Palestinian Territory': ['Israel'],
            'Syrian Arab Republic': ['Cyprus'],
            'Antarctica (the territory South of 60 deg S)': ['Chile'],
            'South Georgia and the South Sandwich Islands': ['Falkland Islands (Malvinas)']
        }
        
        # Validate that returned connections are in dataset
        result = connections.get(country, [])
        valid_connections = [c for c in result if c in REGION_MAP]
        return valid_connections