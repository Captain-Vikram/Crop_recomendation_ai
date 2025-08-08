def format_data_for_ai(soil_data, weather_data, air_quality_data, user_goal, prefer_native):
    """
    Format all environmental data into a structured format for AI processing
    """
    formatted_data = {
        # Location info
        'location': weather_data.get('location', 'India'),
        
        # Soil information
        'soil_ph': soil_data.get('ph', 6.5),
        'soil_texture': soil_data.get('texture', 'clay loam'),
        'soil_organic_carbon': soil_data.get('organic_carbon', 1.8),
        
        # Climate information
        'temperature': weather_data.get('temperature', 27.5),
        'humidity': weather_data.get('humidity', 65),
        'rainfall': weather_data.get('rainfall', 1000),
        'climate_type': weather_data.get('climate_type', 'tropical'),
        
        # Air quality information
        'aqi': air_quality_data.get('aqi', 3),
        'pm2_5': air_quality_data.get('pm2_5', 35),
        
        # User preferences
        'user_goal': user_goal,
        'prefer_native': prefer_native,
        
        # Data status
        'data_status': {
            'soil': soil_data.get('status', 'unknown'),
            'weather': weather_data.get('status', 'unknown'),
            'air_quality': air_quality_data.get('status', 'unknown')
        }
    }
    
    return formatted_data

def validate_environmental_data(data):
    """
    Validate and clean environmental data
    """
    # Validate pH range (4-9 for soil)
    if data.get('soil_ph'):
        data['soil_ph'] = max(4.0, min(9.0, float(data['soil_ph'])))
    
    # Validate temperature range (-10 to 50°C)
    if data.get('temperature'):
        data['temperature'] = max(-10, min(50, float(data['temperature'])))
    
    # Validate humidity (0-100%)
    if data.get('humidity'):
        data['humidity'] = max(0, min(100, float(data['humidity'])))
    
    # Validate AQI (1-5 scale)
    if data.get('aqi'):
        data['aqi'] = max(1, min(5, int(data['aqi'])))
    
    return data

def get_data_quality_summary(data):
    """
    Provide a summary of data quality for user information
    """
    status = data.get('data_status', {})
    
    quality_info = {
        'overall_quality': 'good',
        'issues': [],
        'recommendations': []
    }
    
    # Check data sources
    if status.get('soil') == 'default_values':
        quality_info['issues'].append('Using default soil data')
        quality_info['recommendations'].append('Consider soil testing for more accurate results')
    
    if status.get('weather') == 'default_values':
        quality_info['issues'].append('Using default weather data')
        quality_info['recommendations'].append('Check internet connection for real-time weather')
    
    if status.get('air_quality') == 'default_values':
        quality_info['issues'].append('Using default air quality data')
    
    # Overall quality assessment
    if len(quality_info['issues']) > 2:
        quality_info['overall_quality'] = 'poor'
    elif len(quality_info['issues']) > 0:
        quality_info['overall_quality'] = 'fair'
    
    return quality_info

def create_environmental_summary(data):
    """
    Create a human-readable summary of environmental conditions
    """
    summary = []
    
    # Location
    summary.append(f"📍 Location: {data.get('location', 'India')}")
    
    # Soil conditions
    ph = data.get('soil_ph', 6.5)
    ph_desc = get_ph_description(ph)
    summary.append(f"🌱 Soil: {data.get('soil_texture', 'clay loam')}, pH {ph} ({ph_desc})")
    
    # Climate
    temp = data.get('temperature', 27.5)
    climate = data.get('climate_type', 'tropical')
    summary.append(f"🌡️ Climate: {climate.title()}, {temp}°C, {data.get('humidity', 65)}% humidity")
    
    # Rainfall
    rainfall = data.get('rainfall', 1000)
    rainfall_desc = get_rainfall_description(rainfall)
    summary.append(f"🌧️ Rainfall: {rainfall}mm/year ({rainfall_desc})")
    
    # Air quality
    aqi = data.get('aqi', 3)
    aqi_desc = get_aqi_description(aqi)
    summary.append(f"💨 Air Quality: {aqi_desc} (AQI {aqi}/5)")
    
    return summary

def get_ph_description(ph):
    """Get descriptive text for pH values"""
    if ph < 5.5:
        return "acidic"
    elif ph < 6.5:
        return "slightly acidic"
    elif ph < 7.5:
        return "neutral"
    elif ph < 8.5:
        return "slightly alkaline"
    else:
        return "alkaline"

def get_rainfall_description(rainfall):
    """Get descriptive text for rainfall amounts"""
    if rainfall < 600:
        return "low rainfall"
    elif rainfall < 1200:
        return "moderate rainfall"
    elif rainfall < 2000:
        return "high rainfall"
    else:
        return "very high rainfall"

