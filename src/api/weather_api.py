import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_weather_data(lat, lon):
    """
    Fetch weather and air quality data from OpenWeatherMap
    Returns temperature, rainfall, humidity, and air pollution data
    """
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    
    if not api_key:
        return get_default_weather_data()
    
    try:
        # Get current weather data
        weather_url = "http://api.openweathermap.org/data/2.5/weather"
        weather_params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'
        }
        
        weather_response = requests.get(weather_url, params=weather_params, timeout=10)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # Get air pollution data (using same API key)
        air_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        air_params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key
        }
        
        air_response = requests.get(air_url, params=air_params, timeout=10)
        air_response.raise_for_status()
        air_data = air_response.json()
        
        # Extract relevant data
        rainfall_value = get_rainfall_estimate(lat, lon)
        climate_type_value = get_climate_type(lat, lon)
        
        climate_info = {
            'temperature': weather_data['main']['temp'],
            'humidity': weather_data['main']['humidity'],
            'rainfall': rainfall_value,
            'climate_type': climate_type_value,
            'aqi': air_data['list'][0]['main']['aqi'],
            'pm2_5': air_data['list'][0]['components'].get('pm2_5', 0),
            'location': f"{weather_data.get('name', 'Unknown')}, India",
            'status': 'success'
        }
        
        print(f"Weather API final data: temp={climate_info['temperature']}°C, rainfall={climate_info['rainfall']}mm")
        return climate_info
        
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return get_default_weather_data()

def get_rainfall_estimate(lat=20.5937, lon=78.9629):
    """
    Get rainfall estimate using Open-Meteo API with balanced seasonal calculation
    """
    # Use longer historical period for more accurate estimation
    rain_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation&past_days=60&forecast_days=0"
    
    try:
        response = requests.get(rain_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Check if data exists and has the expected structure
            if 'hourly' in data and 'precipitation' in data['hourly']:
                precipitation_data = data['hourly']['precipitation']
                
                # Filter out None values and calculate total
                valid_precipitation = [p for p in precipitation_data if p is not None]
                
                if valid_precipitation and len(valid_precipitation) > 0:
                    total_rainfall_mm = sum(valid_precipitation)
                    days_of_data = len(valid_precipitation) / 24  # Convert hours to days
                    
                    if days_of_data > 0:
                        daily_average = total_rainfall_mm / days_of_data
                        annual_estimate = daily_average * 365
                        
                        # Apply realistic bounds for Indian rainfall based on geographic location
                        # Coastal areas: 1000-4000mm, Interior: 500-2000mm, Arid: 100-500mm
                        if lat < 12 or (lat < 20 and (lon < 73 or lon > 85)):  # Southern/coastal regions
                            annual_estimate = max(800, min(3500, annual_estimate))
                        elif lat > 28:  # Northern regions
                            annual_estimate = max(300, min(1500, annual_estimate))
                        else:  # Central India
                            annual_estimate = max(500, min(2500, annual_estimate))
                        
                        print(f"Rainfall calculation: {total_rainfall_mm:.1f}mm over {days_of_data:.1f} days → {annual_estimate:.1f}mm/year")
                        return round(annual_estimate, 1)
                    else:
                        print("No valid time period data")
                        return 800
                else:
                    print("No valid precipitation data found")
                    return 800  # Default fallback
            else:
                print("Invalid data structure from precipitation API")
                return 800
        else:
            print(f"Precipitation API returned status code: {response.status_code}")
            return 800
            
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching precipitation data: {e}")
        return 800
    except Exception as e:
        print(f"Error processing precipitation data: {e}")
        return 800

def get_climate_type(lat=20.5937, lon=78.9629):
    """
    Determine climate type using current weather data and geographic location
    """
    try:
        # Use current weather endpoint for temperature data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m&daily=temperature_2m_max,temperature_2m_min&forecast_days=1"
        
        response = requests.get(weather_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Get current temperature or use daily average
            if 'current' in data and 'temperature_2m' in data['current']:
                current_temp = data['current']['temperature_2m']
                annual_temp = current_temp  # Use current as estimate
            elif 'daily' in data and 'temperature_2m_max' in data['daily']:
                max_temp = data['daily']['temperature_2m_max'][0] if data['daily']['temperature_2m_max'] else 25
                min_temp = data['daily']['temperature_2m_min'][0] if data['daily']['temperature_2m_min'] else 20
                annual_temp = (max_temp + min_temp) / 2
            else:
                print("No temperature data found, using fallback")
                annual_temp = 24.1  # Fallback
        else:
            print(f"Climate API returned status code: {response.status_code}")
            annual_temp = 24.1  # Fallback
            
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching climate data: {e}")
        annual_temp = 24.1
    except Exception as e:
        print(f"Error processing climate data: {e}")
        annual_temp = 24.1

    # Enhanced Köppen-like classification for India based on temperature and latitude
    rainfall_estimate = get_rainfall_estimate(lat, lon)  # Get rainfall for better classification
    
    print(f"Climate calculation: lat={lat}, temp={annual_temp}°C, rainfall={rainfall_estimate}mm")
    
    if lat > 32:
        # Northern mountainous regions
        if annual_temp < 10:
            return "Alpine/Cold Desert"
        elif annual_temp < 18:
            return "Temperate Continental"
        else:
            return "Subtropical Highland"
    elif lat > 26:
        # Northern plains
        if rainfall_estimate < 500:
            return "Arid/Desert"
        elif rainfall_estimate < 1000:
            return "Semi-Arid"
        else:
            return "Subtropical Humid"
    elif lat > 20:
        # Central India (including Wardha region)
        if rainfall_estimate < 600:
            return "Semi-Arid Hot"
        elif rainfall_estimate < 1200:
            return "Tropical Dry"
        else:
            return "Tropical Wet-Dry"
    else:
        # Southern India
        if rainfall_estimate > 2000:
            return "Tropical Monsoon"
        elif rainfall_estimate > 1000:
            return "Tropical Wet-Dry"
        else:
            return "Tropical Semi-Arid"

def get_default_weather_data():
    """
    Return default weather data for India
    """
    return {
        'temperature': 27.5,
        'humidity': 65,
        'rainfall': 1000,
        'climate_type': 'tropical',
        'aqi': 3,  # Moderate
        'pm2_5': 35,
        'location': 'India',
        'status': 'default_values'
    }

# Add a test function to verify the data
def test_weather_functions(lat=20.5937, lon=78.9629):
    """
    Test function to verify rainfall and climate functions are working
    """
    print(f"Testing weather functions for coordinates: {lat}, {lon}")
    
    print("\n1. Testing rainfall estimation...")
    rainfall = get_rainfall_estimate(lat, lon)
    print(f"   Rainfall estimate: {rainfall} mm/year")
    
    print("\n2. Testing climate type determination...")
    climate = get_climate_type(lat, lon)
    print(f"   Climate type: {climate}")
    
    print("\n3. Testing full weather data...")
    weather_data = get_weather_data(lat, lon)
    print(f"   Full weather data: {weather_data}")
    
    return rainfall, climate, weather_data