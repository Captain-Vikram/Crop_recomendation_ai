import streamlit as st
import re

def show_api_key_popup():
    """
    Show API key input popup at application launch
    Returns True if API keys are provided, False otherwise
    """
    # Check if both API keys are already stored in session state
    gemini_key_exists = 'gemini_api_key' in st.session_state and st.session_state.gemini_api_key
    weather_key_exists = 'openweather_api_key' in st.session_state and st.session_state.openweather_api_key
    
    if gemini_key_exists and weather_key_exists:
        return True
    
    # Check if user chose to skip API key (local AI mode)
    if 'skip_api_key' in st.session_state and st.session_state.skip_api_key:
        return True
    
    # Create the popup content with better styling
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
        padding: 40px;
        border-radius: 20px;
        border: 3px solid #4CAF50;
        box-shadow: 0 10px 30px rgba(76, 175, 80, 0.2);
        max-width: 800px;
        margin: 20px auto;
        text-align: center;
    ">
        <h1 style="color: #2E7D32; margin-bottom: 20px; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            🌱 Welcome to Crop & Afforestation AI Bot
        </h1>
        <p style="color: #555; font-size: 1.2rem; margin-bottom: 30px; line-height: 1.6;">
            🔑 To get personalized plant recommendations, please enter your API keys.<br>
            <small style="color: #777;">Your API keys are securely stored only for this session and never shared.</small>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered columns for the form
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # API key inputs with better styling
        st.markdown("### 🔑 Enter Your API Keys")
        
        # Gemini API Key Input
        st.markdown("#### 🤖 Gemini AI API Key")
        gemini_api_key = st.text_input(
            "",
            type="password",
            placeholder="Paste your Gemini API key here... (e.g., AIzaSyA...)",
            help="Get your free API key from Google AI Studio",
            key="gemini_api_key_input",
            label_visibility="collapsed",
            value=st.session_state.get('gemini_api_key', '')
        )
        
        # OpenWeatherMap API Key Input
        st.markdown("#### 🌤️ OpenWeatherMap API Key")
        weather_api_key = st.text_input(
            "",
            type="password",
            placeholder="Paste your OpenWeatherMap API key here... (e.g., a1b2c3d4...)",
            help="Get your free API key from OpenWeatherMap",
            key="weather_api_key_input",
            label_visibility="collapsed",
            value=st.session_state.get('openweather_api_key', '')
        )
        
        # Instructions for getting API keys
        with st.expander("🤔 How to get FREE API keys?", expanded=False):
            tab1, tab2 = st.tabs(["🤖 Gemini AI", "🌤️ OpenWeatherMap"])
            
            with tab1:
                st.markdown("""
                ### Step-by-step guide for Gemini API:
                
                1. **Visit Google AI Studio** 
                   👉 Go to [aistudio.google.com](https://aistudio.google.com/)
                
                2. **Sign in with Google**
                   🔐 Use your Gmail account to log in
                
                3. **Get API Key**
                   🔑 Click "Get API key" in the left sidebar
                   
                4. **Create New Key**
                   ➕ Click "Create API key in new project" or use existing project
                   
                5. **Copy & Paste**
                   📋 Copy the generated key and paste it above
                
                **✅ It's completely FREE with generous usage limits!**
                """)
            
            with tab2:
                st.markdown("""
                ### Step-by-step guide for OpenWeatherMap API:
                
                1. **Visit OpenWeatherMap** 
                   👉 Go to [openweathermap.org/api](https://openweathermap.org/api)
                
                2. **Sign Up/Login**
                   📝 Create a free account or log in
                
                3. **Get API Key**
                   🔑 Go to "API keys" section in your account
                   
                4. **Generate Key**
                   ➕ Create a new API key (may take a few minutes to activate)
                   
                5. **Copy & Paste**
                   📋 Copy the generated key and paste it above
                
                **✅ Free tier includes 1000 calls/day!**
                """)
            
            st.markdown("**🔒 Security:** Your API keys are only stored in your browser session and never shared.")
        
        st.markdown("---")
        
        # Action buttons
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 Continue with API Keys", use_container_width=True, type="primary"):
                # Validate Gemini API key
                gemini_valid = gemini_api_key and len(gemini_api_key.strip()) > 25
                # Validate OpenWeatherMap API key (typically 32 characters)
                weather_valid = weather_api_key and len(weather_api_key.strip()) > 20
                
                if gemini_valid and weather_valid:
                    st.session_state.gemini_api_key = gemini_api_key.strip()
                    st.session_state.openweather_api_key = weather_api_key.strip()
                    st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
                    st.success("✅ Both API keys saved successfully! Loading application...")
                    st.rerun()
                elif not gemini_valid and not weather_valid:
                    st.error("❌ Please enter both valid API keys")
                elif not gemini_valid:
                    st.error("❌ Please enter a valid Gemini API key")
                elif not weather_valid:
                    st.error("❌ Please enter a valid OpenWeatherMap API key")
        
        with col_b:
            if st.button("🏠 Try Local AI Instead", use_container_width=True):
                # Check if local AI is available
                try:
                    from api.local_api import check_lm_studio_connection
                    if check_lm_studio_connection():
                        st.session_state.ai_model_choice = "🏠 Local AI (LM Studio)"
                        st.session_state.skip_api_key = True
                        st.success("✅ Switched to Local AI mode! Loading application...")
                        st.rerun()
                    else:
                        st.error("❌ Local AI (LM Studio) is not running. Please start LM Studio with a loaded model first.")
                except Exception:
                    st.error("❌ Local AI is not configured. Please use API keys instead.")
        
        # Additional help section
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            <p>🌍 <strong>Why do I need API keys?</strong></p>
            <p>This app uses Google's Gemini AI to analyze your location's conditions and OpenWeatherMap 
            to get real-time weather, soil, and air quality data for accurate plant recommendations.</p>
            
            <p>🔒 <strong>Privacy:</strong> Your API keys stay in your browser and are never stored on our servers.</p>
        </div>
        """, unsafe_allow_html=True)
    
    return False

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
        
        # API Key Management
        gemini_key_exists = 'gemini_api_key' in st.session_state and st.session_state.gemini_api_key
        weather_key_exists = 'openweather_api_key' in st.session_state and st.session_state.openweather_api_key
        
        if gemini_key_exists and weather_key_exists:
            st.sidebar.success("🔑 API Keys: Both Configured")
            if st.sidebar.button("🔄 Change API Keys"):
                if 'gemini_api_key' in st.session_state:
                    del st.session_state.gemini_api_key
                if 'openweather_api_key' in st.session_state:
                    del st.session_state.openweather_api_key
                st.rerun()
        elif gemini_key_exists and not weather_key_exists:
            st.sidebar.warning("⚠️ Gemini: ✅ | Weather: ❌")
            if st.sidebar.button("🔑 Configure Weather API"):
                st.rerun()
        elif not gemini_key_exists and weather_key_exists:
            st.sidebar.warning("⚠️ Gemini: ❌ | Weather: ✅")
            if st.sidebar.button("🔑 Configure Gemini API"):
                st.rerun()
        else:
            st.sidebar.error("❌ API Keys Required")
            if st.sidebar.button("🔑 Configure API Keys"):
                if 'skip_api_key' in st.session_state:
                    del st.session_state.skip_api_key
                st.rerun()
    
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
            preference_items.append(f"🏔️ Soil: {user_preferences['soil_type']}")
        if user_preferences.get('water_availability'):
            preference_items.append(f"💧 Water: {user_preferences['water_availability']}")
        if user_preferences.get('space_constraint'):
            preference_items.append(f"📐 Space: {user_preferences['space_constraint']}")
        
        if preference_items:
            st.info(f"🎯 **Your Preferences:** {' | '.join(preference_items)}")
    
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
            rainfall_help += f" (adjusted for {user_preferences['water_availability']} water preference)"
        
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
            soil_help += f" (considering your {user_preferences['soil_type']} soil)"
        
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
            st.info("📐 **Space Optimized:** Recommendations tailored for terrace/balcony gardens")
        elif space_constraint == 'Medium (Small Garden)':
            st.info("📐 **Space Optimized:** Recommendations for small garden spaces")
        elif space_constraint == 'Large (Farmland/Estate)':
            st.info("📐 **Space Optimized:** Recommendations for large-scale plantation")

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
        st.write(f"Best months: {pw.get('best_months', 'Not specified')}")
        st.write(f"Can plant now: {'✅ Yes' if pw.get('can_plant_now') else '❌ No'}")
    
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
        st.write(water_req.get('seedling_stage', watering.get('seedling', '2-3 liters/week')))
        
        st.markdown("**🌿 Young Plant:**")
        st.write(water_req.get('young_plant', watering.get('young', '5-10 liters/week')))
    
    with col2:
        st.markdown("**🌳 Mature Plant:**")
        st.write(water_req.get('mature_plant', watering.get('mature', '15-25 liters/week')))
        
        st.markdown("**🏜️ Dry Season Adjustment:**")
        st.write(water_req.get('dry_season_adjustment', watering.get('dry_season', '+30% more water')))

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
        st.markdown("**📏 Mature Height:**")
        st.write(growth.get('mature_height', '5-10 meters'))
        
        st.markdown("**🚀 Growth Rate:**")
        st.write(growth.get('growth_rate', 'Medium'))
    
    with col2:
        st.markdown("**📐 Space Requirements:**")
        st.write(growth.get('space_requirements', '2-3 meters spacing'))
        
        st.markdown("**⏳ Lifespan:**")
        st.write(growth.get('lifespan', '20-50 years'))
    
    st.markdown("### 💰 Economic Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💸 Initial Cost:**")
        st.write(economics.get('initial_cost', '₹100-500 per plant'))
        
        st.markdown("**🔄 Annual Maintenance:**")
        st.write(economics.get('maintenance_cost_annual', '₹50-200 per year'))
    
    with col2:
        st.markdown("**💹 Economic Returns:**")
        st.write(economics.get('economic_returns', 'Varies by plant type'))
        
        st.markdown("**🏠 Property Value Impact:**")
        st.write(economics.get('property_value_impact', '2-5% increase'))

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
        st.success("✅ **Data Quality:** Excellent - All environmental data successfully retrieved")
    elif quality == 'fair':
        st.warning("⚠️ **Data Quality:** Fair - Some data estimated, recommendations may be less precise")
    else:
        st.info("ℹ️ **Data Quality:** Using default estimates - Consider providing more specific location details")

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
        summary += f"### {i}. {plant.get('common_name', 'Unknown Plant')}\n"
        summary += f"**Scientific Name:** {plant.get('scientific_name', 'N/A')}\n"
        summary += f"**Local Name:** {plant.get('local_name', 'N/A')}\n"
        summary += f"**Type:** {plant.get('plant_type', 'Plant')}\n"
        summary += f"**Suitability:** {plant.get('suitability_score', 'N/A')}\n"
        summary += f"**Analysis:** {plant.get('suitability_analysis', 'N/A')}\n\n"
    
    return summary