def get_aqi_description(aqi):
    """Get descriptive text for AQI values"""
    aqi_descriptions = {
        1: "Good",
        2: "Fair", 
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    return aqi_descriptions.get(aqi, "Unknown")


def format_data_for_gemini(location, processed_data, user_goal, prefer_native):
    formatted_data = {
        "location": location,
        "soil_ph": processed_data["soil_ph"],
        "soil_texture": processed_data["soil_texture"],
        "organic_carbon": processed_data["organic_carbon"],
        "climate": "tropical wet and dry",  # Placeholder, can be adjusted based on user input
        "rainfall": processed_data["rainfall"],
        "temperature": processed_data["temperature"],
        "aqi": processed_data["aqi"],
        "pm2_5": processed_data["pm2_5"],
        "available_space": "roadside",  # Placeholder, can be adjusted based on user input
        "user_goal": user_goal,
        "prefer_native": prefer_native,
    }
    return formatted_data

def convert_area_to_square_meters(area_text):
    """
    Convert various area units to square meters for standardization
    
    Args:
        area_text (str): Text containing area with units like "2 acres", "0.5 hectare", "100 sq ft"
    
    Returns:
        float: Area in square meters, or 0 if conversion fails
    """
    if not area_text or not isinstance(area_text, str):
        return 0.0
    
    import re
    
    # Clean the text and extract number and unit
    text = area_text.lower().strip()
    
    # Conversion factors to square meters
    conversions = {
        # Metric
        'sq m': 1,
        'square meter': 1,
        'square metre': 1,
        'm2': 1,
        'm²': 1,
        
        # Imperial/US
        'sq ft': 0.092903,
        'square feet': 0.092903,
        'square foot': 0.092903,
        'ft2': 0.092903,
        'ft²': 0.092903,
        
        'sq yd': 0.836127,
        'square yard': 0.836127,
        'yard': 0.836127,
        'yd2': 0.836127,
        'yd²': 0.836127,
        
        # Large units
        'acre': 4046.86,
        'acres': 4046.86,
        'hectare': 10000,
        'hectares': 10000,
        'ha': 10000,
        
        # Indian units
        'bigha': 2529.29,  # Standard bigha (varies by region)
        'bighas': 2529.29,
        'katha': 338.96,   # Standard katha
        'kathas': 338.96,
        'gunda': 100.84,   # Standard gunda
        'gundas': 100.84
    }
    
    # Extract number and unit using regex
    pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z\²²\s]+)'
    match = re.search(pattern, text)
    
    if match:
        try:
            number = float(match.group(1))
            unit = match.group(2).strip()
            
            # Find matching unit in conversions (check longer matches first)
            sorted_units = sorted(conversions.items(), key=lambda x: len(x[0]), reverse=True)
            for unit_key, factor in sorted_units:
                if unit_key in unit:
                    return number * factor
            
            # If no unit found, assume square meters
            return number
            
        except (ValueError, AttributeError):
            pass
    
    # Try to extract just a number (assume square meters)
    number_match = re.search(r'(\d+(?:\.\d+)?)', text)
    if number_match:
        try:
            return float(number_match.group(1))
        except ValueError:
            pass
    
    return 0.0

def get_space_type_suggestions(location_type):
    """
    Get plant size and type suggestions based on location type
    
    Args:
        location_type (str): Description of planting location
    
    Returns:
        dict: Suggestions for plant characteristics
    """
    if not location_type:
        return {}
    
    location_lower = location_type.lower().strip()
    
    suggestions = {
        'max_height': '10 meters',
        'container_suitable': True,
        'space_category': 'general',
        'plant_types': ['Any suitable plants'],
        'special_notes': []
    }
    
    # Indoor/small spaces
    if any(word in location_lower for word in ['window', 'pane', 'sill', 'indoor']):
        suggestions.update({
            'max_height': '0.5 meters',
            'container_suitable': True,
            'space_category': 'indoor_small',
            'plant_types': ['Small herbs', 'Succulents', 'Small flowering plants'],
            'special_notes': ['Ensure adequate sunlight', 'Use good quality potting soil']
        })
    
    # Semi-outdoor medium spaces
    elif any(word in location_lower for word in ['balcony', 'terrace', 'patio', 'veranda']):
        suggestions.update({
            'max_height': '2 meters',
            'container_suitable': True,
            'space_category': 'semi_outdoor_medium',
            'plant_types': ['Medium shrubs', 'Dwarf fruit trees', 'Flowering plants'],
            'special_notes': ['Consider wind exposure', 'Ensure proper drainage in pots']
        })
    
    # Outdoor garden spaces
    elif any(word in location_lower for word in ['backyard', 'garden', 'yard', 'compound']):
        suggestions.update({
            'max_height': '5 meters',
            'container_suitable': False,
            'space_category': 'outdoor_medium',
            'plant_types': ['Medium trees', 'Large shrubs', 'Fruit trees'],
            'special_notes': ['Direct ground planting recommended', 'Consider mature size']
        })
    
    # Large farming areas
    elif any(word in location_lower for word in ['farmland', 'field', 'farm', 'acre', 'hectare']):
        suggestions.update({
            'max_height': '15 meters',
            'container_suitable': False,
            'space_category': 'outdoor_large',
            'plant_types': ['Large trees', 'Commercial crops', 'Timber trees'],
            'special_notes': ['Commercial/large-scale planting suitable', 'Consider spacing for machinery access']
        })
    
    return suggestions