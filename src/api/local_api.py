import requests
import json
import datetime
import re
from typing import Dict, List, Any, Optional

# LM Studio API Configuration
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234"
MODEL_NAME = "llama-3.2-3b-crop-recommender"

def get_goal_specific_instructions(goal_type, region):
    """
    Get specific instructions based on goal type and region
    """
    instructions = {
        'cash_crops': f"""
For CASH CROPS in {region} focus on:
• High-value commercial crops with strong regional market demand
• Fast-growing varieties with multiple harvests per year  
• Crops with export potential and value-added processing opportunities
• Regional specialties like spices, medicinal plants, and cash crops
• Consider storage life, transportation, and local market infrastructure
• Emphasize crops with established supply chains and steady pricing
• Focus on water-efficient and climate-resilient varieties
        """,
        'food_crops': f"""
For FOOD CROPS in {region} focus on:
• Nutritious staples, vegetables, and fruits for household food security
• Kitchen garden suitable crops for year-round home consumption
• High-yield, nutrient-dense varieties adapted to local conditions
• Traditional crops with cultural significance in {region}
• Seasonal rotation for continuous food production
• Protein-rich legumes and vitamin-rich vegetables
• Drought-tolerant and disease-resistant varieties
        """,
        'afforestation': f"""
For AFFORESTATION in {region} focus on:
• Fast-growing native trees for rapid environmental restoration
• Species with excellent air purification and oxygen production
• Trees providing shade, erosion control, and biodiversity support
• Urban-suitable species with pollution tolerance
• Multi-purpose trees (timber, fruit, medicinal, fodder)
• Carbon sequestration potential and climate adaptation
• Traditional agroforestry species integrated with farming
        """
    }
    return instructions.get(goal_type, instructions['afforestation'])

def check_lm_studio_connection():
    """
    Check if LM Studio is running and accessible
    """
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/v1/models", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"LM Studio connection error: {e}")
        return False

def get_available_models():
    """
    Get list of available models from LM Studio
    """
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/v1/models", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            return [model['id'] for model in models_data.get('data', [])]
        return []
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def get_model_info(model_id: str):
    """
    Get information about a specific model
    """
    try:
        response = requests.get(f"{LM_STUDIO_BASE_URL}/v1/models/{model_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching model info: {e}")
        return None

def get_recommendations(location_data, prefer_native=True, goal_type="afforestation", lat=20.5937, lon=78.9629):
    """
    Get comprehensive plant/crop recommendations from LM Studio local API with specific water/sunlight requirements
    """
    try:
        # Check if LM Studio is running
        if not check_lm_studio_connection():
            return create_error_response("LM Studio is not running. Please start LM Studio server first.")
        
        # Check if the model is available
        available_models = get_available_models()
        if not available_models:
            return create_error_response("No models found in LM Studio. Please load a model first.")
        
        # Use the specified model or fallback to first available
        model_to_use = MODEL_NAME if MODEL_NAME in available_models else available_models[0]
        
        # Generate user goal from goal type
        goal_mapping = {
            'cash_crops': 'commercial cash crop cultivation for maximum economic returns',
            'food_crops': 'food crop cultivation for nutrition and food security',
            'afforestation': 'afforestation and tree plantation for environmental benefits'
        }
        user_goal = goal_mapping.get(goal_type, 'sustainable environmental plantation')
        
        # Create a concise prompt optimized for local 3B models
        prompt = create_concise_local_prompt(location_data, user_goal, prefer_native, goal_type, lat, lon)
        
        # Generate response with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = generate_chat_completion(prompt, model_to_use)
                
                if response and response.strip():
                    # Parse the response into structured data
                    parsed_recommendations = parse_enhanced_local_response(response)
                    
                    # Ensure we return a list of dictionaries with valid data
                    if isinstance(parsed_recommendations, list) and len(parsed_recommendations) > 0:
                        return parsed_recommendations
                    else:
                        print(f"Attempt {attempt + 1}: No valid recommendations parsed from response")
                        if attempt == max_retries - 1:
                            return create_error_response("Unable to generate valid recommendations after multiple attempts")
                else:
                    print(f"Attempt {attempt + 1}: No response from local model")
                    if attempt == max_retries - 1:
                        return create_error_response("Local model not responding. Please check if LM Studio is running and the model is loaded.")
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return create_error_response(f"Local AI service error: {e}")
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return create_error_response(f"System error: {e}")

