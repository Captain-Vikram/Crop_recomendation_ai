def format_data_for_ai(soil_data, weather_data, air_quality_data, prefer_native, user_preferences=None):
    """
    Format all environmental data into a structured format for AI processing
    Enhanced to prioritize user-provided data while maintaining API data for validation
    """
    formatted_data = {
        # Location info
        'location': weather_data.get('location', 'India'),
        
        # Soil information (API data with user overrides)
        'soil_ph': soil_data.get('soil_ph', 6.5),  # Fixed: use correct key from soil API
        'soil_texture': soil_data.get('soil_texture', 'clay loam'),
        'soil_organic_carbon': soil_data.get('soil_organic_carbon', 1.8),
        
        # Climate information (API data)
        'temperature': weather_data.get('temperature', 27.5),
        'humidity': weather_data.get('humidity', 65),
        'rainfall': weather_data.get('rainfall', 1000),
        'climate_type': weather_data.get('climate_type', 'tropical'),
        
        # Air quality information (API data)
        'aqi': air_quality_data.get('aqi', 75),  # Use calculated AQI (0-500 scale)
        'aqi_rating': air_quality_data.get('aqi_rating', 3),  # Keep 1-5 rating for compatibility
        'pm2_5': air_quality_data.get('pm2_5', 35),
        
        # User preferences
        'prefer_native': prefer_native,
        
        # Data status tracking
        'data_status': {
            'soil': soil_data.get('status', 'unknown'),
            'weather': weather_data.get('status', 'unknown'),
            'air_quality': air_quality_data.get('status', 'unknown')
        },
        
        # Store original API values for comparison/validation
        'api_data': {
            'soil_texture_api': soil_data.get('texture', 'clay loam'),
            'rainfall_api': weather_data.get('rainfall', 1000),
            'temperature_api': weather_data.get('temperature', 27.5)
        }
    }
    
    # Enhance with user preferences if provided
    if user_preferences:
        formatted_data = enhance_with_user_preferences(formatted_data, user_preferences)
    
    return formatted_data

