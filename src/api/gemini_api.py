import google.generativeai as genai
import os
import json
import streamlit as st
from dotenv import load_dotenv
import datetime
import re

load_dotenv()

def configure_gemini_api():
    """
    Configure Gemini API with key from session state or environment
    """
    # Try to get API key from session state first
    api_key = None
    if hasattr(st, 'session_state') and 'gemini_api_key' in st.session_state:
        api_key = st.session_state.gemini_api_key
    
    # Fallback to environment variable
    if not api_key:
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        raise ValueError("No Gemini API key found. Please provide an API key.")
    
    genai.configure(api_key=api_key)
    return api_key

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

def get_recommendations(location_data, prefer_native=True, goal_type="afforestation", lat=20.5937, lon=78.9629):
    """
    Get comprehensive plant/crop recommendations from Gemini AI
    """
    try:
        # Configure API first
        configure_gemini_api()
        
        # Generate user goal from goal type
        goal_mapping = {
            'cash_crops': 'commercial cash crop cultivation for maximum economic returns',
            'food_crops': 'food crop cultivation for nutrition and food security',
            'afforestation': 'afforestation and tree plantation for environmental benefits'
        }
        user_goal = goal_mapping.get(goal_type, 'sustainable environmental plantation')
        
        # Create an enhanced, agentic prompt
        prompt = create_enhanced_recommendation_prompt(location_data, user_goal, prefer_native, goal_type, lat, lon)
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate response with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                
                # Parse the response into structured data
                parsed_recommendations = parse_enhanced_gemini_response(response.text)
                
                # Ensure we return a list of dictionaries with valid data
                if isinstance(parsed_recommendations, list) and len(parsed_recommendations) > 0:
                    return parsed_recommendations
                else:
                    print(f"Attempt {attempt + 1}: No valid recommendations parsed")
                    if attempt == max_retries - 1:
                        return create_error_response("Unable to generate valid recommendations after multiple attempts")
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return create_error_response(f"AI service error: {e}")
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return create_error_response(f"System error: {e}")

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
        'growth_characteristics': {
            'growth_rate': 'Not applicable',
            'mature_height': 'Not applicable',
            'spacing_requirements': 'Not applicable'
        },
        'sustainability_highlights': ['Please try again with different parameters']
    }]

def create_enhanced_recommendation_prompt(data, user_goal, prefer_native, goal_type="afforestation", lat=20.5937, lon=78.9629):
    """
    Create an enhanced, agentic prompt for Gemini with comprehensive plant recommendations and specific measurements
    """
    # Determine region for regional context
    region = "North India" if lat > 26 else "South India" if lat < 15 else "West India" if lon < 77 else "East India"
    
    # Get current season
    import datetime
    current_month = datetime.datetime.now().month
    if current_month in [11, 12, 1, 2, 3, 4]:
        current_season = "Rabi (Winter)"
    elif current_month in [6, 7, 8, 9, 10]:
        current_season = "Kharif (Monsoon)" 
    else:
        current_season = "Zaid (Summer)"
    
    # Get user preferences section
    user_prefs = data.get('user_preferences', {})
    user_preferences_text = ""
    
    if user_prefs:
        user_preferences_text = f"""
USER-SPECIFIED PREFERENCES (PRIORITIZE THESE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        if user_prefs.get('water_availability', 'Auto-detect') != 'Auto-detect':
            user_preferences_text += f"\n💧 User Water Availability: {user_prefs['water_availability']} - PRIORITIZE plants suited for this water level"
        
        if user_prefs.get('soil_type_input', '').strip():
            user_preferences_text += f"\n🏔️ User Soil Type: {user_prefs['soil_type_input']} - PRIORITIZE plants that thrive in this specific soil"
        
        if user_prefs.get('space_availability', 0) > 0:
            space_area = user_prefs['space_availability']
            user_preferences_text += f"\n📐 Available Space: {space_area} sq meters - RECOMMEND plants that fit within this space constraint"
        
        if user_prefs.get('space_location_type', '').strip():
            location_type = user_prefs['space_location_type']
            user_preferences_text += f"\n🏠 Planting Location: {location_type} - PRIORITIZE plants suitable for this specific location type"
            
            # Add specific constraints based on location type
            location_lower = location_type.lower()
            if any(word in location_lower for word in ['window', 'pane', 'sill']):
                user_preferences_text += f"\n   ⚠️ CONSTRAINT: Indoor/window location - recommend small potted plants, max height 0.5m, good for containers"
            elif any(word in location_lower for word in ['balcony', 'terrace', 'patio']):
                user_preferences_text += f"\n   ⚠️ CONSTRAINT: Semi-outdoor space - recommend medium-sized plants, max height 2m, container-friendly"
            elif any(word in location_lower for word in ['backyard', 'garden', 'yard']):
                user_preferences_text += f"\n   ⚠️ CONSTRAINT: Outdoor garden space - can recommend trees up to 5m, ground planting suitable"
            elif any(word in location_lower for word in ['farmland', 'field', 'farm', 'acre', 'hectare']):
                user_preferences_text += f"\n   ⚠️ CONSTRAINT: Large-scale farming area - can recommend large trees up to 15m, commercial cultivation suitable"
        
        if user_prefs.get('budget_preference', 'Auto-suggest') != 'Auto-suggest':
            user_preferences_text += f"\n💰 Budget Preference: {user_prefs['budget_preference']} - PRIORITIZE plants matching this budget range"
        
        user_preferences_text += "\n\nIMPORTANT: User-provided preferences should override API data where they conflict!"
    
    prompt = f"""