def generate_chat_completion(prompt: str, model: str, temperature: float = 0.7, max_tokens: int = 4096):
    """
    Generate chat completion using LM Studio REST API
    """
    try:
        # Truncate prompt if it's too long (conservative approach)
        max_prompt_length = 8000  # Balanced limit for 3B models with good output
        if len(prompt) > max_prompt_length:
            print(f"Warning: Prompt too long ({len(prompt)} chars), truncating to {max_prompt_length}")
            prompt = prompt[:max_prompt_length] + "\n\nPlease provide 5 plant recommendations in JSON format with specific water amounts and sunlight hours."
        
        # Prepare the request payload with conservative settings
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI agricultural consultant. Provide plant recommendations for Indian climate in valid JSON format. Always include specific water amounts in liters and exact sunlight hours. Keep responses concise and under 4000 tokens. Always recommend exactly 5 plants."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "stop": ["</response>", "\n\n---", "###"],  # Stop sequences to prevent runaway generation
            "top_p": 0.9,  # More focused responses
            "repeat_penalty": 1.1  # Prevent repetition
        }
        
        # Make the API request with conservative timeout
        response = requests.post(
            f"{LM_STUDIO_BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=45  # Increased timeout to 45 seconds for complex requests
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Extract the content from the response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                
                # Print stats if available
                if 'stats' in response_data:
                    stats = response_data['stats']
                    print(f"Local AI Stats - Tokens/sec: {stats.get('tokens_per_second', 0):.2f}, "
                          f"Time to first token: {stats.get('time_to_first_token', 0):.3f}s")
                
                return content
            else:
                print("No valid response choices from local model")
                return None
        elif response.status_code == 400:
            error_msg = response.text
            if "crashed" in error_msg.lower():
                print("❌ Model crashed - try reducing max_tokens or reloading the model in LM Studio")
            elif "out of memory" in error_msg.lower():
                print("❌ Out of memory - try a smaller model or reduce context length")
            else:
                print(f"❌ Bad request: {error_msg}")
            return None
        else:
            print(f"API request failed with status {response.status_code}: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error generating completion: {e}")
        return None

def create_error_response(error_message):
    """
    Create an error response that will be handled gracefully by the UI
    """
    return [{
        'error': True,
        'message': error_message,
        'scientific_name': 'Error',
        'common_name': 'Unable to generate recommendations',
        'local_name': 'कृपया फिर से कोशिश करें (Please try again)',
        'plant_type': 'Error',
        'family': 'System Error',
        'suitability_score': '0/10',
        'suitability_analysis': f'Error: {error_message}',
        'environmental_impact_score': 0,
        'air_quality_benefits': {
            'pollution_reduction': 'Not available',
            'co2_absorption': '0 kg/year',
            'oxygen_production': '0 kg/year',
            'aqi_improvement': 'Not available'
        },
        'water_requirements': {
            'seedling_stage': 'Not available - system error',
            'mature_plant': 'Not available - system error',
            'dry_season_adjustment': 'Not available',
            'monsoon_reduction': 'Not available'
        },
        'sunlight_requirements': {
            'daily_hours_needed': 'Not available',
            'light_intensity': 'Not available',
            'optimal_direction': 'Not available'
        },
        'growth_characteristics': {
            'growth_rate': 'Not applicable',
            'mature_height': 'Not applicable',
            'spacing_requirements': 'Not applicable'
        },
        'sustainability_highlights': ['Please try again with different parameters', 
                                   'Make sure LM Studio is running',
                                   'Check if the model is loaded in LM Studio']
    }]

def create_concise_local_prompt(data, user_goal, prefer_native, goal_type="afforestation", lat=20.5937, lon=78.9629):
    """
    Create a concise prompt optimized for local 3B models with specific water/sunlight requirements
    """
    # Get goal-specific instructions
    goal_instructions = get_goal_specific_instructions(goal_type, "India")
    
    # Basic environmental data
    env_summary = f"""Location: {data.get('location', 'India')} ({lat:.2f}, {lon:.2f})
Temperature: {data.get('temperature', 25)}°C
Rainfall: {data.get('rainfall', 1000)}mm/year
Soil pH: {data.get('soil_ph', 6.5)}
Humidity: {data.get('humidity', 65)}%
Air Quality: {data.get('aqi', 106)} AQI"""
    
    # Native preference
    native_text = "Focus on NATIVE Indian plants" if prefer_native else "Include both native and adapted plants"
    
    # User preferences (simplified)
    user_prefs = data.get('user_preferences', {})
    pref_text = ""
    if user_prefs.get('water_availability') and user_prefs['water_availability'] != 'Auto-detect':
        pref_text += f"\nWater Constraint: {user_prefs['water_availability']}"
    if user_prefs.get('space_availability'):
        pref_text += f"\nSpace Available: {user_prefs['space_availability']} sq meters"
    if user_prefs.get('space_location_type'):
        location_type = user_prefs['space_location_type']
        pref_text += f"\nLocation Type: {location_type}"
        
        # Add specific constraints for location type
        if 'window' in location_type.lower() or 'balcony' in location_type.lower():
            pref_text += " (Container plants only, max 2m height)"
        elif 'garden' in location_type.lower() or 'yard' in location_type.lower():
            pref_text += " (Ground planting possible, trees up to 5m)"
        elif 'farm' in location_type.lower():
            pref_text += " (Large scale planting, any size trees)"

    # Create concise prompt with specific water/sunlight requirements
        prompt = f"""TASK: Recommend exactly 5 plants for {goal_type} in India.

LOCATION DATA:
{env_summary}

REQUIREMENTS:
- {native_text}
- {goal_instructions.strip()[:200]}
{pref_text}

WATER AMOUNT GUIDELINES (use specific amounts):
- Large Trees: 80-200L/week mature, 20-50L/week seedling
- Medium Trees: 30-80L/week mature, 10-25L/week seedling
- Small Trees/Shrubs: 15-40L/week mature, 5-15L/week seedling
- Crops: 3-15L/week per plant depending on crop type
- Herbs/Small plants: 1-5L/week per plant
- Potted plants: 0.5-3L/day per plant

SUNLIGHT GUIDELINES (use specific hours):
- Full sun: 6-8 hours daily
- Partial sun: 4-6 hours daily
- Partial shade: 2-4 hours daily
- Full shade: <2 hours daily

SEASONAL SUITABILITY & PLANTING WINDOW (CRITICAL):
- For every recommended species include a "planting_window" object with:
    - "best_months": a list of month names (e.g. ["June","July"]) representing the optimal planting window for the specified location/region.
    - "can_plant_now": true/false (boolean). If false, add a one-sentence "planting_window_justification" explaining why it's not recommended now and what climate/soil/season constraint prevents planting now.
    - If "can_plant_now" is false, include a short "planting_mitigation_steps" string that explains how to successfully establish the plant off-window (for example: use seedlings, shade nets, staggered watering, raised beds, or suggest the next best months to plant).

Provide exactly 5 plant recommendations in this JSON format (do not include any extra text):
[
    {{
        "common_name": "Plant Name",
        "local_name": "स्थानीय नाम (Local Name)",
        "scientific_name": "Scientific name",
        "plant_type": "Tree/Shrub/Crop/Herb/Potted",
        "family": "Plant family",
        "mature_height": "X-Y meters",
        "spacing": "X meters apart",

        "water_needs": {{
            "seedling": "X liters per week for first 6 months (numeric liters)",
            "mature": "X liters per week when fully grown (numeric liters)", 
            "dry_season": "X liters per week during summer (numeric liters)",
            "monsoon": "X liters per week during rains (numeric liters)"
        }},

        "sunlight": {{
            "daily_hours": "X-Y hours direct sunlight (numeric hours)",
            "type": "Full sun/Partial sun/Partial shade/Full shade",
            "best_direction": "South/East/West facing recommended"
        }},

        "planting_window": {{
            "best_months": ["Month1","Month2"],
            "can_plant_now": true,
            "planting_window_justification": "One-sentence explanation (why/why not)",
            "planting_mitigation_steps": "If off-window, short steps to mitigate or next best window"
        }},

        "care_level": "Easy/Medium/Hard",
        "growth_rate": "Fast/Medium/Slow (X cm/month)",
        "benefits": ["air purification", "carbon absorption", "oxygen production"],
        "initial_cost": "₹X-Y per plant",
        "suitability_score": 8.5
    }}
]

CRITICAL: Use EXACT numeric amounts in liters and hours (e.g., "25 liters per week", "6-8 hours"), and match the amounts to the plant_type (trees need much higher volumes than potted herbs). Do not use vague descriptors. Ensure the "planting_window" is accurate for India at the provided coordinates. Respond with valid JSON only."""
    
    return prompt

def parse_enhanced_local_response(response_text):
    """
    Parse enhanced local AI response with ultra-robust JSON extraction and fixing
    """
    try:
        # Clean the response text to handle markdown code blocks
        cleaned_text = response_text.strip()
        
        # Remove markdown code block markers if present
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]   # Remove ``` 
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]  # Remove trailing ```
        
        cleaned_text = cleaned_text.strip()
        
        # Try to find JSON array first (which is what the model actually returns)
        array_start = cleaned_text.find('[')
        
        if array_start != -1:
            # Find the matching closing bracket
            bracket_count = 0
            end_idx = array_start
            
            for i, char in enumerate(cleaned_text[array_start:], array_start):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
            
            if bracket_count == 0:  # Found complete JSON array
                json_str = cleaned_text[array_start:end_idx]
                json_str = clean_json_string(json_str)
                
                try:
                    data = json.loads(json_str)
                    if isinstance(data, list) and len(data) > 0:
                        # Normalize each recommendation's fields for UI compatibility
                        for rec in data:
                            normalize_recommendation_fields(rec)
                        print(f"✅ Successfully parsed {len(data)} recommendations from local AI")
                        return enhance_local_recommendations_for_ui(data)
                except json.JSONDecodeError as e:
                    print(f"JSON array parse error: {e}")
                    # Try to fix and re-parse
                    json_str = fix_json_error(json_str, e)
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, list) and len(data) > 0:
                            return enhance_local_recommendations_for_ui(data)
                    except:
                        pass
        
        # Fallback: Look for object structure (original logic)
        start_idx = cleaned_text.find('{')
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(cleaned_text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count == 0:  # Found complete JSON object
                json_str = cleaned_text[start_idx:end_idx]
                json_str = clean_json_string(json_str)
                
                try:
                    data = json.loads(json_str)
                    recommendations = data.get('recommendations', [])
                    if recommendations:
                        # Normalize recommendations
                        for rec in recommendations:
                            normalize_recommendation_fields(rec)
                        print(f"✅ Successfully parsed {len(recommendations)} recommendations from object structure")
                        return enhance_local_recommendations_for_ui(recommendations)
                except json.JSONDecodeError as e:
                    print(f"JSON object parse error: {e}")
        
        print("No valid JSON structure found, extracting partial data...")
        return extract_partial_recommendations(cleaned_text)
            
    except Exception as e:
        print(f"Critical parsing error: {e}")
        return extract_partial_recommendations(response_text)

def clean_json_string(json_str):
    """Clean and normalize JSON string"""
    # Remove problematic characters and patterns
    json_str = json_str.replace('\n', ' ').replace('\t', ' ')
    json_str = json_str.replace('\\"', '"')  # Fix escaped quotes
    json_str = json_str.replace('""', '"')   # Fix double quotes
    
    # Fix common AI text artifacts
    json_str = json_str.replace('"...', '""')     # Replace unfinished strings
    json_str = json_str.replace('...', '')        # Remove ellipsis
    json_str = json_str.replace('",}', '"}')      # Fix trailing commas
    json_str = json_str.replace(',}', '}')        # Fix trailing commas
    json_str = json_str.replace(',]', ']')        # Fix trailing commas in arrays
    
    # Fix multiple spaces
    import re
    json_str = re.sub(r'\s+', ' ', json_str)
    
    return json_str.strip()


def normalize_recommendation_fields(rec: dict):
    """Normalize various possible field names from model output into the UI-friendly schema.

    - Accepts either 'water_needs' or 'water_requirements' and ensures 'water_requirements' exists.
    - Accepts either 'sunlight' or 'sunlight_requirements' and ensures 'sunlight_requirements' exists.
    - Converts vague schedules ("daily", "weekly") into conservative numeric defaults if exact numbers missing.
    - Ensures 'planting_window' exists with safe defaults.
    """
    # Normalize water fields
    water = rec.get('water_needs') or rec.get('water_requirements') or {}
    # Convert string-based water descriptors to structured keys if necessary
    if isinstance(water, str):
        w = water.lower()
        if 'daily' in w:
            seedling = '7 liters per week'
        else:
            seedling = '5-10 liters per week'
        water = {
            'seedling_stage': seedling,
            'mature_plant': '25-40 liters per week',
            'dry_season_adjustment': 'Add 10-15 liters per week',
            'monsoon_reduction': 'Reduce to 10-20 liters per week'
        }

    # Normalize keys names
    if 'seedling' in water and 'seedling_stage' not in water:
        water['seedling_stage'] = water.pop('seedling')
    if 'mature' in water and 'mature_plant' not in water:
        water['mature_plant'] = water.pop('mature')

    # Ensure numeric-like strings exist (keep as strings but prefer explicit liters)
    if not water.get('seedling_stage') and water.get('seedling'):
        water['seedling_stage'] = water.get('seedling') or '5-10 liters per week'
    if not water.get('seedling_stage'):
        water['seedling_stage'] = '5-10 liters per week'
    if not water.get('mature_plant') and water.get('mature'):
        water['mature_plant'] = water.get('mature') or '25-40 liters per week'
    if not water.get('mature_plant'):
        water['mature_plant'] = '25-40 liters per week'

    # Convert fuzzy frequency descriptors into explicit liters/week when possible
    plant_type = rec.get('plant_type', 'plant')
    for key in list(water.keys()):
        val = water.get(key)
        if isinstance(val, str) and any(word in val.lower() for word in ['daily', 'weekly', 'alternate', 'every']):
            # map key to stage for conversion heuristics
            stage = 'seed' if 'seed' in key else 'mature' if 'mature' in key else 'mature'
            water[key] = frequency_to_liters(val, plant_type=plant_type, stage=stage)

    rec['water_requirements'] = water

    # Normalize sunlight fields
    sun = rec.get('sunlight') or rec.get('sunlight_requirements') or {}
    if isinstance(sun, str):
        s = sun.lower()
        daily = '6-8 hours' if 'full' in s else '4-6 hours'
        sun = {
            'daily_hours_needed': daily,
            'light_intensity': 'Full Sun' if 'full' in s else 'Partial Sun',
            'optimal_direction': 'South facing'
        }

    # Map alternative keys
    if 'daily_hours' in sun and 'daily_hours_needed' not in sun:
        sun['daily_hours_needed'] = sun.pop('daily_hours')
    if 'type' in sun and 'light_intensity' not in sun:
        sun['light_intensity'] = sun.pop('type')

    if not sun.get('daily_hours_needed'):
        # try to use 'daily_hours' if present
        if 'daily_hours' in sun:
            sun['daily_hours_needed'] = sun.get('daily_hours') or '6-8 hours'
        else:
            sun['daily_hours_needed'] = '6-8 hours'
    if not sun.get('light_intensity'):
        sun['light_intensity'] = 'Full Sun'
    rec['sunlight_requirements'] = sun

    # Ensure planting_window exists
    if 'planting_window' not in rec or not isinstance(rec.get('planting_window'), dict):
        rec['planting_window'] = {
            'best_months': ['June', 'July', 'August'],
            'can_plant_now': True,
            'planting_window_justification': 'Default monsoon window for India.',
            'planting_mitigation_steps': 'Use container seedlings, mulch, and supplemental irrigation when off-window.'
        }

    return rec


def frequency_to_liters(text: str, plant_type: str = 'plant', stage: str = 'mature') -> str:
    """Convert vague frequency text into a conservative numeric liters/week string based on plant type.

    This is heuristic and aims to replace words like 'daily', 'weekly', 'alternate day' with explicit
    liters per week so the UI shows concrete numbers.
    """
    if not text:
        return '25-40 liters per week'
    t = str(text).lower()
    p = (plant_type or '').lower()

    # If a numeric liters value already exists, return it roughly as-is
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:liters?|l)", t)
    if m:
        # return normalized 'X liters per week' (if a per-day is found we'll not detect here)
        return f"{m.group(1)} liters per week"

    # base buckets
    if 'tree' in p:
        seedling_daily = '35 liters per week'  # ~5L/day
        seedling_alt = '20 liters per week'
        seedling_weekly = '20-30 liters per week'
        mature_weekly = '80-150 liters per week'
        mature_weekly_small = '30-60 liters per week'
    elif 'crop' in p:
        seedling_daily = '10 liters per week'
        seedling_alt = '6 liters per week'
        seedling_weekly = '6-10 liters per week'
        mature_weekly = '10-40 liters per week'
        mature_weekly_small = '5-15 liters per week'
    else:
        # herbs / potted / default
        seedling_daily = '7 liters per week'
        seedling_alt = '4 liters per week'
        seedling_weekly = '3-7 liters per week'
        mature_weekly = '10-25 liters per week'
        mature_weekly_small = '3-10 liters per week'

    if 'daily' in t or 'every day' in t:
        return seedling_daily if stage.startswith('seed') else mature_weekly
    if 'alternate' in t or 'alternate day' in t or 'every other' in t:
        return seedling_alt if stage.startswith('seed') else mature_weekly_small
    if 'weekly' in t or 'once a week' in t:
        return seedling_weekly if stage.startswith('seed') else mature_weekly_small
    if 'monthly' in t:
        # monthly -> convert to weekly estimate
        return '5-10 liters per week'

    # fallback: return a conservative mature_weekly
    return mature_weekly