def enhance_with_user_preferences(formatted_data, user_preferences):
    """
    Enhance environmental data with user-provided preferences
    Prioritizes user input while keeping API data for validation and context
    """
    # Track user overrides for display purposes
    user_overrides = []
    
    # Soil type override with validation
    if user_preferences.get('soil_type_input', '').strip():
        user_soil = user_preferences['soil_type_input'].strip()
        api_soil = formatted_data.get('api_data', {}).get('soil_texture_api', 'clay loam')
        
        formatted_data['soil_texture'] = user_soil
        formatted_data['soil_texture_source'] = 'user_input'
        formatted_data['soil_texture_note'] = f"User specified: {user_soil} (API suggested: {api_soil})"
        user_overrides.append(f"Soil: {user_soil}")
    
    # Water availability override with intelligent mapping
    if user_preferences.get('water_availability', 'Auto-detect') != 'Auto-detect':
        water_pref = user_preferences['water_availability']
        api_rainfall = formatted_data.get('api_data', {}).get('rainfall_api', 1000)
        
        # Map user preference to rainfall values (mm/year)
        water_mapping = {
            'Low': 400,     # Arid/semi-arid conditions
            'Medium': 1000,  # Moderate rainfall
            'High': 1800    # High rainfall regions
        }
        
        user_rainfall = water_mapping.get(water_pref, 1000)
        
        # Use user preference if API data seems unrealistic or user strongly disagrees
        if api_rainfall < 100 or api_rainfall > 4000 or abs(api_rainfall - user_rainfall) > 800:
            formatted_data['rainfall'] = user_rainfall
            formatted_data['rainfall_source'] = 'user_preference'
            formatted_data['rainfall_note'] = f"Using user preference ({water_pref}: {user_rainfall}mm) - API value ({api_rainfall}mm) seemed unrealistic or very different"
            user_overrides.append(f"Water: {water_pref} ({user_rainfall}mm)")
        else:
            # Keep API value but note user preference for AI context
            formatted_data['user_water_preference'] = water_pref
            formatted_data['user_preferred_rainfall'] = user_rainfall
            formatted_data['rainfall_note'] = f"Using API data ({api_rainfall}mm) as it aligns with {water_pref} conditions"
    
    # Space and location constraints
    if user_preferences.get('space_availability', 0) > 0:
        formatted_data['available_space'] = user_preferences['space_availability']
        formatted_data['space_source'] = 'user_input'
        user_overrides.append(f"Space: {user_preferences['space_availability']} m²")
    
    # Alternative area input with unit conversion
    if user_preferences.get('area_with_units', '').strip():
        converted_area = convert_area_to_square_meters(user_preferences['area_with_units'])
        if converted_area > 0:
            formatted_data['available_space'] = converted_area
            formatted_data['space_source'] = 'user_input_converted'
            formatted_data['area_conversion'] = f"{user_preferences['area_with_units']} → {converted_area} m²"
            user_overrides.append(f"Space: {user_preferences['area_with_units']} ({converted_area} m²)")
    
    # Location type constraints
    if user_preferences.get('space_location_type', '').strip():
        location_type = user_preferences['space_location_type'].strip()
        formatted_data['space_location_type'] = location_type
        
        # Add automatic space constraints based on location type
        space_suggestions = get_space_type_suggestions(location_type)
        if space_suggestions:
            formatted_data['location_constraints'] = space_suggestions
            formatted_data['max_plant_height'] = space_suggestions.get('max_height', '10 meters')
            formatted_data['container_suitable'] = space_suggestions.get('container_suitable', True)
            formatted_data['space_category'] = space_suggestions.get('space_category', 'general')
        
        user_overrides.append(f"Location: {location_type}")
    
    # Budget preference
    if user_preferences.get('budget_preference', 'Auto-suggest') != 'Auto-suggest':
        formatted_data['budget_preference'] = user_preferences['budget_preference']
        user_overrides.append(f"Budget: {user_preferences['budget_preference']}")
    
    # Store summary of user overrides
    if user_overrides:
        formatted_data['user_customizations'] = user_overrides
        formatted_data['customization_summary'] = f"User preferences: {' | '.join(user_overrides)}"
    
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
    
    # Validate AQI (0-500 EPA scale)
    if data.get('aqi'):
        data['aqi'] = max(0, min(500, int(data['aqi'])))
    
    # Validate AQI rating (1-5 scale)
    if data.get('aqi_rating'):
        data['aqi_rating'] = max(1, min(5, int(data['aqi_rating'])))
    
    return data

def get_data_quality_summary(data):
    """
    Provide a summary of data quality for user information
    Enhanced to account for user input and data source mixing
    """
    status = data.get('data_status', {})
    
    quality_info = {
        'overall_quality': 'good',
        'issues': [],
        'recommendations': [],
        'user_contributions': []
    }
    
    # Check API data sources
    if status.get('soil') == 'default_values':
        quality_info['issues'].append('Using default soil data')
        quality_info['recommendations'].append('Consider soil testing for more accurate results')
    
    if status.get('weather') == 'default_values':
        quality_info['issues'].append('Using default weather data')
        quality_info['recommendations'].append('Check internet connection for real-time weather')
    
    if status.get('air_quality') == 'default_values':
        quality_info['issues'].append('Using default air quality data')
    
    # Account for user customizations
    user_customizations = data.get('user_customizations', [])
    if user_customizations:
        quality_info['user_contributions'] = user_customizations
        
        # Improve quality score based on user input
        if len(user_customizations) >= 3:
            quality_info['overall_quality'] = 'excellent'
        elif len(user_customizations) >= 1:
            if quality_info['overall_quality'] == 'poor':
                quality_info['overall_quality'] = 'fair'
            elif quality_info['overall_quality'] == 'fair':
                quality_info['overall_quality'] = 'good'
    
    # Overall quality assessment
    if len(quality_info['issues']) > 2 and not user_customizations:
        quality_info['overall_quality'] = 'poor'
    elif len(quality_info['issues']) > 0 and not user_customizations:
        quality_info['overall_quality'] = 'fair'
    
    # Add specific notes about data sources
    if data.get('soil_texture_source') == 'user_input':
        quality_info['user_contributions'].append('User-specified soil type improves accuracy')
    
    if data.get('rainfall_source') == 'user_preference':
        quality_info['user_contributions'].append('User water preference overrides API data')
    
    if data.get('space_source') in ['user_input', 'user_input_converted']:
        quality_info['user_contributions'].append('User-defined space constraints improve relevance')
    
    return quality_info

