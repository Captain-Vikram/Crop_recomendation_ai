import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

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

def get_recommendations(location_data, user_goal="sustainable urban afforestation", prefer_native=True, goal_type="afforestation", lat=20.5937, lon=78.9629):
    """
    Get comprehensive plant/crop recommendations from Gemini AI - Pure AI-driven approach
    """
    try:
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
    Create an enhanced, agentic prompt for comprehensive plant recommendations
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
🌬️ Air Quality Index: {data.get('aqi', 3)} (1=Excellent, 5=Hazardous)
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

INDIAN CROP/PLANT KNOWLEDGE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For {region}, prioritize regionally adapted varieties:
- Use local/Hindi names alongside scientific names
- Consider seasonal growing patterns (Kharif/Rabi/Zaid)
- Include traditional varieties with cultural significance
- Focus on climate-resilient and drought-tolerant options
- Recommend established market varieties with good supply chains

AGENTIC THINKING PROCESS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please think through this systematically:

1. ENVIRONMENTAL ASSESSMENT: Analyze the soil, climate, and air quality conditions
2. USER PREFERENCES: PRIORITIZE user-specified preferences over API data
3. GOAL ALIGNMENT: Match plant species to the specific user goals
4. SPACE CONSTRAINTS: Ensure recommendations fit within available space
5. BUDGET CONSIDERATION: Match plant costs to user budget preferences
6. NATIVE PREFERENCE: Prioritize indigenous species if requested
7. URBAN ADAPTATION: Consider pollution tolerance and space constraints
8. SUSTAINABILITY: Focus on long-term ecosystem benefits

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
      
      "air_quality_benefits": {{
        "pollution_reduction": "Specific air pollutants this plant removes (PM2.5, SO2, NO2, etc.)",
        "oxygen_production": "Estimated oxygen production per day",
        "co2_absorption": "Estimated CO2 absorption per year",
        "aqi_improvement": "Expected AQI improvement potential"
      }},
      
      "plantation_guide": {{
        "best_season": "Optimal planting season with months",
        "soil_preparation": "Step-by-step soil preparation instructions",
        "planting_method": "Detailed planting procedure with spacing",
        "initial_care": "First 30 days care instructions"
      }},
      
      "watering_patterns": {{
        "seedling_stage": "Daily water requirements for first 6 months",
        "young_plant": "Watering schedule for 6 months to 2 years", 
        "mature_plant": "Long-term watering needs",
        "seasonal_variations": "Adjustments for monsoon/dry seasons",
        "water_conservation_tips": "Techniques to minimize water usage"
      }},
      
      "growth_characteristics": {{
        "mature_height": "Expected height with range",
        "mature_spread": "Canopy/root spread",
        "growth_rate": "Fast/Medium/Slow with timeline",
        "lifespan": "Expected plant lifespan",
        "space_requirements": "Minimum area needed"
      }},
      
      "maintenance_schedule": {{
        "daily": "Daily maintenance tasks",
        "weekly": "Weekly care requirements",
        "monthly": "Monthly maintenance",
        "seasonal": "Seasonal care activities",
        "annual": "Yearly maintenance tasks"
      }},
      
      "environmental_impact": {{
        "carbon_sequestration": "Annual carbon storage capacity",
        "biodiversity_support": "Wildlife and ecosystem benefits",
        "soil_improvement": "How it enhances soil quality",
        "microclimate_effects": "Local climate modification",
        "erosion_control": "Soil conservation benefits"
      }},
      
      "economic_benefits": {{
        "initial_cost": "Estimated planting cost",
        "maintenance_cost_annual": "Yearly maintenance expenses",
        "economic_returns": "Potential monetary benefits (fruit, timber, etc.)",
        "property_value_impact": "Effect on land/property value",
        "long_term_savings": "Cost savings over time"
      }},
      
      "challenges_and_solutions": {{
        "common_problems": "Typical issues faced during cultivation",
        "pest_management": "Natural pest control methods",
        "disease_prevention": "Disease prevention strategies",
        "climate_adaptation": "Handling extreme weather",
        "troubleshooting": "Quick fixes for common issues"
      }},
      
      "user_goal_alignment": "2-3 sentences explaining how this plant specifically addresses the user's stated goals",
      "additional_uses": "Secondary benefits like medicinal uses, food production, etc.",
      "companion_plants": "Plants that grow well together with this species"
    }}
  ],
  
  "site_specific_recommendations": {{
    "soil_amendments": "Specific improvements needed for this location",
    "irrigation_strategy": "Optimal watering system for local conditions", 
    "layout_suggestions": "Recommended spatial arrangement of plants",
    "timeline": "Month-by-month planting and care schedule",
    "success_metrics": "How to measure plantation success"
  }},
  
  "long_term_management": {{
    "year_1": "First year expectations and care",
    "years_2_5": "Medium-term management strategy",
    "beyond_5_years": "Long-term maintenance and harvesting",
    "succession_planning": "How to expand or replace plants over time"
  }}
}}