def fix_json_error(json_str, error):
    """Attempt to fix specific JSON errors"""
    try:
        error_pos = getattr(error, 'pos', 0)
        
        if "Extra data" in str(error):
            # Truncate at the error position
            json_str = json_str[:error_pos]
            # Try to close any open braces
            brace_count = json_str.count('{') - json_str.count('}')
            json_str += '}' * brace_count
        
        elif "Expecting" in str(error):
            # Try to add missing characters
            if "," in str(error):
                json_str = json_str[:error_pos] + ',' + json_str[error_pos:]
            elif "}" in str(error):
                json_str = json_str[:error_pos] + '}' + json_str[error_pos:]
        
        return json_str
    except Exception:
        return json_str

def extract_partial_recommendations(text):
    """Extract partial recommendation data when JSON parsing fails"""
    try:
        recommendations = []
        
        # Look for plant names and basic info in the text
        import re
        
        # Try to find scientific names (usually in quotes or with specific patterns)
        scientific_names = re.findall(r'"scientific_name":\s*"([^"]+)"', text)
        common_names = re.findall(r'"common_name":\s*"([^"]+)"', text)
        local_names = re.findall(r'"local_name":\s*"([^"]+)"', text)
        
        # Create basic recommendations from found data
        for i in range(min(len(scientific_names), 5)):  # Limit to 5 plants
            rec = {
                'scientific_name': scientific_names[i] if i < len(scientific_names) else f'Plant Species {i+1}',
                'common_name': common_names[i] if i < len(common_names) else f'Common Plant {i+1}',
                'local_name': local_names[i] if i < len(local_names) else f'स्थानीय पौधा {i+1}',
                'plant_type': 'Tree',
                'family': 'Plant Family',
                'suitability_score': '8/10',
                'suitability_analysis': 'This plant is well-suited for your environmental conditions based on local climate analysis.',
                'water_requirements': {
                    'seedling_stage': '5-10 liters per week',
                    'mature_plant': '25-40 liters per week',
                    'dry_season_adjustment': 'Add 10-15 liters per week',
                    'monsoon_reduction': 'Reduce to 10-15 liters per week'
                },
                'sunlight_requirements': {
                    'daily_hours_needed': '6-8 hours',
                    'light_intensity': 'Full Sun',
                    'optimal_direction': 'South facing'
                },
                'air_quality_benefits': {
                    'pollution_reduction': 'PM2.5, dust particles',
                    'co2_absorption': '25 kg/year',
                    'oxygen_production': '20 liters/day',
                    'aqi_improvement': 'Moderate improvement'
                },
                'growth_characteristics': {
                    'growth_rate': 'Medium',
                    'mature_height': '3-5 meters',
                    'spacing_requirements': '2-3 meters apart'
                },
                'sustainability_highlights': ['Good air purification', 'Low maintenance', 'Native species']
            }
            # Add default planting_window info when the model did not provide it
            rec['planting_window'] = {
                'best_months': ['June', 'July', 'August'],
                'can_plant_now': True,
                'planting_window_justification': 'Monsoon window in India is typically best for establishment',
                'planting_mitigation_steps': 'If off-window, use container-grown seedlings, mulch and increased watering for 4-6 weeks.'
            }
            recommendations.append(rec)
        
        if not recommendations:
            # Create at least one fallback recommendation
            return create_fallback_recommendations()
        
        return recommendations
        
    except Exception as e:
        print(f"Error extracting partial data: {e}")
        return create_fallback_recommendations()

