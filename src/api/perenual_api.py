import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_plant_details(plant_name, limit=5):
    """
    Search for plants by name and get detailed information
    """
    api_key = os.getenv('PERENUAL_API_KEY')
    
    if not api_key:
        return []
    
    try:
        # First, search for the plant
        search_url = "https://perenual.com/api/species-list"
        search_params = {
            'key': api_key,
            'q': plant_name,
            'per_page': limit
        }
        
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        
        search_data = response.json()
        plants = search_data.get('data', [])
        
        detailed_plants = []
        
        # Get detailed information for each plant
        for plant in plants[:limit]:
            plant_id = plant.get('id')
            if plant_id:
                detail = get_single_plant_detail(plant_id)
                if detail:
                    detailed_plants.append(detail)
        
        return detailed_plants
        
    except Exception as e:
        print(f"Error fetching plant details: {e}")
        return []

def get_single_plant_detail(plant_id):
    """
    Get detailed information for a single plant by ID
    """
    api_key = os.getenv('PERENUAL_API_KEY')
    
    try:
        detail_url = f"https://perenual.com/api/species/details/{plant_id}"
        detail_params = {'key': api_key}
        
        response = requests.get(detail_url, params=detail_params, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"Error fetching plant detail for ID {plant_id}: {e}")
        return None

def search_plants_by_criteria(criteria):
    """
    Search for plants based on environmental criteria
    """
    api_key = os.getenv('PERENUAL_API_KEY')
    
    if not api_key:
        return []
    
    try:
        search_url = "https://perenual.com/api/species-list"
        search_params = {'key': api_key, 'per_page': 20}
        
        # Add criteria filters
        if criteria.get('edible'):
            search_params['edible'] = 1
        
        if criteria.get('sunlight'):
            search_params['sunlight'] = criteria['sunlight']
        
        if criteria.get('watering'):
            search_params['watering'] = criteria['watering']
        
        if criteria.get('cycle'):
            search_params['cycle'] = criteria['cycle']
        
        if criteria.get('hardiness'):
            search_params['hardiness'] = criteria['hardiness']
        
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        
        return response.json().get('data', [])
        
    except Exception as e:
        print(f"Error searching plants by criteria: {e}")
        return []

def get_plant_care_guide(species_id):
    """
    Get care guide for a specific plant species
    """
    api_key = os.getenv('PERENUAL_API_KEY')
    
    if not api_key:
        return None
    
    try:
        guide_url = "https://perenual.com/api/species-care-guide-list"
        guide_params = {
            'key': api_key,
            'species_id': species_id
        }
        
        response = requests.get(guide_url, params=guide_params, timeout=10)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"Error fetching care guide for species {species_id}: {e}")
        return None

def enhance_recommendations_with_perenual(gemini_recommendations):
    """
    Enhance Gemini recommendations with detailed Perenual data
    """
    enhanced_recommendations = []
    
    for recommendation in gemini_recommendations:
        scientific_name = recommendation.get('scientific_name', '')
        
        # Search for this plant in Perenual
        plant_details = get_plant_details(scientific_name, limit=1)
        
        if plant_details:
            plant_data = plant_details[0]
            
            # Enhance the recommendation with Perenual data
            enhanced_rec = {
                **recommendation,  # Keep original Gemini data
                'perenual_data': {
                    'id': plant_data.get('id'),
                    'cycle': plant_data.get('cycle'),
                    'watering': plant_data.get('watering'),
                    'sunlight': plant_data.get('sunlight', []),
                    'hardiness': plant_data.get('hardiness', {}),
                    'growth_rate': plant_data.get('growth_rate'),
                    'maintenance': plant_data.get('maintenance'),
                    'drought_tolerant': plant_data.get('drought_tolerant'),
                    'poisonous_to_humans': plant_data.get('poisonous_to_humans'),
                    'poisonous_to_pets': plant_data.get('poisonous_to_pets'),
                    'edible_fruit': plant_data.get('edible_fruit'),
                    'medicinal': plant_data.get('medicinal'),
                    'description': plant_data.get('description'),
                    'default_image': plant_data.get('default_image'),
                    'watering_benchmark': plant_data.get('watering_general_benchmark'),
                    'pruning_month': plant_data.get('pruning_month', []),
                    'flowering_season': plant_data.get('flowering_season')
                }
            }
            
            # Get care guide if available
            care_guide = get_plant_care_guide(plant_data.get('id'))
            if care_guide:
                enhanced_rec['care_guide'] = care_guide
            
            enhanced_recommendations.append(enhanced_rec)
        else:
            # If no Perenual data found, keep original recommendation
            enhanced_recommendations.append(recommendation)
    
    return enhanced_recommendations

def get_indian_native_plants(limit=50):
    """
    Get plants that are suitable for Indian climate
    """
    api_key = os.getenv('PERENUAL_API_KEY')
    
    if not api_key:
        return []
    
    try:
        # Search for tropical and subtropical plants
        search_url = "https://perenual.com/api/species-list"
        
        # Get plants suitable for warm climates
        tropical_params = {
            'key': api_key,
            'per_page': limit,
            'hardiness': '9-13',  # Warm climate zones
            'cycle': 'perennial'  # Long-lasting plants
        }
        
        response = requests.get(search_url, params=tropical_params, timeout=10)
        response.raise_for_status()
        
        return response.json().get('data', [])
        
    except Exception as e:
        print(f"Error fetching Indian suitable plants: {e}")
        return []

def format_perenual_data_for_display(plant_data):
    """
    Format Perenual plant data for nice display in Streamlit
    """
    perenual = plant_data.get('perenual_data', {})
    
    if not perenual:
        return {}
    
    formatted = {
        'watering_schedule': perenual.get('watering', 'Not specified'),
        'sunlight_needs': ', '.join(perenual.get('sunlight', [])) or 'Not specified',
        'growth_rate': perenual.get('growth_rate', 'Not specified'),
        'maintenance_level': perenual.get('maintenance', 'Not specified'),
        'drought_tolerance': 'Yes' if perenual.get('drought_tolerant') else 'No',
        'safety': {
            'humans': 'Safe' if not perenual.get('poisonous_to_humans') else 'Caution - Poisonous',
            'pets': 'Safe' if not perenual.get('poisonous_to_pets') else 'Caution - Poisonous'
        },
        'special_features': []
    }
    
    # Add special features
    if perenual.get('edible_fruit'):
        formatted['special_features'].append('Edible fruit')
    if perenual.get('medicinal'):
        formatted['special_features'].append('Medicinal properties')
    if perenual.get('flowering_season'):
        formatted['special_features'].append(f"Flowers in {perenual.get('flowering_season')}")
    
    # Watering details
    benchmark = perenual.get('watering_benchmark', {})
    if benchmark and benchmark.get('value'):
        formatted['watering_frequency'] = f"Every {benchmark['value']} {benchmark.get('unit', 'days')}"
    
    return formatted
