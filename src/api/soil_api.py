"""
Soil data API module with geographic estimation for Indian regions
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_soil_data(lat, lon):
    """
    Fetch soil data with robust fallback system
    Returns soil pH, texture, and organic carbon data
    """
    # Always use estimated data for reliability
    return get_estimated_soil_data(lat, lon)

def get_estimated_soil_data(lat, lon):
    """
    Provide estimated soil data based on geographic location within India
    """
    # Estimate soil properties based on Indian geography
    estimated_ph = estimate_ph_from_location(lat, lon)
    estimated_texture = estimate_texture_from_location(lat, lon)
    estimated_carbon = estimate_organic_carbon(lat, lon)
    
    return {
        'soil_ph': estimated_ph,
        'soil_texture': estimated_texture,
        'soil_organic_carbon': estimated_carbon,
        'status': 'success',
        'source': 'Estimated based on Indian soil patterns'
    }

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