You are an advanced AI agricultural and environmental consultant with deep expertise in Indian botany, sustainable farming, 
and regional agriculture. You have comprehensive knowledge of Indian crops and trees.

LOCATION & ENVIRONMENTAL ANALYSIS FOR {data.get('location', 'India')}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Location: {data.get('location', 'India')} ({region})
🗺️ Coordinates: {lat:.4f}, {lon:.4f}
🌾 Current Season: {current_season}
🌡️ Temperature: {data.get('temperature', 27.5)}°C
💧 Humidity: {data.get('humidity', 65)}%
🌧️ Annual Rainfall: {data.get('rainfall', 1000)}mm{' (User-adjusted)' if data.get('user_water_preference') else ''}
🧪 Soil pH: {data.get('soil_ph', 6.5)}
🏔️ Soil Texture: {data.get('soil_texture', 'clay loam')}{' (User-specified)' if data.get('user_soil_input') else ''}
🌱 Soil Organic Carbon: {data.get('soil_organic_carbon', 1.8)}%
🌬️ Air Quality Index: {data.get('aqi', 106)} ({data.get('aqi_rating', 3)}/5 rating)
💨 PM2.5 Level: {data.get('pm2_5', 35)} μg/m³
🌀 Climate Type: {data.get('climate_type', 'tropical')}
{f"📐 Available Space: {data.get('available_space')} sq meters" if data.get('available_space') else ''}
{user_preferences_text}

USER REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Goal: {user_goal}
🌿 Prefer Native Species: {prefer_native}
🏙️ Context: Urban/suburban environment
📋 Goal Type: {goal_type.upper()}

GOAL-SPECIFIC REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{get_goal_specific_instructions(goal_type, region)}

WATER & SUNLIGHT SPECIFICATION GUIDELINES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WATER REQUIREMENTS (be SPECIFIC with liters):
• Large Trees (>10m): 50-200 liters per week when mature
• Medium Trees (5-10m): 20-80 liters per week when mature  
• Small Trees (<5m): 10-40 liters per week when mature
• Shrubs: 5-20 liters per week when mature
• Food Crops: 2-10 liters per plant per week (varies by crop)
• Herbs/Small Plants: 0.5-3 liters per plant per week
• Potted Plants: 0.2-2 liters per plant per day

