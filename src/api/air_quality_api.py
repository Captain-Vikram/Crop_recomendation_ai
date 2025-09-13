from .weather_api import get_weather_data

def get_air_quality_data(lat, lon):
    """
    Get air quality data from OpenWeatherMap (included in weather data)
    """
    weather_data = get_weather_data(lat, lon)
    
    return {
        'aqi': weather_data.get('aqi', 3),
        'pm2_5': weather_data.get('pm2_5', 35),
        'status': weather_data.get('status', 'success')
    }