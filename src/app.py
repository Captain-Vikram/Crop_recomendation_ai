import streamlit as st
import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from api.soil_api import get_soil_data
from api.weather_api import get_weather_data
from api.air_quality_api import get_air_quality_data
from api.gemini_api import get_recommendations as get_gemini_recommendations
from api.local_api import get_recommendations as get_local_recommendations, check_lm_studio_connection
from utils.location_handler import get_lat_lon, validate_pin_code, get_location_name
from utils.data_processor import format_data_for_ai, validate_environmental_data, get_data_quality_summary, create_environmental_summary
from components.ui_components import create_minimal_sidebar, display_environmental_summary, display_recommendations, display_data_quality_info
from components.styling import apply_custom_styles, create_app_header, create_loading_animation, show_loading_message, add_footer
from components.map_interface import create_map_interface, get_location_from_map, create_location_summary
from components.report_generator import create_comprehensive_report_download

def main():
    """
    Main application function
    """
    # Configure page
    st.set_page_config(
        page_title="Crop & Afforestation AI Bot",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom styling
    apply_custom_styles()
    
    # Initialize session state FIRST
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None
    if 'env_data' not in st.session_state:
        st.session_state.env_data = None
    if 'ai_model_choice' not in st.session_state:
        st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
    
    # Create header (after session state is initialized)
    create_app_header()
    
    # Create minimal sidebar
    create_minimal_sidebar()
    
    # Prominent AI Model Selection Banner
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
    ">
        <h3 style="margin: 0; color: white;">🤖 Choose Your AI Model</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if LM Studio is available
    try:
        lm_studio_available = check_lm_studio_connection()
    except Exception as e:
        lm_studio_available = False
    
    # Create AI selection columns
    if lm_studio_available:
        ai_col1, ai_col2 = st.columns(2)
        
        with ai_col1:
            web_ai_selected = st.button(
                "🌐 Web AI (Gemini)\n\nOnline • Comprehensive • Cloud-based",
                key="web_ai_btn",
                use_container_width=True,
                help="Uses Google Gemini AI via internet connection"
            )
            if web_ai_selected:
                st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
                st.rerun()
        
        with ai_col2:
            local_ai_selected = st.button(
                "🏠 Local AI (LM Studio)\n\nPrivate • Offline • Local processing",
                key="local_ai_btn", 
                use_container_width=True,
                help="Uses your local LM Studio model for complete privacy"
            )
            if local_ai_selected:
                st.session_state.ai_model_choice = "🏠 Local AI (LM Studio)"
                st.rerun()
    else:
        st.button(
            "🌐 Web AI (Gemini)\n\nOnline • Comprehensive • Cloud-based",
            key="web_ai_only_btn",
            use_container_width=True,
            disabled=False,
            help="Uses Google Gemini AI via internet connection"
        )
        st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
        
        # Show local AI setup info
        st.info("🏠 **Local AI not available.** To enable local AI, install and run LM Studio with a loaded model.")
    
    # Display current selection
    current_ai = st.session_state.get('ai_model_choice', '🌐 Web AI (Gemini)')
    
    if "Local AI" in current_ai:
        if lm_studio_available:
            st.success(f"✅ **Currently using:** {current_ai}")
            # Show model info
            try:
                from api.local_api import get_available_models
                models = get_available_models()
                if models:
                    st.info(f"📦 **Active model:** {models[0]}")
            except Exception:
                pass
        else:
            st.error("❌ Local AI selected but LM Studio not available. Falling back to Web AI.")
            st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
    else:
        st.success(f"✅ **Currently using:** {current_ai}")
    
    st.markdown("---")
    
    # Main content area
    # Create location selection interface
    st.markdown("## 🌍 Location Selection & Plant Recommendations")
    
    # Location input method selection
    input_method = st.radio(
        "Choose your preferred location input method:",
        ["🗺️ Interactive Map", "📝 Manual Input (PIN/City)"],
        horizontal=True
    )
    
    # Initialize location variables
    lat, lon = None, None
    location_from_map = False
    
    if input_method == "🗺️ Interactive Map":
        # Show map interface
        map_coords = create_map_interface()
        if map_coords:
            lat, lon = map_coords
            location_from_map = True
            create_location_summary()
        
    else:
        # Show traditional input
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### 📝 Manual Location Input")
            
            # Location input method
            location_method = st.selectbox(
                "How would you like to specify location?",
                ["PIN Code", "City Name"],
                help="Choose your preferred method to specify location"
            )
            
            location_input = None
            
            if location_method == "PIN Code":
                location_input = st.text_input(
                    "Enter 6-digit PIN Code",
                    placeholder="e.g., 400001",
                    help="Enter Indian postal PIN code"
                )
            elif location_method == "City Name":
                location_input = st.text_input(
                    "Enter City Name",
                    placeholder="e.g., Mumbai",
                    help="Enter city name in India"
                )
            
            if location_input:
                # Validate location input
                if location_method == "PIN Code" and not validate_pin_code(location_input):
                    st.error("Please enter a valid 6-digit Indian PIN code (e.g., 400001)")
                else:
                    # Get coordinates from location input
                    lat, lon = get_lat_lon(
                        location_input, 
                        method=location_method.lower().replace(" ", "_")
                    )
                    if lat and lon:
                        st.success(f"📍 Location found: {lat:.4f}, {lon:.4f}")
            else:
                st.info("👈 Please enter your location in the sidebar to get started!")
        
        with col2:
            display_info_panel()
    
    # Show recommendation generation if we have valid coordinates
    if lat and lon:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # User goal selection with buttons
            st.markdown("### 🎯 What's your goal?")
            st.markdown("Choose your primary objective for plantation:")
            
            # Create goal selection buttons
            goal_col1, goal_col2, goal_col3 = st.columns(3)
            
            with goal_col1:
                cash_crops = st.button(
                    "💰 Cash Crops",
                    help="High-value crops for commercial farming and income generation",
                    use_container_width=True
                )
            
            with goal_col2:
                food_crops = st.button(
                    "� Food Crops", 
                    help="Nutritious crops for food security and kitchen gardens",
                    use_container_width=True
                )
            
            with goal_col3:
                afforestation = st.button(
                    "🌳 Afforestation",
                    help="Trees for air purification, shade, and environmental benefits",
                    use_container_width=True
                )
            
            # Determine selected goal
            goal_type = None
            
            if cash_crops:
                goal_type = "cash_crops"
                st.session_state.selected_goal = "💰 Cash Crops"
            elif food_crops:
                goal_type = "food_crops" 
                st.session_state.selected_goal = "🌾 Food Crops"
            elif afforestation:
                goal_type = "afforestation"
                st.session_state.selected_goal = "🌳 Afforestation"
            
            # Show selected goal
            if hasattr(st.session_state, 'selected_goal'):
                st.success(f"Selected: {st.session_state.selected_goal}")
                # Use the stored goal if no new selection
                if not goal_type:
                    if st.session_state.selected_goal == "💰 Cash Crops":
                        goal_type = "cash_crops"
                    elif st.session_state.selected_goal == "🌾 Food Crops":
                        goal_type = "food_crops"
                    elif st.session_state.selected_goal == "🌳 Afforestation":
                        goal_type = "afforestation"
            
            prefer_native = st.checkbox(
                "🌿 Prefer native Indian species",
                value=True,
                help="Prioritize plants native to India"
            )
            
            # Optional user inputs section
            st.markdown("---")
            st.markdown("### 📋 Optional Details (for better recommendations)")
            st.markdown("*These details help us provide more accurate plant suggestions*")
            
            # Create expandable section for optional inputs
            with st.expander("🔧 Customize Your Recommendations", expanded=False):
                opt_col1, opt_col2 = st.columns(2)
                
                with opt_col1:
                    # Water availability input
                    water_availability = st.selectbox(
                        "💧 Water Availability",
                        options=["Auto-detect", "Low", "Medium", "High"],
                        index=0,
                        help="Select your water supply/availability for irrigation"
                    )
                    
                    # Soil type input
                    soil_type_input = st.text_input(
                        "🏔️ Soil Type (Optional)",
                        placeholder="e.g., red soil, black soil, sandy loam, clay...",
                        help="Describe your soil type if known"
                    )
                
                with opt_col2:
                    # Space availability input with location type
                    st.markdown("**📐 Available Space & Location**")
                    
                    # Numeric area input
                    space_availability = st.number_input(
                        "Area (square meters)",
                        min_value=0.0,
                        max_value=10000.0,
                        value=0.0,
                        step=1.0,
                        help="Enter available planting area in square meters (0 = auto-estimate)"
                    )
                    
                    # Alternative area input with units
                    area_with_units = st.text_input(
                        "🔄 Or specify area with units",
                        placeholder="e.g., 2 acres, 0.5 hectare, 100 sq ft, 1 bigha...",
                        help="Enter area with units - will be converted to square meters automatically"
                    )
                    
                    # Location type/constraint input
                    space_location_type = st.text_input(
                        "🏠 Where will you plant?",
                        placeholder="e.g., window pane, balcony, backyard, terrace, garden, farmland...",
                        help="Describe your planting location (indoor/outdoor space type)"
                    )
                    
                    # Show space type suggestions if location type is provided
                    if space_location_type.strip():
                        from utils.data_processor import get_space_type_suggestions
                        suggestions = get_space_type_suggestions(space_location_type)
                        if suggestions:
                            st.caption(f"💡 Suggested for {space_location_type}: {', '.join(suggestions['plant_types'])}")
                    
                    # Budget preference input
                    budget_preference = st.selectbox(
                        "💰 Budget Preference",
                        options=["Auto-suggest", "Low cost", "Medium cost", "Premium options"],
                        index=0,
                        help="Select your preferred budget range for plantation"
                    )
                
                # Store user preferences in session state
                if 'user_preferences' not in st.session_state:
                    st.session_state.user_preferences = {}
                
                st.session_state.user_preferences.update({
                    'water_availability': water_availability,
                    'soil_type_input': soil_type_input,
                    'space_availability': space_availability,
                    'area_with_units': area_with_units,
                    'space_location_type': space_location_type,
                    'budget_preference': budget_preference
                })
                
                # Show summary of custom inputs
                if any([
                    water_availability != "Auto-detect",
                    soil_type_input.strip(),
                    space_availability > 0,
                    area_with_units.strip(),
                    space_location_type.strip(),
                    budget_preference != "Auto-suggest"
                ]):
                    st.info("✅ Custom preferences will be prioritized in recommendations!")
                    
                    # Show detailed preference summary
                    prefs_summary = []
                    if water_availability != "Auto-detect":
                        prefs_summary.append(f"💧 Water: {water_availability}")
                    if soil_type_input.strip():
                        prefs_summary.append(f"🏔️ Soil: {soil_type_input}")
                    if space_availability > 0:
                        prefs_summary.append(f"📐 Area: {space_availability} m²")
                    elif area_with_units.strip():
                        prefs_summary.append(f"📐 Area: {area_with_units}")
                    if space_location_type.strip():
                        prefs_summary.append(f"🏠 Location: {space_location_type}")
                    if budget_preference != "Auto-suggest":
                        prefs_summary.append(f"💰 Budget: {budget_preference}")
                    
                    st.caption(f"Custom settings: {' | '.join(prefs_summary)}")
        
        with col2:
            st.markdown("") # Spacer
            st.markdown("") # Spacer
            if st.button("🚀 Get Plant Recommendations", type="primary", use_container_width=True):
                if goal_type:
                    generate_recommendations_from_coords(lat, lon, goal_type, prefer_native)
                else:
                    st.warning("Please select your goal first!")
        
        # Display cached recommendations if available
        if st.session_state.get('recommendations') and st.session_state.get('env_data'):
            display_results()
            
            # Add comprehensive report download
            # st.markdown("---")
            create_comprehensive_report_download(st.session_state.recommendations, st.session_state.env_data)
    
    else:
        # Show sample recommendations when no location is selected
        if input_method == "📝 Manual Input (PIN/City)":
            pass  # Already handled above
        else:
            st.info("🗺️ Please select a location on the map above to get personalized plant recommendations!")
            display_sample_recommendations()
    
    # Add footer
    add_footer()

def generate_recommendations_from_coords(lat, lon, goal_type, prefer_native):
    """
    Generate plant recommendations based on coordinates and goal type with user preferences
    """
    # Create loading animation
    loading_placeholder = create_loading_animation()
    
    try:
        show_loading_message(loading_placeholder, "Fetching environmental data...")
        
        # Get location name for display
        location_name = get_location_name(lat, lon)
        
        # Fetch environmental data
        with st.spinner("Analyzing environmental conditions..."):
            soil_data = get_soil_data(lat, lon)
            weather_data = get_weather_data(lat, lon)
            air_quality_data = get_air_quality_data(lat, lon)
        
        # Get user preferences if available
        user_preferences = getattr(st.session_state, 'user_preferences', {})
        
        # Format data for AI processing with user preferences
        formatted_data = format_data_for_ai(
            soil_data, 
            weather_data, 
            air_quality_data,
            prefer_native,
            user_preferences  # Pass user preferences to the enhanced function
        )
        
        # Add goal type to formatted data
        formatted_data['goal_type'] = goal_type
        
        # Validate and clean data
        formatted_data = validate_environmental_data(formatted_data)
        
        # Update location name
        formatted_data['location'] = location_name or f"Location ({lat:.4f}, {lon:.4f})"
        
        # Get AI recommendations with goal type and user preferences
        ai_choice = st.session_state.get('ai_model_choice', '🌐 Web AI (Gemini)')
        
        with st.spinner(f"Generating AI-powered recommendations using {ai_choice}..."):
            if "Local AI" in ai_choice:
                recommendations = get_local_recommendations(
                    formatted_data,
                    prefer_native,
                    goal_type=goal_type,
                    lat=lat,
                    lon=lon
                )
            else:
                recommendations = get_gemini_recommendations(
                    formatted_data,
                    prefer_native,
                    goal_type=goal_type,
                    lat=lat,
                    lon=lon
                )
        
        loading_placeholder.empty()
        
        # Store results in session state
        st.session_state.recommendations = recommendations
        st.session_state.env_data = formatted_data
        st.session_state.generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Display success message with goal-specific text
        goal_text = {
            'cash_crops': 'high-value cash crops',
            'food_crops': 'nutritious food crops', 
            'afforestation': 'environmental trees'
        }
        
        ai_model_name = "🏠 Local AI" if "Local AI" in ai_choice else "🌐 Web AI"
        success_message = f"✅ Generated {len(recommendations)} {goal_text.get(goal_type, 'plant')} recommendations for {formatted_data['location']} using {ai_model_name}"
        
        # Add note about user preferences if they were used
        if user_preferences and any([
            user_preferences.get('water_availability', 'Auto-detect') != 'Auto-detect',
            user_preferences.get('soil_type_input', '').strip(),
            user_preferences.get('space_availability', 0) > 0,
            user_preferences.get('area_with_units', '').strip(),
            user_preferences.get('space_location_type', '').strip(),
            user_preferences.get('budget_preference', 'Auto-suggest') != 'Auto-suggest'
        ]):
            success_message += " ⚙️ (customized with your preferences)"
        
        st.success(success_message)
        
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"An error occurred: {str(e)}")
        st.error("Please try again or check your internet connection.")