def create_environmental_summary(data):
    """
    Create a human-readable summary of environmental conditions
    Enhanced to show user customizations and API vs user data
    """
    summary = []
    
    # Location
    summary.append(f"📍 Location: {data.get('location', 'India')}")
    
    # Soil conditions with source indication
    ph = data.get('soil_ph', 6.5)
    ph_desc = get_ph_description(ph)
    soil_texture = data.get('soil_texture', 'clay loam')
    soil_source = data.get('soil_texture_source', 'api')
    
    if soil_source == 'user_input':
        summary.append(f"🌱 Soil: {soil_texture} (👤 user-specified), pH {ph} ({ph_desc})")
    else:
        summary.append(f"🌱 Soil: {soil_texture}, pH {ph} ({ph_desc})")
    
    # Climate
    temp = data.get('temperature', 27.5)
    climate = data.get('climate_type', 'tropical')
    summary.append(f"🌡️ Climate: {climate.title()}, {temp}°C, {data.get('humidity', 65)}% humidity")
    
    # Rainfall with source indication
    rainfall = data.get('rainfall', 1000)
    rainfall_desc = get_rainfall_description(rainfall)
    rainfall_source = data.get('rainfall_source', 'api')
    
    if rainfall_source == 'user_preference':
        water_pref = data.get('user_water_preference', 'medium')
        summary.append(f"🌧️ Rainfall: {rainfall}mm/year ({rainfall_desc}) - 👤 based on {water_pref} water preference")
    elif data.get('user_water_preference'):
        summary.append(f"🌧️ Rainfall: {rainfall}mm/year ({rainfall_desc}) - matches {data.get('user_water_preference')} preference")
    else:
        summary.append(f"🌧️ Rainfall: {rainfall}mm/year ({rainfall_desc})")
    
    # Air quality
    aqi = data.get('aqi', 75)
    aqi_rating = data.get('aqi_rating', 3)
    aqi_desc = get_aqi_description(aqi_rating)  # Use rating for description
    summary.append(f"💨 Air Quality: AQI {aqi} ({aqi_desc} - {aqi_rating}/5)")
    
    # Space availability if specified
    if data.get('available_space'):
        space = data.get('available_space')
        space_source = data.get('space_source', 'calculated')
        
        if space_source == 'user_input':
            summary.append(f"📐 Available Space: {space:,.0f} m² (👤 user-specified)")
        elif space_source == 'user_input_converted':
            conversion = data.get('area_conversion', '')
            summary.append(f"📐 Available Space: {space:,.0f} m² (👤 {conversion})")
        else:
            summary.append(f"📐 Available Space: {space:,.0f} m²")
    
    # Location type constraints
    if data.get('space_location_type'):
        location_type = data.get('space_location_type')
        space_category = data.get('space_category', 'general')
        summary.append(f"🏠 Planting Location: {location_type} (👤 user-specified)")
        
        # Add constraint information
        if data.get('max_plant_height'):
            summary.append(f"📏 Height Limit: {data.get('max_plant_height')} (based on location type)")
    
    # User customizations summary
    if data.get('user_customizations'):
        customizations = data.get('user_customizations', [])
        summary.append(f"⚙️ Customizations: {' | '.join(customizations)}")
    
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