def enhance_local_recommendations_for_ui(recommendations):
    """
    Enhance local AI recommendations to ensure UI compatibility with specific water/sunlight measurements
    """
    enhanced = []
    
    for rec in recommendations:
        # Extract and enhance water needs with specific measurements
        # Prefer normalized 'water_requirements' produced by parser
        water_needs = rec.get('water_requirements') or rec.get('water_needs', {})
        if isinstance(water_needs, str):
            # Convert old format to new structure with specific amounts
            water_needs = {
                'seedling_stage': '5-10 liters per week',
                'mature_plant': '25-40 liters per week',
                'dry_season_adjustment': 'Add 10-15 liters per week',
                'monsoon_reduction': 'Reduce to 10-20 liters per week'
            }

        # Extract and enhance sunlight needs with specific hours
        # Prefer normalized 'sunlight_requirements'
        sunlight = rec.get('sunlight_requirements') or rec.get('sunlight', {})
        if isinstance(sunlight, str):
            sunlight = {
                'daily_hours_needed': '6-8 hours' if 'full' in str(sunlight).lower() else '4-6 hours',
                'light_intensity': 'Full Sun' if 'full' in str(sunlight).lower() else 'Partial Sun',
                'optimal_direction': 'South facing'
            }

        # Create enhanced recommendation with specific measurements
        enhanced_rec = {
            'scientific_name': rec.get('scientific_name', 'Unknown Species'),
            'common_name': rec.get('common_name', 'Unknown Plant'),
            'local_name': rec.get('local_name', 'स्थानीय नाम अज्ञात'),
            'plant_type': rec.get('plant_type', 'Tree'),
            'family': rec.get('family', 'Plant Family'),
            'suitability_score': f"{rec.get('suitability_score', 8)}/10",
            'suitability_analysis': f"This {rec.get('common_name', 'plant')} is well-suited for your environmental conditions, requiring {water_needs.get('mature', '25-40 liters per week')} water when mature and {sunlight.get('daily_hours', '6-8 hours')} of daily sunlight.",
            'environmental_impact_score': rec.get('suitability_score', 8),
            
            # Enhanced water requirements with specific measurements
            'water_requirements': {
                'seedling_stage': water_needs.get('seedling', '5-10 liters per week for first 6 months'),
                'young_plant': '15-25 liters per week for young plants',
                'mature_plant': water_needs.get('mature', '25-40 liters per week for mature plants'),
                'dry_season_adjustment': water_needs.get('dry_season', 'Add 10-15 liters per week during summer'),
                'monsoon_reduction': water_needs.get('monsoon', 'Reduce to 10-20 liters per week during monsoon'),
                'water_conservation_methods': 'Drip irrigation: 2-4 liters/hour, Mulching: 5cm deep, Rainwater harvesting recommended'
            },
            
            # Enhanced sunlight requirements with specific hours
            'sunlight_requirements': {
                'daily_hours_needed': sunlight.get('daily_hours', '6-8 hours'),
                'light_intensity': sunlight.get('type', 'Full Sun'),
                'optimal_direction': sunlight.get('best_direction', 'South facing recommended'),
                'shade_tolerance': 'Can tolerate 1-2 hours less sunlight if needed',
                'seasonal_adjustments': 'May need partial shade during peak summer (12-3 PM)'
            },
            
            # Convert simple benefits to structured format
            'air_quality_benefits': {
                'pollution_reduction': 'PM2.5, dust particles, CO2',
                'co2_absorption': '25-50 kg per year',
                'oxygen_production': '20-40 liters per day',
                'aqi_improvement': 'Moderate to significant improvement'
            },
            
            # Enhanced growth characteristics with specific measurements
            'growth_characteristics': {
                'mature_height': rec.get('mature_height', '3-5 meters'),
                'mature_spread': f"{rec.get('spacing', '3 meters').replace(' apart', '')} canopy spread",
                'growth_rate': rec.get('growth_rate', 'Medium growth rate'),
                'lifespan': '15-30 years',
                'space_requirements': f"{rec.get('spacing', '3 meters apart')} minimum spacing"
            },
            
            # Convert benefits array to sustainability highlights
            'sustainability_highlights': rec.get('benefits', ['Air purification', 'Carbon absorption', 'Oxygen production']),
            
            # Enhanced plantation guide with specific measurements
            'plantation_guide': {
                'best_season': 'Monsoon season (June-September) or post-monsoon (October-November)',
                'soil_preparation': f"Dig pit 60x60x60cm, mix 5kg compost, suitable for {rec.get('plant_type', 'tree')} planting",
                'planting_method': f"Plant with {rec.get('spacing', '3 meter spacing')}, water immediately with {water_needs.get('mature_plant', water_needs.get('mature', '15-20 liters'))}",
                'initial_care': f"Water with {water_needs.get('seedling_stage', water_needs.get('seedling', '5-10 liters'))} during establishment (first 4 weeks)"
            },
            
            # Additional enhanced fields for UI
            'watering_patterns': {
                'seedling_stage': f"{water_needs.get('seedling_stage', water_needs.get('seedling', '5-10 liters per week'))} during establishment",
                'young_plant': f"{water_needs.get('young_plant', '15-25 liters per week')} for young plants",
                'mature_plant': f"{water_needs.get('mature_plant', water_needs.get('mature', '25-40 liters per week'))} for mature plants",
                'seasonal_variations': f"Summer: {water_needs.get('dry_season_adjustment', water_needs.get('dry_season', 'add 10-15L/week'))}, Monsoon: {water_needs.get('monsoon_reduction', water_needs.get('monsoon', 'reduce to 10-20L/week'))}"
            },
            
            'maintenance_schedule': {
                'daily': f"Check soil moisture, water if needed with {water_needs.get('seedling', '1-2 liters')} during first month",
                'weekly': f"Deep watering with {water_needs.get('mature', '25-40 liters')} for mature plants",
                'monthly': 'Pruning if needed, fertilizer application, pest inspection',
                'seasonal': 'Adjust watering based on monsoon/dry season, seasonal pruning',
                'annual': 'Major health assessment, soil amendment, structural pruning'
            },
            
            'economic_benefits': {
                'initial_cost': rec.get('initial_cost', '₹50-200 per plant'),
                'maintenance_cost_annual': '₹100-500 per plant per year',
                'economic_returns': 'Environmental benefits, potential fruit/timber value',
                'property_value_impact': '2-5% increase in property value',
                'long_term_savings': 'Reduced air conditioning costs, health benefits'
            },
            
            'user_goal_alignment': f"This {rec.get('common_name', 'plant')} aligns perfectly with your environmental goals, requiring specific care of {sunlight.get('daily_hours', '6-8 hours')} daily sunlight and {water_needs.get('mature', 'moderate water')} for optimal growth and maximum environmental benefits.",
            
            'additional_uses': ', '.join(rec.get('benefits', [])) if rec.get('benefits') else 'Multiple environmental and aesthetic benefits',
            'companion_plants': 'Compatible with other native species in mixed plantation schemes'
        }
        # Ensure planting_window exists and is well-formed
        planting_window = rec.get('planting_window')
        if not planting_window:
            # Try to infer from plantation_guide.best_season if available
            best_months = None
            plantation_guide = rec.get('plantation_guide', {})
            best_season = plantation_guide.get('best_season', '') if isinstance(plantation_guide, dict) else ''
            if isinstance(best_season, str) and 'monsoon' in best_season.lower():
                best_months = ['June', 'July', 'August', 'September']
            elif isinstance(best_season, str) and 'post-monsoon' in best_season.lower():
                best_months = ['October', 'November']
            elif isinstance(best_season, str) and 'winter' in best_season.lower():
                best_months = ['December', 'January', 'February']
            else:
                best_months = ['June', 'July', 'August']

            planting_window = {
                'best_months': best_months,
                'can_plant_now': True,
                'planting_window_justification': f"Defaulted to {', '.join(best_months)} based on common regional planting windows.",
                'planting_mitigation_steps': 'If off-window, use container seedlings, mulching and increased watering during establishment.'
            }

        enhanced_rec['planting_window'] = planting_window

        enhanced.append(enhanced_rec)
    
    return enhanced