def display_results():
    """
    Display the generated recommendations and environmental data
    """
    env_data = st.session_state.env_data
    recommendations = st.session_state.recommendations
    user_preferences = st.session_state.get('user_preferences', {})
    
    # Display environmental summary with user preferences
    display_environmental_summary(env_data, user_preferences)
    
    # Display data quality information
    quality_info = get_data_quality_summary(env_data)
    display_data_quality_info(quality_info)
    
    # Display recommendations
    display_recommendations(recommendations)

def display_sample_recommendations():
    """
    Display sample recommendations to show app capabilities for different goal types
    """
    st.markdown("### 🌟 Sample Recommendations by Goal Type")
    st.markdown("*Here's what you can expect for different goals:*")
    
    # Create tabs for different goal types
    sample_tab1, sample_tab2, sample_tab3 = st.tabs(["💰 Cash Crops", "🌾 Food Crops", "🌳 Afforestation"])
    
    with sample_tab1:
        st.markdown("#### High-Value Commercial Crops")
        cash_crops_samples = [
            {
                'scientific_name': 'Curcuma longa',
                'local_name': 'Turmeric (हल्दी)',
                'suitability': 'High-value spice crop with excellent market demand and export potential.',
                'benefits': 'Premium pricing, medicinal properties, easy storage, multiple harvests.',
                'care_tips': 'Plant during monsoon, harvest after 7-10 months, requires well-drained soil.',
                'plant_type': 'Cash Crop'
            },
            {
                'scientific_name': 'Mentha spicata',
                'local_name': 'Mint (पुदीना)',
                'suitability': 'Fast-growing aromatic crop with continuous harvest potential.',
                'benefits': 'Essential oil extraction, culinary use, pharmaceutical demand.',
                'care_tips': 'Requires consistent moisture, shade tolerance, propagates easily.',
                'plant_type': 'Cash Crop'
            }
        ]
        
        for i, plant in enumerate(cash_crops_samples, 1):
            with st.expander(f"💰 {i}. {plant['local_name']} - *{plant['scientific_name']}*"):
                st.write(f"**Suitability:** {plant['suitability']}")
                st.write(f"**Economic Benefits:** {plant['benefits']}")
                st.write(f"**Care Tips:** {plant['care_tips']}")
    
    with sample_tab2:
        st.markdown("#### Nutritious Food Security Crops")
        food_crops_samples = [
            {
                'scientific_name': 'Solanum lycopersicum',
                'local_name': 'Tomato (टमाटर)',
                'suitability': 'High-yield vegetable perfect for kitchen gardens and food security.',
                'benefits': 'Rich in vitamins, multiple harvests, essential cooking ingredient.',
                'care_tips': 'Regular watering, support structures needed, harvest in 60-80 days.',
                'plant_type': 'Food Crop'
            },
            {
                'scientific_name': 'Vigna radiata',
                'local_name': 'Mung Bean (मूंग)',
                'suitability': 'Protein-rich legume that improves soil fertility.',
                'benefits': 'High protein content, nitrogen fixation, drought tolerance.',
                'care_tips': 'Minimal water needs, harvest in 60-65 days, suitable for inter-cropping.',
                'plant_type': 'Food Crop'
            }
        ]
        
        for i, plant in enumerate(food_crops_samples, 1):
            with st.expander(f"🌾 {i}. {plant['local_name']} - *{plant['scientific_name']}*"):
                st.write(f"**Suitability:** {plant['suitability']}")
                st.write(f"**Nutritional Benefits:** {plant['benefits']}")
                st.write(f"**Care Tips:** {plant['care_tips']}")
    
    with sample_tab3:
        st.markdown("#### Environmental Trees")
        afforestation_samples = [
            {
                'scientific_name': 'Azadirachta indica',
                'local_name': 'Neem (नीम)',
                'suitability': 'Hardy tree perfect for urban environments with excellent pollution tolerance.',
                'benefits': 'Natural air purifier, medicinal properties, and effective pest control.',
                'care_tips': 'Water regularly in the first year, then minimal care needed. Prune annually.',
                'plant_type': 'Tree'
            },
            {
                'scientific_name': 'Moringa oleifera',
                'local_name': 'Drumstick (सहजन)',
                'suitability': 'Fast-growing tree that thrives in poor soil conditions.',
                'benefits': 'Highly nutritious leaves and pods, medicinal uses, soil improvement.',
                'care_tips': 'Minimal watering once established. Harvest regularly for best growth.',
                'plant_type': 'Tree'
            }
        ]
        
        for i, plant in enumerate(afforestation_samples, 1):
            with st.expander(f"🌳 {i}. {plant['local_name']} - *{plant['scientific_name']}*"):
                st.write(f"**Suitability:** {plant['suitability']}")
                st.write(f"**Environmental Benefits:** {plant['benefits']}")
                st.write(f"**Care Tips:** {plant['care_tips']}")