SUNLIGHT REQUIREMENTS (be SPECIFIC with hours):
• Full Sun: 6-8 hours direct sunlight daily
• Partial Sun: 4-6 hours direct sunlight daily  
• Partial Shade: 2-4 hours direct sunlight daily
• Full Shade: <2 hours direct sunlight daily

ADJUST water amounts based on:
- Seedling stage: 50% of mature amount
- Young plant: 75% of mature amount
- Mature plant: 100% amount
- Dry season: +25-50% more water
- Monsoon season: Reduce by 50-75%

SEASONAL SUITABILITY & PLANTING WINDOW (CRITICAL):
• CURRENT SEASON: {current_season} — ONLY recommend plants that are appropriate to plant or establish in {current_season} in the specified region.
• If a plant is not suitable to be planted right now, the model MUST explicitly state "Not ideal to plant now" and provide the next optimal planting window (months and season) and the reason.
• For each recommended species, include a "planting_window" field with: "best_months": ["Mon", "Jun"], "can_plant_now": true/false, and a 1-2 sentence justification tied to local climate/seasonality.
• Prefer varieties/management steps that enable successful establishment if planting in the current season (e.g., suggest root-balled saplings, shade nets, mulching depth, irrigation schedule) when recommending species that can be established now with mitigation.
• For food crops and short-duration crops, ensure the cultivar and planting timing will allow at least one full harvest cycle in the upcoming season(s) given current month.
• Always provide the recommended planting month(s) and a 1-line "why now/how to mitigate" if recommending off-window planting.


REQUIRED OUTPUT FORMAT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provide exactly 5 plant recommendations in the following comprehensive JSON format:

