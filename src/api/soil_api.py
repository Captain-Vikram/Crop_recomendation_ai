"""
Soil data API module with SoilGrids REST API integration and geographic estimation fallback
"""
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

def get_soil_data(lat, lon):
    """
    Fetch soil data from SoilGrids API with robust fallback system
    Returns soil pH, texture, and organic carbon data
    """
    try:
        # First attempt to get real data from SoilGrids API
        api_data = get_soilgrids_data(lat, lon)
        if api_data and api_data.get('status') == 'success':
            print(f"✅ Successfully retrieved soil data from SoilGrids API")
            return api_data
        else:
            print(f"⚠️ SoilGrids API has no data for location ({lat}, {lon}), using Indian soil estimation")
            # Enhance estimated data with API attempt info
            estimated_data = get_estimated_soil_data(lat, lon)
            estimated_data['api_attempted'] = True
            estimated_data['api_status'] = 'no_data_available'
            return estimated_data
    except Exception as e:
        print(f"❌ Error fetching soil data from API: {e}")
        estimated_data = get_estimated_soil_data(lat, lon)
        estimated_data['api_attempted'] = True
        estimated_data['api_error'] = str(e)
        return estimated_data

def get_soilgrids_data(lat, lon):
    """
    Fetch soil data from SoilGrids REST API
    """
    try:
        # SoilGrids API endpoint for soil properties
        url = f"{os.getenv('SOILGRIDS_BASE_URL')}/properties/query"

        # Parameters for the API call - request more properties
        params = {
            'lon': lon,
            'lat': lat,
            'property': ['phh2o', 'clay', 'sand', 'silt', 'soc', 'bdod'],  # Added bulk density
            'depth': ['0-5cm', '5-15cm'],  # Multiple depths for better coverage
            'value': ['mean', 'Q0.05', 'Q0.95']  # Get mean and uncertainty range
        }
        
        # Make API request with better headers
        headers = {
            'User-Agent': 'CropRecommendationBot/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return parse_soilgrids_response(data, lat, lon)
        elif response.status_code == 422:
            print(f"SoilGrids validation error: coordinates might be out of bounds")
            return None
        else:
            print(f"SoilGrids API returned status code: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error parsing SoilGrids response: {e}")
        return None

def parse_soilgrids_response(data, lat, lon):
    """
    Parse SoilGrids API response and extract relevant soil properties
    """
    try:
        if 'properties' not in data or 'layers' not in data['properties']:
            return None
        
        layers = data['properties']['layers']
        
        # Extract soil properties with multiple depth fallbacks
        ph_data = extract_property_value(layers, 'phh2o', conversion_factor=10.0)
        clay_percent = extract_property_value(layers, 'clay', conversion_factor=10.0)
        sand_percent = extract_property_value(layers, 'sand', conversion_factor=10.0)
        silt_percent = extract_property_value(layers, 'silt', conversion_factor=10.0)
        soc_data = extract_property_value(layers, 'soc', conversion_factor=10.0)
        bulk_density = extract_property_value(layers, 'bdod', conversion_factor=100.0)
        
        # Determine soil texture from percentages
        soil_texture = determine_soil_texture(clay_percent, sand_percent, silt_percent)
        
        # Check if we got meaningful data from the API
        has_real_data = any([
            ph_data is not None and ph_data > 0,
            soil_texture is not None,
            soc_data is not None and soc_data > 0
        ])
        
        if not has_real_data:
            print(f"SoilGrids returned null/zero values - no soil data available for this location")
            return None
        
        print(f"✅ SoilGrids provided data: pH={ph_data}, texture={soil_texture}, SOC={soc_data}")
        
        return {
            'soil_ph': ph_data if ph_data is not None and ph_data > 0 else 6.5,
            'soil_texture': soil_texture if soil_texture else 'clay loam',
            'soil_organic_carbon': soc_data if soc_data is not None and soc_data > 0 else 1.5,
            'clay_percent': clay_percent,
            'sand_percent': sand_percent,
            'silt_percent': silt_percent,
            'bulk_density': bulk_density,
            'status': 'success',
            'source': f'SoilGrids API v2.0 (lat: {lat}, lon: {lon})',
            'data_quality': 'high',
            'api_data_available': {
                'ph': ph_data is not None and ph_data > 0,
                'texture': soil_texture is not None,
                'organic_carbon': soc_data is not None and soc_data > 0,
                'bulk_density': bulk_density is not None
            }
        }
        
    except Exception as e:
        print(f"Error parsing SoilGrids data: {e}")
        return None

def extract_property_value(layers, property_name, conversion_factor=1.0):
    """
    Extract property value from layers with fallback to different depths
    """
    for layer in layers:
        if layer['name'].startswith(property_name):
            for depth in layer.get('depths', []):
                values = depth.get('values', {})
                mean_value = values.get('mean')
                if mean_value is not None and mean_value != 0:
                    return mean_value / conversion_factor
    return None

def determine_soil_texture(clay_percent, sand_percent, silt_percent):
    """
    Determine soil texture class based on clay, sand, and silt percentages
    Using USDA soil texture triangle classification
    """
    if clay_percent is None or sand_percent is None or silt_percent is None:
        return None
    
    # USDA soil texture classification
    if clay_percent >= 40:
        return "clay"
    elif clay_percent >= 27:
        if sand_percent >= 45:
            return "sandy clay"
        else:
            return "clay loam"
    elif clay_percent >= 20:
        if sand_percent >= 45:
            return "sandy clay loam"
        elif silt_percent >= 28:
            return "silty clay loam"
        else:
            return "clay loam"
    elif clay_percent >= 7:
        if sand_percent >= 52:
            return "sandy loam"
        elif silt_percent >= 50:
            return "silt loam"
        else:
            return "loam"
    else:  # clay < 7%
        if silt_percent >= 80:
            return "silt"
        elif sand_percent >= 85:
            return "sand"
        elif sand_percent >= 70:
            return "loamy sand"
        else:
            return "sandy loam"

def get_estimated_soil_data(lat, lon):
    """
    Provide enhanced estimated soil data based on geographic location within India
    Uses detailed soil mapping and regional characteristics
    """
    # Estimate soil properties based on Indian geography
    estimated_ph = estimate_ph_from_location(lat, lon)
    estimated_texture = estimate_texture_from_location(lat, lon)
    estimated_carbon = estimate_organic_carbon(lat, lon)
    
    # Determine region for better context
    region = determine_indian_region(lat, lon)
    
    return {
        'soil_ph': estimated_ph,
        'soil_texture': estimated_texture,
        'soil_organic_carbon': estimated_carbon,
        'status': 'success',
        'source': f'Enhanced Indian soil estimation for {region}',
        'data_quality': 'estimated',
        'region': region,
        'estimation_basis': 'Indian soil survey patterns and regional characteristics',
        'clay_percent': estimate_clay_percentage(estimated_texture),
        'sand_percent': estimate_sand_percentage(estimated_texture),
        'silt_percent': estimate_silt_percentage(estimated_texture),
        'api_data_available': {
            'ph': False,
            'texture': False,
            'organic_carbon': False,
            'bulk_density': False
        }
    }

def determine_indian_region(lat, lon):
    """
    Determine the Indian region based on coordinates for better soil estimation context
    """
    if lat >= 32:
        return "Jammu & Kashmir / Ladakh"
    elif lat >= 30:
        return "Himachal Pradesh / Uttarakhand"
    elif lat >= 28:
        if lon <= 77:
            return "Punjab / Haryana / Delhi"
        else:
            return "Uttar Pradesh / Bihar"
    elif lat >= 26:
        if lon <= 74:
            return "Rajasthan"
        elif lon <= 85:
            return "Madhya Pradesh / Uttar Pradesh"
        else:
            return "West Bengal / Jharkhand"
    elif lat >= 22:
        if lon <= 72:
            return "Gujarat"
        elif lon <= 82:
            return "Maharashtra / Chhattisgarh"
        else:
            return "Odisha / West Bengal"
    elif lat >= 18:
        if lon <= 75:
            return "Maharashtra / Goa"
        elif lon <= 80:
            return "Telangana / Andhra Pradesh"
        else:
            return "Andhra Pradesh / Odisha"
    elif lat >= 12:
        if lon <= 77:
            return "Karnataka"
        else:
            return "Tamil Nadu / Andhra Pradesh"
    elif lat >= 8:
        return "Tamil Nadu / Kerala"
    else:
        return "Kerala / Southern Tamil Nadu"

def estimate_clay_percentage(texture):
    """Estimate clay percentage based on texture class"""
    texture_clay_map = {
        'clay': 45,
        'clay loam': 30,
        'sandy clay': 35,
        'sandy clay loam': 25,
        'silty clay': 45,
        'silty clay loam': 30,
        'sandy loam': 15,
        'loam': 20,
        'silt loam': 15,
        'sand': 5,
        'loamy sand': 8,
        'silt': 10
    }
    return texture_clay_map.get(texture, 25)

def estimate_sand_percentage(texture):
    """Estimate sand percentage based on texture class"""
    texture_sand_map = {
        'clay': 25,
        'clay loam': 35,
        'sandy clay': 50,
        'sandy clay loam': 60,
        'silty clay': 10,
        'silty clay loam': 15,
        'sandy loam': 65,
        'loam': 40,
        'silt loam': 25,
        'sand': 90,
        'loamy sand': 80,
        'silt': 5
    }
    return texture_sand_map.get(texture, 40)

def estimate_silt_percentage(texture):
    """Estimate silt percentage based on texture class"""
    clay = estimate_clay_percentage(texture)
    sand = estimate_sand_percentage(texture)
    return max(0, 100 - clay - sand)  # Ensure it adds up to 100%

def estimate_ph_from_location(lat, lon):
    """
    Estimate soil pH based on location within India
    Based on known soil patterns across different regions
    """
    # Northern India (high pH due to arid conditions and alkaline soils)
    if lat >= 28:
        return 7.8
    # Western India (varied, but generally alkaline due to low rainfall)
    elif lat >= 20 and lon <= 75:
        return 7.2
    # Central India (neutral to slightly alkaline - black cotton soils)
    elif lat >= 15:
        return 6.8
    # Southern India (slightly acidic due to higher rainfall and lateritic soils)
    elif lat >= 8:
        return 6.2
    # Very southern regions and coastal areas (more acidic)
    else:
        return 5.9

def estimate_texture_from_location(lat, lon):
    """
    Estimate soil texture based on location within India
    Based on known soil types across different regions
    """
    # Northern plains (alluvial soils - Indo-Gangetic plains)
    if lat >= 28:
        return "clay loam"
    # Western India (sandy and rocky soils - Rajasthan, Gujarat)
    elif lat >= 20 and lon <= 75:
        return "sandy loam"
    # Central India (black cotton soils - Deccan plateau)
    elif lat >= 15 and 75 <= lon <= 82:
        return "clay"
    # Eastern India (lateritic and alluvial)
    elif lat >= 15 and lon > 82:
        return "clay loam"
    # Southern India (lateritic and red soils)
    elif lat >= 8:
        return "clay loam"
    # Coastal areas (sandy clay)
    else:
        return "sandy clay loam"

def estimate_organic_carbon(lat, lon):
    """
    Estimate soil organic carbon based on climate and vegetation patterns
    Higher values in areas with more rainfall and vegetation
    """
    # Northern plains (moderate organic matter)
    if lat >= 28:
        return 1.2
    # Western arid regions (low organic matter)
    elif lat >= 20 and lon <= 75:
        return 0.8
    # Central India (moderate organic matter)
    elif lat >= 15:
        return 1.5
    # Southern India (higher rainfall, more vegetation)
    elif lat >= 8:
        return 2.1
    # Coastal tropical areas (highest organic matter)
    else:
        return 2.8

def get_soil_recommendations(soil_data):
    """
    Get soil improvement recommendations based on soil properties
    """
    ph = soil_data.get('soil_ph', 6.5)
    texture = soil_data.get('soil_texture', 'clay loam')
    organic_carbon = soil_data.get('soil_organic_carbon', 1.5)
    
    recommendations = []
    
    # pH recommendations
    if ph < 6.0:
        recommendations.append("Add lime to reduce soil acidity")
    elif ph > 8.0:
        recommendations.append("Add organic matter or sulfur to reduce alkalinity")
    else:
        recommendations.append("Soil pH is optimal for most plants")
    
    # Texture recommendations
    if 'sandy' in texture.lower():
        recommendations.append("Add compost to improve water retention")
    elif 'clay' in texture.lower():
        recommendations.append("Add sand and organic matter to improve drainage")
    else:
        recommendations.append("Soil texture is well-balanced")
    
    # Organic carbon recommendations
    if organic_carbon < 1.0:
        recommendations.append("Increase organic matter with compost and mulching")
    elif organic_carbon > 3.0:
        recommendations.append("Soil has excellent organic content")
    else:
        recommendations.append("Maintain current organic matter levels")
    
    return recommendations