def display_info_panel():
    """
    Display information panel with tips and features
    """
    st.markdown("### ℹ️ How It Works")
    
    with st.expander("🔍 Data Sources"):
        st.write("""
        **Soil Data:** ISRIC SoilGrids (pH, texture, organic carbon)
        
        **Weather:** OpenWeatherMap (temperature, humidity, rainfall)
        
        **Air Quality:** OpenWeatherMap Air Pollution API
        
        **AI Engine:** Google Gemini Pro for intelligent recommendations
        """)
    
    with st.expander("🌱 Features"):
        st.write("""
        ✅ Real-time environmental data analysis
        
        ✅ Native Indian species prioritization
        
        ✅ Pollution-tolerant plant suggestions
        
        ✅ Personalized care instructions
        
        ✅ Multiple location input methods
        
        ✅ Downloadable recommendations
        """)
    
    with st.expander("💡 Tips"):
        st.write("""
        🎯 **Be Specific:** Describe your goals clearly (e.g., "pollution control near roadside")
        
        📍 **Accurate Location:** Use precise PIN codes for better soil data
        
        🌿 **Native First:** Enable native species preference for better ecosystem support
        
        📱 **Mobile Friendly:** Works great on phones and tablets
        """)
    
    # Show environmental conditions legend
    st.markdown("### 🌡️ Environmental Indicators")
    st.write("""
    **Soil pH:** 
    - 4-5.5: Acidic
    - 5.5-6.5: Slightly acidic  
    - 6.5-7.5: Neutral
    - 7.5-8.5: Slightly alkaline
    - 8.5+: Alkaline
    
    **Air Quality Index:**
    - 1: Good
    - 2: Fair
    - 3: Moderate
    - 4: Poor
    - 5: Very Poor
    """)

if __name__ == "__main__":
    main()