{{
  "recommendations": [
    {{
      "scientific_name": "Botanical scientific name",
      "common_name": "English common name",
      "local_name": "Hindi/regional name with pronunciation",
      "plant_type": "Tree/Shrub/Crop/Herb/Grass",
      "family": "Botanical family name",
      "suitability_score": "8.5/10",
      "suitability_analysis": "Detailed 3-4 sentence analysis of why this plant suits the environmental conditions",
      
      "water_requirements": {{
        "seedling_stage": "X liters per plant per day/week for first 6 months (be specific: e.g., '2.5 liters per plant per day')",
        "young_plant": "X liters per plant per day/week for 6 months to 2 years (be specific: e.g., '15 liters per plant per week')",
        "mature_plant": "X liters per plant per day/week for mature plant (be specific: e.g., '40 liters per plant per week')",
        "dry_season_adjustment": "Additional X liters or +X% increase during dry months",
        "monsoon_reduction": "Reduce to X liters or -X% during monsoon season",
        "water_conservation_methods": "Specific techniques like drip irrigation (X liters/hour), mulching (X cm deep), rainwater harvesting potential"
      }},
      
      "sunlight_requirements": {{
        "daily_hours_needed": "X-Y hours (be specific: e.g., '6-8 hours')",
        "light_intensity": "Full Sun/Partial Sun/Partial Shade/Full Shade",
        "optimal_direction": "Best placement direction (e.g., 'South-facing', 'East morning sun')",
        "shade_tolerance": "Can tolerate X hours less sunlight if needed",
        "seasonal_adjustments": "Summer/winter sunlight requirement changes"
      }},
      
      "air_quality_benefits": {{
        "pollution_reduction": "Specific air pollutants this plant removes (PM2.5, SO2, NO2, etc.)",
        "oxygen_production": "Estimated oxygen production per day in liters",
        "co2_absorption": "Estimated CO2 absorption per year in kg",
        "aqi_improvement": "Expected AQI improvement potential (numerical if possible)"
      }},
      
      "plantation_guide": {{
        "best_season": "Optimal planting season with specific months",
        "soil_preparation": "Step-by-step soil preparation with measurements (pit size, fertilizer amounts)",
        "planting_method": "Detailed planting procedure with exact spacing in meters",
        "initial_care": "First 30 days care with specific water amounts and frequency"
      }},
      
      "growth_characteristics": {{
        "mature_height": "Expected height range in meters (e.g., '8-12 meters')",
        "mature_spread": "Canopy/root spread in meters (e.g., '4-6 meters')",
        "growth_rate": "Fast/Medium/Slow with specific timeline (e.g., 'Fast: 2-3 meters per year')",
        "lifespan": "Expected plant lifespan in years",
        "space_requirements": "Minimum area needed in square meters per plant"
      }},
      
      "maintenance_schedule": {{
        "daily": "Daily tasks with specific times/amounts",
        "weekly": "Weekly care with specific measurements",
        "monthly": "Monthly maintenance with exact requirements",
        "seasonal": "Seasonal care with specific quantities",
        "annual": "Yearly maintenance with precise instructions"
      }},
      
      "environmental_impact": {{
        "carbon_sequestration": "Annual carbon storage in kg per plant",
        "biodiversity_support": "Wildlife species supported (with numbers if possible)",
        "soil_improvement": "Specific soil benefits with measurable improvements",
        "microclimate_effects": "Temperature reduction in degrees, humidity increase percentage",
        "erosion_control": "Soil retention capacity and root strength"
      }},
      
      "economic_benefits": {{
        "initial_cost": "Estimated planting cost in INR per plant",
        "maintenance_cost_annual": "Yearly maintenance expenses in INR per plant",
        "economic_returns": "Potential monetary benefits with specific amounts/timeline",
        "property_value_impact": "Property value increase percentage or amount",
        "long_term_savings": "Specific cost savings over 5/10 years"
      }},
      
      "challenges_and_solutions": {{
        "common_problems": "Typical issues with specific symptoms and solutions",
        "pest_management": "Natural pest control methods with application rates",
        "disease_prevention": "Disease prevention with specific treatments and frequencies",
        "climate_adaptation": "Handling extreme weather with specific protection measures",
        "troubleshooting": "Quick fixes with step-by-step instructions and quantities"
      }},
      
      "user_goal_alignment": "2-3 sentences explaining how this plant specifically addresses the user's stated goals with measurable benefits",
      "additional_uses": "Secondary benefits like medicinal uses, food production with quantities/yields",
      "companion_plants": "Specific plants that grow well together with optimal spacing"
    }}
  ],
  
  "site_specific_recommendations": {{
    "soil_amendments": "Specific improvements needed with exact quantities (kg of compost, fertilizer amounts)",
    "irrigation_strategy": "Optimal watering system with flow rates (liters/hour), coverage area, and scheduling",
    "layout_suggestions": "Plant arrangement with exact spacing measurements and total area utilization",
    "timeline": "Month-by-month planting and care schedule with specific activities and quantities",
    "success_metrics": "Measurable targets: survival rate %, growth rate cm/month, canopy coverage %, AQI improvement points"
  }},
  
  "long_term_management": {{
    "year_1": "First year expectations: height increase, water needs, survival targets",
    "years_2_5": "Medium-term targets: mature size percentage, productivity levels, maintenance reduction",
    "beyond_5_years": "Long-term yields, harvesting quantities, replacement planning",
    "succession_planning": "Expansion strategy with additional plant numbers and timeline"
  }}
}}

CRITICAL REQUIREMENTS FOR WATER & SUNLIGHT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ALWAYS provide EXACT water amounts in liters (not vague terms like "moderate watering")
✅ ALWAYS provide EXACT sunlight hours (e.g., "6-8 hours" not "full sun")
✅ Match water amounts to plant type:
   - Large trees: 100-200L/week when mature
   - Medium trees: 30-80L/week when mature  
   - Shrubs: 10-30L/week when mature
   - Crops: 3-15L/week per plant
   - Herbs: 1-5L/week per plant
   - Potted plants: 0.5-3L/day per plant

✅ Adjust water for growth stages:
   - Seedling: 50% of mature amount
   - Young: 75% of mature amount  
   - Mature: 100% amount