def enhance_recommendations_for_ui(recommendations):
    """Enhance recommendations to ensure UI compatibility - kept for backwards compatibility"""
    enhanced = []
    
    for rec in recommendations:
        # Ensure all required fields exist with defaults including specific measurements
        enhanced_rec = {
            'scientific_name': rec.get('scientific_name', 'Unknown Species'),
            'common_name': rec.get('common_name', 'Unknown Plant'),
            'local_name': rec.get('local_name', 'स्थानीय नाम अज्ञात'),
            'plant_type': rec.get('plant_type', 'Plant'),
            'family': rec.get('family', 'Plant Family'),
            'suitability_score': rec.get('suitability_score', '7/10'),
            'suitability_analysis': rec.get('suitability_analysis', 'Suitable for local conditions with specific water and sunlight requirements.'),
            'environmental_impact_score': rec.get('environmental_impact_score', 8),
            
            # Enhanced with specific measurements
            'water_requirements': rec.get('water_requirements', {
                'seedling_stage': '5-10 liters per week for first 6 months',
                'mature_plant': '25-40 liters per week for mature plants',
                'dry_season_adjustment': 'Add 10-15 liters per week during summer',
                'monsoon_reduction': 'Reduce to 10-20 liters per week during monsoon'
            }),
            'sunlight_requirements': rec.get('sunlight_requirements', {
                'daily_hours_needed': '6-8 hours',
                'light_intensity': 'Full Sun',
                'optimal_direction': 'South facing preferred'
            }),
            'air_quality_benefits': rec.get('air_quality_benefits', {
                'pollution_reduction': 'General air purification',
                'co2_absorption': '20 kg/year',
                'oxygen_production': '15 liters/day',
                'aqi_improvement': 'Moderate'
            }),
            'growth_characteristics': rec.get('growth_characteristics', {
                'growth_rate': 'Medium',
                'mature_height': '2-4 meters',
                'spacing_requirements': '2 meters apart'
            }),
            'sustainability_highlights': rec.get('sustainability_highlights', ['Environmentally beneficial']),
            
            # Additional fields that might be expected by UI
            'plantation_guide': rec.get('plantation_guide', {}),
            'watering_patterns': rec.get('watering_patterns', {}),
            'maintenance_schedule': rec.get('maintenance_schedule', {}),
            'environmental_impact': rec.get('environmental_impact', {}),
            'economic_benefits': rec.get('economic_benefits', {}),
            'challenges_and_solutions': rec.get('challenges_and_solutions', {}),
            'user_goal_alignment': rec.get('user_goal_alignment', 'This plant supports your environmental goals with specific care requirements.'),
            'additional_uses': rec.get('additional_uses', ''),
            'companion_plants': rec.get('companion_plants', '')
        }
        # Ensure planting_window exists
        planting_window = rec.get('planting_window')
        if not planting_window:
            plantation_guide = rec.get('plantation_guide', {})
            best_season = plantation_guide.get('best_season', '') if isinstance(plantation_guide, dict) else ''
            if isinstance(best_season, str) and 'monsoon' in best_season.lower():
                best_months = ['June', 'July', 'August', 'September']
            elif isinstance(best_season, str) and 'post-monsoon' in best_season.lower():
                best_months = ['October', 'November']
            elif isinstance(best_season, str) and 'winter' in best_season.lower():
                best_months = ['December', 'January', 'February']
            else:
                best_months = ['June', 'July', 'August']

            planting_window = {
                'best_months': best_months,
                'can_plant_now': True,
                'planting_window_justification': f"Defaulted to {', '.join(best_months)} based on common regional planting windows.",
                'planting_mitigation_steps': 'If off-window, use container seedlings, mulching and increased watering during establishment.'
            }

        enhanced_rec['planting_window'] = planting_window

        enhanced.append(enhanced_rec)
    
    return enhanced


