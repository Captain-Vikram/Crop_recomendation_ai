import streamlit as st
import re

def extract_number_from_text(text):
    """
    Extract the first number from a text string, handling various formats
    """
    if not text:
        return 25  # Default value
    
    # Remove common prefixes and find numbers
    text = str(text).lower()
    
    # Look for patterns like "25 kg", "about 30 liters", "approximately 20-25 kg"
    number_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:kg|liters?|l)',  # "25 kg" or "30 liters"
        r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)',     # "20-25" (take the first number)
        r'(\d+(?:\.\d+)?)',                     # Any number
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Take the first match and first group
            match = matches[0]
            if isinstance(match, tuple):
                # For ranges like "20-25", take the first number
                return int(float(match[0]))
            else:
                return int(float(match))
    
    return 25  # Default fallback

def create_minimal_sidebar():
    """
    Create a minimal sidebar with only essential information
    """
    st.sidebar.title("🌱 Plant Recommendation AI")
    
    # AI Model Selection
    st.sidebar.markdown("### 🤖 AI Model Selection")
    
    # Check if LM Studio is available
    try:
        from api.local_api import check_lm_studio_connection
        lm_studio_available = check_lm_studio_connection()
    except Exception:
        lm_studio_available = False
    
    if lm_studio_available:
        ai_options = ["🌐 Web AI (Gemini)", "🏠 Local AI (LM Studio)"]
        ai_help = "Choose between online Gemini AI or your local LM Studio model"
    else:
        ai_options = ["🌐 Web AI (Gemini)"]
        ai_help = "Local AI not available. Make sure LM Studio is running with a loaded model."
    
    ai_choice = st.sidebar.radio(
        "Select AI Model:",
        ai_options,
        index=ai_options.index(st.session_state.get('ai_model_choice', ai_options[0])) if st.session_state.get('ai_model_choice', ai_options[0]) in ai_options else 0,
        help=ai_help
    )
    
    # Store AI choice in session state only if it actually changed
    if st.session_state.get('ai_model_choice') != ai_choice:
        st.session_state.ai_model_choice = ai_choice
        # Clear previous recommendations when switching models
        if 'recommendations' in st.session_state:
            del st.session_state.recommendations
        if 'env_data' in st.session_state:
            del st.session_state.env_data
    
    # Show model status
    if "Local AI" in ai_choice:
        if lm_studio_available:
            st.sidebar.success("✅ LM Studio Connected")
            try:
                from api.local_api import get_available_models
                models = get_available_models()
                if models:
                    st.sidebar.info(f"📦 Models: {len(models)} available")
                    # Show first few model names
                    for model in models[:2]:
                        st.sidebar.text(f"• {model[:30]}...")
                else:
                    st.sidebar.warning("⚠️ No models loaded")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {e}")
        else:
            st.sidebar.error("❌ LM Studio Not Available")
            st.sidebar.markdown("""
            **To use Local AI:**
            1. Install LM Studio
            2. Start the server: `lms server start`
            3. Load a model (llama-3.2-3b-crop-recommender)
            4. Ensure server runs on http://127.0.0.1:1234
            """)
    else:
        st.sidebar.success("✅ Gemini AI Ready")
        st.sidebar.info("Using Google Gemini 1.5 Flash")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📍 Location Selection")
    st.sidebar.info("Use the main interface to select your location via interactive map or manual input.")
    
    st.sidebar.markdown("### 🎯 How It Works")
    st.sidebar.markdown("""
    1. **Select Location** - Choose via map or enter PIN/city
    2. **Set Goals** - Define your planting objectives  
    3. **Get AI Recommendations** - Receive personalized suggestions
    4. **Follow Guides** - Implement detailed plantation plans
    """)
    
    st.sidebar.markdown("### 🌱 Features")
    st.sidebar.markdown("""
    - **AI-Powered Analysis** - Smart environmental assessment
    - **Comprehensive Guides** - Step-by-step plantation instructions
    - **Air Quality Focus** - Pollution reduction strategies
    - **Native Species Priority** - Local ecosystem support
    - **Economic Analysis** - Cost-benefit insights
    """)
    
    st.sidebar.markdown("### 📊 Environmental Impact")
    if 'recommendations' in st.session_state and st.session_state.recommendations:
        recs = st.session_state.recommendations
        total_co2 = sum(extract_number_from_text(plant.get('air_quality_benefits', {}).get('co2_absorption', '25 kg')) for plant in recs)
        total_oxygen = sum(extract_number_from_text(plant.get('air_quality_benefits', {}).get('oxygen_production', '25 liters')) for plant in recs)
        
        ai_model_used = "🏠 Local AI" if "Local AI" in st.session_state.get('ai_model_choice', '') else "🌐 Web AI"
        
        st.sidebar.success(f"""
        **Your Selected Plants Will:**
        - Absorb {total_co2} kg CO2/year
        - Produce {total_oxygen} L oxygen/day
        - Improve local air quality
        - Support biodiversity
        
        *Generated by {ai_model_used}*
        """)
    
    return {
        "minimal_sidebar": True, 
        "ai_choice": ai_choice,
        "lm_studio_available": lm_studio_available
    }