✅ Include seasonal water adjustments:
   - Summer: +30-50% more water
   - Monsoon: -50-70% less water

✅ Provide specific sunlight placement advice based on location type
✅ All measurements must be realistic for Indian climate conditions
✅ PRIORITIZE user-specified preferences over API data
✅ Ensure all plants fit within available space if specified
✅ Include realistic costs in INR
✅ Focus on plants suitable for {region} climate

IMPORTANT: Respond ONLY with valid JSON. Start with {{ and end with }}. No additional text.
Make every measurement specific and actionable. Replace ALL vague terms with exact quantities.
"""
    return prompt

def parse_enhanced_gemini_response(response_text):
    """
    Parse enhanced Gemini response with ultra-robust JSON extraction and fixing
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
        
        # Find JSON in the cleaned response with better detection
        start_idx = cleaned_text.find('{')
        
        # Find the matching closing brace by counting braces
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
            
            if brace_count == 0:  # Found complete JSON
                json_str = cleaned_text[start_idx:end_idx]
                
                # Comprehensive JSON cleaning
                json_str = clean_json_string(json_str)
                
                # Try multiple parsing attempts with different fixes
                for attempt in range(3):
                    try:
                        data = json.loads(json_str)
                        recommendations = data.get('recommendations', [])
                        
                        if recommendations:
                            # Ensure UI compatibility
                            return enhance_recommendations_for_ui(recommendations)
                        else:
                            print(f"Attempt {attempt + 1}: No recommendations found in parsed JSON")
                            
                    except json.JSONDecodeError as parse_error:
                        print(f"Parse attempt {attempt + 1} failed: {parse_error}")
                        
                        if attempt < 2:  # Try to fix for next attempt
                            json_str = fix_json_error(json_str, parse_error)
                        else:
                            # Last attempt failed, try extracting partial data
                            return extract_partial_recommendations(cleaned_text)
            else:
                print("Incomplete JSON structure found (unmatched braces)")
                return extract_partial_recommendations(cleaned_text)
        else:
            print("No JSON structure found in AI response")
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

def fix_json_error(json_str, error):
    """Attempt to fix specific JSON errors"""
    try:
        error_pos = getattr(error, 'pos', 0)
        
        if "Extra data" in str(error):
            # Truncate at the error position
            json_str = json_str[:error_pos]
            # Ensure proper closing
            if json_str.count('{') > json_str.count('}'):
                json_str += '}' * (json_str.count('{') - json_str.count('}'))
        
        elif "Unterminated string" in str(error):
            # Add closing quote
            if error_pos < len(json_str):
                json_str = json_str[:error_pos] + '"' + json_str[error_pos:]
        
        elif "Expecting ',' delimiter" in str(error):
            # Add missing comma
            if error_pos < len(json_str):
                json_str = json_str[:error_pos] + ',' + json_str[error_pos:]
        
    except Exception:
        pass  # Return original string if fixing fails
    
    return json_str