def create_fallback_recommendations():
    """Create fallback recommendations when all else fails - with specific measurements"""
    return [
        {
            'scientific_name': 'Azadirachta indica',
            'common_name': 'Neem Tree',
            'local_name': 'नीम (Neem)',
            'plant_type': 'Tree',
            'family': 'Meliaceae',
            'suitability_score': '9/10',
            'suitability_analysis': 'Excellent drought-tolerant tree, perfect for Indian climate with specific water needs of 40-60 liters per week when mature and 6-8 hours of daily sunlight.',
            'environmental_impact_score': 9,
            'water_requirements': {
                'seedling_stage': '10-15 liters per week for first 6 months',
                'young_plant': '20-30 liters per week for 6 months to 2 years',
                'mature_plant': '40-60 liters per week when fully grown',
                'dry_season_adjustment': 'Add 15-20 liters per week during summer',
                'monsoon_reduction': 'Reduce to 15-25 liters per week during rains',
                'water_conservation_methods': 'Drip irrigation: 3-5 liters/hour, Mulching: 5cm deep, Rainwater harvesting highly effective'
            },
            'sunlight_requirements': {
                'daily_hours_needed': '6-8 hours',
                'light_intensity': 'Full Sun',
                'optimal_direction': 'South facing preferred',
                'shade_tolerance': 'Can tolerate 2 hours less sunlight if needed',
                'seasonal_adjustments': 'Thrives in high summer sun, no shade protection needed'
            },
            'air_quality_benefits': {
                'pollution_reduction': 'PM2.5, SO2, NO2, dust particles',
                'co2_absorption': '48 kg/year',
                'oxygen_production': '260 liters/day',
                'aqi_improvement': 'Significant improvement (5-10 points)'
            },
            'growth_characteristics': {
                'mature_height': '15-20 meters',
                'mature_spread': '8-12 meters canopy',
                'growth_rate': 'Fast (2-3 meters per year)',
                'lifespan': '50-100 years',
                'space_requirements': '25-36 sq meters per tree (5-6 meters spacing)'
            },
            'sustainability_highlights': ['Natural pesticide properties', 'Medicinal uses', 'Fast growing', 'Extreme drought tolerance']
            ,
            'planting_window': {
                'best_months': ['June', 'July', 'August'],
                'can_plant_now': True,
                'planting_window_justification': 'Monsoon months are best for establishment in most Indian regions.',
                'planting_mitigation_steps': 'Use container seedlings, mulch heavily and provide supplemental watering if planting off-window.'
            }
        },
        {
            'scientific_name': 'Ficus religiosa',
            'common_name': 'Peepal Tree',
            'local_name': 'पीपल (Peepal)',
            'plant_type': 'Tree',
            'family': 'Moraceae',
            'suitability_score': '8.5/10',
            'suitability_analysis': 'Sacred tree with excellent air purification capabilities requiring 60-100 liters per week when mature and 6-8 hours of daily sunlight. Releases oxygen even at night.',
            'environmental_impact_score': 9,
            'water_requirements': {
                'seedling_stage': '15-20 liters per week for first 6 months',
                'young_plant': '30-50 liters per week for young trees',
                'mature_plant': '60-100 liters per week when fully grown',
                'dry_season_adjustment': 'Add 20-30 liters per week during summer',
                'monsoon_reduction': 'Reduce to 20-40 liters per week during rains',
                'water_conservation_methods': 'Deep root watering, 6cm mulch layer, collect rainwater for dry season use'
            },
            'sunlight_requirements': {
                'daily_hours_needed': '6-8 hours',
                'light_intensity': 'Full Sun',
                'optimal_direction': 'South or East facing preferred',
                'shade_tolerance': 'Can tolerate 1-2 hours less sunlight',
                'seasonal_adjustments': 'Benefits from morning sun exposure'
            },
            'air_quality_benefits': {
                'pollution_reduction': 'PM2.5, CO, dust, SO2',
                'co2_absorption': '50 kg/year',
                'oxygen_production': '300 liters/day (including nighttime)',
                'aqi_improvement': 'High improvement (8-15 points)'
            },
            'growth_characteristics': {
                'mature_height': '20-25 meters',
                'mature_spread': '12-15 meters canopy',
                'growth_rate': 'Medium (1-2 meters per year)',
                'lifespan': '100-200 years',
                'space_requirements': '64-100 sq meters per tree (8-10 meters spacing)'
            },
            'sustainability_highlights': ['24-hour oxygen production', 'Sacred cultural significance', 'Wildlife habitat support', 'Exceptionally long-lived']
            ,
            'planting_window': {
                'best_months': ['June', 'July', 'August'],
                'can_plant_now': True,
                'planting_window_justification': 'Monsoon months are generally ideal for tree establishment in India.',
                'planting_mitigation_steps': 'If planting outside monsoon, use irrigation and shade nets for establishment.'
            }
        }
    ]