def create_sidebar_inputs():
    """
    Legacy function - kept for compatibility, now redirects to minimal sidebar
    """
    return create_minimal_sidebar()

def display_environmental_summary(env_data, user_preferences=None):
    """
    Display environmental conditions summary with user preference indicators
    """
    st.subheader("🌍 Environmental Conditions")
    
    # Show user preference context if available
    if user_preferences:
        preference_items = []
        if user_preferences.get('soil_type'):
            preference_items.append(f"👤 Soil: {user_preferences['soil_type']}")
        if user_preferences.get('water_availability'):
            preference_items.append(f"👤 Water: {user_preferences['water_availability']}")
        if user_preferences.get('space_constraint'):
            preference_items.append(f"👤 Space: {user_preferences['space_constraint']}")
        
        if preference_items:
            st.info(f"📋 Your Preferences: {' • '.join(preference_items)}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Temperature from API
        st.metric(
            "🌡️ Temperature",
            f"{env_data.get('temperature', 0):.1f}°C",
            help="Current temperature from weather API"
        )
        
        # Rainfall - show user preference indicator if overridden
        rainfall_value = env_data.get('rainfall', 0)
        rainfall_help = "Annual rainfall estimate"
        if user_preferences and user_preferences.get('water_availability') in ['Limited', 'Abundant']:
            rainfall_help += f" (👤 User preference: {user_preferences['water_availability']} water)"
        
        st.metric(
            "🌧️ Rainfall",
            f"{rainfall_value} mm/year",
            help=rainfall_help
        )
        
        st.metric(
            "💧 Humidity",
            f"{env_data.get('humidity', 0)}%",
            help="Relative humidity from weather API"
        )
    
    with col2:
        # Soil pH - show user preference indicator if specified  
        soil_ph = env_data.get('soil_ph', 6.5)
        soil_help = "Soil acidity/alkalinity"
        if user_preferences and user_preferences.get('soil_type'):
            soil_help += f" (👤 User soil type: {user_preferences['soil_type']})"
        
        st.metric(
            "🌱 Soil pH",
            f"{soil_ph:.1f}",
            help=soil_help
        )
        
        # Air Quality - show actual AQI with rating in small text
        aqi_value = env_data.get('aqi', 75)
        aqi_rating = env_data.get('aqi_rating', 3)
        
        # Convert rating to text
        rating_text = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        rating_display = rating_text.get(aqi_rating, "Moderate")
        
        st.metric(
            "💨 Air Quality",
            f"AQI {aqi_value}",
            delta=f"{rating_display} ({aqi_rating}/5)",
            help="Air Quality Index (EPA scale 0-500)"
        )
        st.metric(
            "🏠 PM2.5",
            f"{env_data.get('pm2_5', 0):.1f} μg/m³",
            help="Fine particulate matter concentration"
        )
    
    # Show space constraints if provided
    if user_preferences and user_preferences.get('space_constraint'):
        space_constraint = user_preferences['space_constraint']
        if space_constraint == 'Small (Terrace/Balcony)':
            st.info("🏠 **Space Optimization:** Recommendations tailored for terrace/balcony planting")
        elif space_constraint == 'Medium (Small Garden)':
            st.info("🌿 **Garden Planning:** Recommendations for small garden spaces")
        elif space_constraint == 'Large (Farmland/Estate)':
            st.info("🌳 **Large Scale:** Recommendations for extensive plantation projects")

def display_recommendations(recommendations):
    """
    Display plant recommendations with enhanced formatting and visualizations
    """
    # Safety check: ensure recommendations is a list
    if isinstance(recommendations, str):
        st.error("❌ Unable to parse AI response. Please try again.")
        st.text_area("Raw Response:", recommendations, height=200)
        return
    
    if not recommendations or len(recommendations) == 0:
        st.warning("No recommendations available.")
        return
    
    st.markdown("# 🌿 AI-Powered Plant Recommendations & Plantation Guide")
    st.markdown(f"**Found {len(recommendations)} perfectly matched species for your location and goals**")
    
    # Create summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = sum(float(plant.get('environmental_impact_score', 7.5)) for plant in recommendations) / len(recommendations)
        st.metric("🌍 Avg Environmental Impact", f"{avg_score:.1f}/10")
    
    with col2:
        total_co2 = sum(extract_number_from_text(plant.get('air_quality_benefits', {}).get('co2_absorption', '25 kg')) for plant in recommendations)
        st.metric("🌬️ Total CO2 Absorption", f"{total_co2} kg/year")
    
    with col3:
        native_count = sum(1 for plant in recommendations if 'Native' in plant.get('sustainability_highlights', []))
        st.metric("🇮🇳 Native Species", f"{native_count}/{len(recommendations)}")
    
    with col4:
        fast_growing = sum(1 for plant in recommendations if 'Fast' in plant.get('growth_characteristics', {}).get('growth_rate', ''))
        st.metric("🚀 Fast Growing", f"{fast_growing}/{len(recommendations)}")
    
    st.markdown("---")
    
    # Display individual plant cards
    for i, plant in enumerate(recommendations, 1):
        display_enhanced_plant_card(plant, i)

def display_enhanced_plant_card(plant, index):
    """
    Display an enhanced plant recommendation card with comprehensive information
    """
    # Main plant header with image placeholder
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f7fa 100%);
        padding: 25px;
        border-radius: 15px;
        border-left: 6px solid #4CAF50;
        margin: 20px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    ">
    """, unsafe_allow_html=True)
    
    # Header section
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f'<h3 class="plant-scientific-name">{index}. {plant.get("scientific_name", "Unknown Plant")}</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="plant-common-name">🌱 {plant.get("common_name", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="plant-local-name">🗣️ {plant.get("local_name", "N/A")}</div>', unsafe_allow_html=True)
        st.markdown(f"**🧬 Family:** {plant.get('family', 'Unknown')}")
    # Show quick water & sunlight summary using normalized fields
    water_req = plant.get('water_requirements', {})
    sun_req = plant.get('sunlight_requirements', {})
    water_mature = water_req.get('mature_plant') or water_req.get('mature') or water_req.get('mature') or 'N/A'
    sun_hours = sun_req.get('daily_hours_needed') or sun_req.get('daily_hours') or 'N/A'
    st.markdown(f"**💧 Water (mature):** {water_mature} • **🌞 Sun:** {sun_hours}")
    
    with col2:
        plant_type = plant.get('plant_type', 'Plant')
        type_emoji = get_plant_type_emoji(plant_type)
        st.markdown(f"### {type_emoji} {plant_type}")
        
        score = plant.get('suitability_score', '7.5/10')
        st.markdown(f"**📊 Suitability:** {score}")
    
    with col3:
        # Environmental impact score with color coding
        env_score = plant.get('environmental_impact_score', 7.5)
        score_color = "#4CAF50" if env_score >= 8 else "#FF9800" if env_score >= 6 else "#F44336"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background-color: {score_color}20; border-radius: 10px;">
            <h3 style="color: {score_color}; margin: 0;">🌍 {env_score}/10</h3>
            <p style="margin: 0; font-size: 12px;">Environmental Impact</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sustainability highlights
    highlights = plant.get('sustainability_highlights', [])
    if highlights:
        st.markdown("**✨ Sustainability Highlights:**")
        highlight_text = " • ".join([f"🌟 {h}" for h in highlights])
        st.markdown(highlight_text)
    
    # Tabbed detailed information
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Analysis", "🌬️ Air Quality", "🌱 Plantation Guide", 
        "💧 Watering & Care", "📈 Growth & Economics", "⚠️ Challenges"
    ])
    
    with tab1:
        display_plant_analysis_tab(plant)
    
    with tab2:
        display_air_quality_tab(plant)
    
    with tab3:
        display_plantation_guide_tab(plant)
    
    with tab4:
        display_watering_care_tab(plant)
    
    with tab5:
        display_growth_economics_tab(plant)
    
    with tab6:
        display_challenges_tab(plant)
    
    # Goal alignment summary
    st.markdown("### 🎯 How This Plant Meets Your Goals")
    goal_alignment = plant.get('user_goal_alignment', 'This plant aligns well with your environmental objectives.')
    st.info(goal_alignment)
    
    # Additional uses
    additional_uses = plant.get('additional_uses', '')
    if additional_uses:
        st.markdown(f"**🎁 Bonus Benefits:** {additional_uses}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

def display_plant_analysis_tab(plant):
    """Display plant suitability analysis"""
    analysis = plant.get('suitability_analysis', 'Well-suited for your environmental conditions.')
    st.write(analysis)
    
    # Companion plants
    companions = plant.get('companion_plants', '')
    if companions:
        st.markdown(f"**🤝 Companion Plants:** {companions}")

def display_air_quality_tab(plant):
    """Display air quality benefits"""
    air_benefits = plant.get('air_quality_benefits', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🌬️ Pollution Reduction:**")
        st.write(air_benefits.get('pollution_reduction', 'Improves air quality'))
        
        st.markdown("**💨 AQI Improvement:**")
        st.write(air_benefits.get('aqi_improvement', 'Moderate improvement'))
    
    with col2:
        st.markdown("**🫁 Oxygen Production:**")
        st.write(air_benefits.get('oxygen_production', '20-30 liters/day'))
        
        st.markdown("**🌱 CO2 Absorption:**")
        st.write(air_benefits.get('co2_absorption', '20-25 kg/year'))

def display_plantation_guide_tab(plant):
    """Display plantation guide"""
    guide = plant.get('plantation_guide', {})
    
    st.markdown("**📅 Best Planting Season:**")
    st.write(guide.get('best_season', 'Spring or early monsoon'))

    # Planting window from normalized recommendation
    pw = plant.get('planting_window', {})
    if pw:
        st.markdown("**🗓️ Planting Window (AI):**")
        best_months = pw.get('best_months') or []
        st.write(f"Best months: {', '.join(best_months) if best_months else 'N/A'}")
        can_now = pw.get('can_plant_now')
        if isinstance(can_now, bool):
            st.write(f"Can plant now: {'Yes' if can_now else 'No'}")
        if not can_now:
            st.markdown("**Why not now:**")
            st.write(pw.get('planting_window_justification', 'Not suitable now based on seasonality'))
            st.markdown("**Mitigation / Next best window:**")
            st.write(pw.get('planting_mitigation_steps', 'Use container seedlings, mulching and supplemental irrigation.'))
    
    st.markdown("**🏗️ Soil Preparation:**")
    st.write(guide.get('soil_preparation', 'Prepare well-drained soil with organic matter'))
    
    st.markdown("**🌱 Planting Method:**")
    st.write(guide.get('planting_method', 'Plant at appropriate depth and spacing'))
    
    st.markdown("**👶 Initial Care (First 30 Days):**")
    st.write(guide.get('initial_care', 'Regular watering and protection from extreme weather'))

def display_watering_care_tab(plant):
    """Display watering patterns and maintenance"""
    # Prefer normalized precise water amounts
    water_req = plant.get('water_requirements', {})
    watering = plant.get('watering_patterns', {})
    maintenance = plant.get('maintenance_schedule', {})
    sun_req = plant.get('sunlight_requirements', {})
    
    st.markdown("### 💧 Watering Schedule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🌱 Seedling Stage:**")
        seed = water_req.get('seedling_stage') or watering.get('seedling_stage', 'Daily watering')
        st.write(seed)
        
        st.markdown("**🌿 Young Plant:**")
        young = water_req.get('young_plant') or watering.get('young_plant', 'Alternate day watering')
        st.write(young)
    
    with col2:
        st.markdown("**🌳 Mature Plant:**")
        mature = water_req.get('mature_plant') or watering.get('mature_plant', 'Weekly watering')
        st.write(mature)
        
        st.markdown("**💡 Water Conservation:**")
        conv = water_req.get('water_conservation_methods') or watering.get('water_conservation_tips') or watering.get('water_conservation_methods') or 'Use mulching and efficient irrigation'
        st.write(conv)

    # Show sunlight requirements in care tab
    st.markdown("### 🌞 Sunlight Needs")
    sun_text = sun_req.get('daily_hours_needed') or sun_req.get('daily_hours') or watering.get('sunlight', '6-8 hours')
    st.write(f"Daily sunlight needed: {sun_text}")
    st.write(f"Light intensity: {sun_req.get('light_intensity', 'Full Sun')}")
    
    st.markdown("### 🔧 Maintenance Schedule")
    
    schedule_items = [
        ('Daily', maintenance.get('daily', 'Basic health monitoring')),
        ('Weekly', maintenance.get('weekly', 'Pest inspection and weeding')),
        ('Monthly', maintenance.get('monthly', 'Fertilization and pruning')),
        ('Seasonal', maintenance.get('seasonal', 'Major care activities')),
        ('Annual', maintenance.get('annual', 'Comprehensive health assessment'))
    ]
    
    for period, task in schedule_items:
        st.markdown(f"**{period}:** {task}")

def display_growth_economics_tab(plant):
    """Display growth characteristics and economic benefits"""
    growth = plant.get('growth_characteristics', {})
    economics = plant.get('economic_benefits', {})
    
    st.markdown("### 📈 Growth Characteristics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**🏗️ Mature Height:** {growth.get('mature_height', '5-10 meters')}")
        st.markdown(f"**🌿 Spread:** {growth.get('mature_spread', '4-8 meters')}")
        st.markdown(f"**⚡ Growth Rate:** {growth.get('growth_rate', 'Medium')}")
    
    with col2:
        st.markdown(f"**⏰ Lifespan:** {growth.get('lifespan', '20-50 years')}")
        st.markdown(f"**📏 Space Needed:** {growth.get('space_requirements', '3x3 meters')}")
    
    st.markdown("### 💰 Economic Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**💵 Initial Cost:** {economics.get('initial_cost', '₹200-500')}")
        st.markdown(f"**🔄 Annual Maintenance:** {economics.get('maintenance_cost_annual', '₹300-800')}")
    
    with col2:
        st.markdown(f"**💎 Property Value Impact:** {economics.get('property_value_impact', '5-15% increase')}")
        st.markdown(f"**💰 Economic Returns:** {economics.get('economic_returns', 'Environmental benefits')}")

def display_challenges_tab(plant):
    """Display challenges and solutions"""
    challenges = plant.get('challenges_and_solutions', {})
    
    st.markdown("**⚠️ Common Problems:**")
    st.write(challenges.get('common_problems', 'Typical plant health issues'))
    
    st.markdown("**🐛 Pest Management:**")
    st.write(challenges.get('pest_management', 'Natural pest control methods'))
    
    st.markdown("**🦠 Disease Prevention:**")
    st.write(challenges.get('disease_prevention', 'Preventive health measures'))
    
    st.markdown("**🌡️ Climate Adaptation:**")
    st.write(challenges.get('climate_adaptation', 'Weather resilience strategies'))
    
    st.markdown("**🔧 Quick Troubleshooting:**")
    st.write(challenges.get('troubleshooting', 'Common fixes for issues'))

def get_plant_type_emoji(plant_type):
    """
    Get emoji for different plant types
    """
    emojis = {
        'Tree': '🌳',
        'Shrub': '🌿',
        'Crop': '🌾',
        'Herb': '🌱',
        'Grass': '🌾',
        'Fruit': '🍎',
        'Flower': '🌸'
    }
    return emojis.get(plant_type, '🌱')

def display_data_quality_info(quality_info):
    """
    Display information about data quality
    """
    quality = quality_info.get('overall_quality', 'unknown')
    
    if quality == 'good':
        st.success("✅ Using real-time environmental data")
    elif quality == 'fair':
        st.warning("⚠️ Using partially estimated data")
        with st.expander("Data Quality Details"):
            for issue in quality_info.get('issues', []):
                st.write(f"• {issue}")
    else:
        st.info("ℹ️ Using default environmental data")
        with st.expander("Data Quality Details"):
            for issue in quality_info.get('issues', []):
                st.write(f"• {issue}")
            for rec in quality_info.get('recommendations', []):
                st.write(f"💡 {rec}")

def create_download_summary(recommendations, env_data):
    """
    Create a downloadable summary of recommendations
    """
    summary = "# Plant Recommendations Summary\n\n"
    summary += f"**Location:** {env_data.get('location', 'India')}\n"
    summary += f"**Date:** {st.session_state.get('generation_date', 'Today')}\n\n"
    
    summary += "## Environmental Conditions\n"
    summary += f"- Temperature: {env_data.get('temperature', 0):.1f}°C\n"
    summary += f"- Soil pH: {env_data.get('soil_ph', 6.5):.1f}\n"
    summary += f"- Rainfall: {env_data.get('rainfall', 0)} mm/year\n"
    
    # Handle new AQI format
    aqi_value = env_data.get('aqi', 75)
    aqi_rating = env_data.get('aqi_rating', 3)
    summary += f"- Air Quality: AQI {aqi_value} ({aqi_rating}/5 rating)\n\n"
    
    summary += "## Recommended Plants\n\n"
    for i, plant in enumerate(recommendations, 1):
        summary += f"### {i}. {plant.get('scientific_name', 'Unknown')}\n"
        summary += f"**Local Name:** {plant.get('local_name', 'N/A')}\n"
        summary += f"**Type:** {plant.get('plant_type', 'Plant')}\n"
        summary += f"**Suitability:** {plant.get('suitability', 'N/A')}\n"
        summary += f"**Benefits:** {plant.get('benefits', 'N/A')}\n"
        summary += f"**Care Tips:** {plant.get('care_tips', 'N/A')}\n\n"
    
    return summary