CRITICAL REQUIREMENTS:
- PRIORITIZE user-specified preferences over API data (water, soil, space, budget)
- Ensure all plants fit within the available space if specified
- Match budget preferences when provided
- Ensure all plants are suitable for the specific environmental conditions provided
- Focus heavily on air quality improvement given the urban context
- Provide actionable, location-specific advice
- Include realistic timelines and costs
- Prioritize drought tolerance and low maintenance where appropriate
- Consider the user's specific goals throughout all recommendations
{f"- SPACE CONSTRAINT: All recommended plants must fit within {data.get('available_space')} sq meters total" if data.get('available_space') else ''}
{f"- BUDGET CONSTRAINT: Match {data.get('budget_preference')} range in cost recommendations" if data.get('budget_preference') and data.get('budget_preference') != 'Auto-suggest' else ''}

Make the response comprehensive, practical, and scientifically accurate.
"""
    return prompt

def parse_enhanced_gemini_response(response_text):
    """
    Parse enhanced Gemini response with robust JSON cleaning
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
        
        # Find JSON in the cleaned response
        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned_text[start_idx:end_idx]
            
            # Additional JSON cleaning to fix common issues
            json_str = json_str.replace('\n', ' ')  # Remove newlines within JSON
            json_str = json_str.replace('\t', ' ')  # Remove tabs
            # Fix common AI mistakes in JSON
            json_str = json_str.replace('"...', '""')  # Replace unfinished strings
            json_str = json_str.replace('...', '')     # Remove ellipsis
            json_str = json_str.replace('"",', '",')   # Fix double commas
            
            # Try to parse - if it fails, attempt basic fixes
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as parse_error:
                print(f"First parse attempt failed: {parse_error}")
                print(f"Attempting to fix JSON around error position...")
                
                # Try to fix the specific error area
                error_pos = getattr(parse_error, 'pos', 0)
                if error_pos > 0 and error_pos < len(json_str):
                    # Look for common issues around the error position
                    before = json_str[:error_pos]
                    after = json_str[error_pos:]
                    
                    # Fix unescaped quotes or incomplete strings
                    if after.startswith('"') and not before.endswith('\\'):
                        # Look for the next complete JSON field
                        next_quote = after.find('"', 1)
                        if next_quote > 0:
                            fixed_content = after[1:next_quote].replace('"', '\\"')
                            json_str = before + '"' + fixed_content + '"' + after[next_quote+1:]
                    
                    # Try parsing again
                    data = json.loads(json_str)
            
            recommendations = data.get('recommendations', [])
            
            # Only add essential default values for UI compatibility
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
        else:
            print("No valid JSON structure found in AI response")
            return []
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response text preview: {response_text[:500]}...")
        return []
    except Exception as e:
        print(f"Parsing error: {e}")
        return []

# Removed all predefined/fallback functions to ensure purely AI-driven recommendations
# The system now relies entirely on Gemini AI's real-time knowledge and responses