# Test function to verify LM Studio connection
def test_local_connection():
    """Test function to verify LM Studio is working"""
    print("Testing LM Studio connection...")
    
    if check_lm_studio_connection():
        print("✅ LM Studio is running!")
        
        models = get_available_models()
        if models:
            print(f"✅ Available models: {', '.join(models)}")
            
            # Test with specific water/sunlight prompt
            test_prompt = """Respond with JSON for 1 plant with specific measurements:
[{"common_name": "Neem", "water_needs": {"mature": "40 liters per week"}, "sunlight": {"daily_hours": "6-8 hours"}}]"""
            response = generate_chat_completion(test_prompt, models[0], temperature=0.3, max_tokens=100)
            
            if response:
                print("✅ Local AI is responding!")
                print(f"Response: {response[:100]}...")
                return True
            else:
                print("❌ Local AI is not responding")
                return False
        else:
            print("❌ No models loaded in LM Studio")
            return False
    else:
        print("❌ LM Studio is not running or not accessible")
        print("Please make sure:")
        print("1. LM Studio is installed and running")
        print("2. LM Studio server is started (lms server start)")
        print("3. A model is loaded in LM Studio")
        print("4. Server is running on http://127.0.0.1:1234")
        return False

if __name__ == "__main__":
    # Test the connection when running directly
    test_local_connection()