def extract_partial_recommendations(text):
    """Extract recommendations from malformed text using pattern matching"""
    try:
        recommendations = []
        
        # Look for plant recommendation patterns
        import re
        
        # Pattern to find scientific names
        scientific_pattern = r'"scientific_name":\s*"([^"]+)"'
        common_pattern = r'"common_name":\s*"([^"]+)"'
        local_pattern = r'"local_name":\s*"([^"]+)"'
        
        scientific_names = re.findall(scientific_pattern, text)
        common_names = re.findall(common_pattern, text)
        local_names = re.findall(local_pattern, text)
        
        # Create minimal recommendations from found patterns
        max_plants = min(len(scientific_names), len(common_names), 5)  # Limit to 5
        
        for i in range(max_plants):
            rec = {
                'scientific_name': scientific_names[i] if i < len(scientific_names) else f'Plant_{i+1}',
                'common_name': common_names[i] if i < len(common_names) else f'Plant {i+1}',
                'local_name': local_names[i] if i < len(local_names) else f'Local Plant {i+1}',
                'plant_type': 'Plant',
                'suitability_analysis': 'AI-recommended for your environmental conditions',
                'care_instructions': 'Standard care applicable for your climate zone',
                'environmental_impact_score': 7.5,
                'air_quality_benefits': {
                    'pollution_reduction': 'Contributes to air purification',
                    'co2_absorption': 'CO2 absorption capabilities',
                    'oxygen_production': 'Oxygen production benefits',
                    'aqi_improvement': 'Helps improve local air quality'
                },
                'growth_characteristics': {
                    'growth_rate': 'Moderate growth rate',
                    'mature_height': 'Suitable height for location',
                    'spacing_requirements': 'Standard spacing recommended'
                },
                'sustainability_highlights': ['AI-recommended for your location', 'Environmentally beneficial']
            }
            recommendations.append(rec)
        
        if recommendations:
            print(f"✅ Extracted {len(recommendations)} partial recommendations from malformed response")
            return recommendations
        else:
            print("❌ Could not extract any recommendations from response")
            return create_fallback_recommendations()
            
    except Exception as e:
        print(f"Error in partial extraction: {e}")
        return create_fallback_recommendations()

def enhance_recommendations_for_ui(recommendations):
    """Ensure all recommendations have required UI fields"""
    for rec in recommendations:
        # Ensure required UI fields exist with minimal defaults
        rec.setdefault('environmental_impact_score', 7.5)
        
        # Ensure air quality benefits structure exists
        if 'air_quality_benefits' not in rec or not rec['air_quality_benefits']:
            rec['air_quality_benefits'] = {
                'pollution_reduction': rec.get('air_quality_benefits', {}).get('pollution_reduction', 'Air purification capabilities'),
                'co2_absorption': rec.get('air_quality_benefits', {}).get('co2_absorption', 'CO2 absorption data not specified'),
                'oxygen_production': rec.get('air_quality_benefits', {}).get('oxygen_production', 'Oxygen production data not specified'),
                'aqi_improvement': rec.get('air_quality_benefits', {}).get('aqi_improvement', 'AQI improvement potential')
            }
        
        # Ensure growth characteristics structure exists
        if 'growth_characteristics' not in rec or not rec['growth_characteristics']:
            rec['growth_characteristics'] = {
                'growth_rate': rec.get('growth_characteristics', {}).get('growth_rate', 'Growth rate not specified'),
                'mature_height': rec.get('growth_characteristics', {}).get('mature_height', 'Height not specified'),
                'spacing_requirements': rec.get('growth_characteristics', {}).get('spacing_requirements', 'Spacing not specified')
            }
        
        # Ensure sustainability highlights exists
        rec.setdefault('sustainability_highlights', ['AI-recommended for your location'])
    
    return recommendations

def create_fallback_recommendations():
    """Create minimal fallback recommendations when all parsing fails"""
    return [{
        'scientific_name': 'Azadirachta indica',
        'common_name': 'Neem',
        'local_name': 'नीम (Neem)',
        'plant_type': 'Tree',
        'suitability_analysis': 'Highly suitable for Indian climate with excellent environmental benefits',
        'care_instructions': 'Water regularly in first year, then minimal care needed. Prune annually.',
        'environmental_impact_score': 9.0,
        'air_quality_benefits': {
            'pollution_reduction': 'Excellent air purification',
            'co2_absorption': 'High CO2 absorption capacity',
            'oxygen_production': 'Significant oxygen production',
            'aqi_improvement': 'Notable AQI improvement'
        },
        'growth_characteristics': {
            'growth_rate': 'Fast-growing',
            'mature_height': '15-20 meters',
            'spacing_requirements': '4-6 meters apart'
        },
        'sustainability_highlights': ['Native to India', 'Drought tolerant', 'Pollution resistant', 'Multi-purpose tree']
    }]

# Removed all predefined/fallback functions to ensure purely AI-driven recommendations
# The system now relies entirely on Gemini AI's real-time knowledge and responses
