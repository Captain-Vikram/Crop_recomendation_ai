import streamlit as st

def apply_custom_styles():
    """
    Apply custom CSS styles to the Streamlit app
    """
    st.markdown("""
    <style>
    /* Main app styling */
    .main {
        padding-top: 1rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white !important;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f0f9f0;
    }
    
    /* Card styling for recommendations */
    .recommendation-card {
        background-color: #f0f9f0;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 10px 0;
    }
    
    /* Plant common name styling - Make it prominent */
    .plant-common-name {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #2E7D32 !important;
        margin: 8px 0 !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        padding: 8px 12px;
        background: linear-gradient(135deg, #E8F5E8, #F1F8E9);
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        display: inline-block;
        min-width: 200px;
        transform: scale(1.02);
        transition: all 0.3s ease;
    }
    
    .plant-common-name:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    
    .plant-local-name {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        color: #558B2F !important;
        font-style: italic;
        margin-top: 4px !important;
        padding: 4px 8px;
        background-color: rgba(139, 195, 74, 0.1);
        border-radius: 4px;
        display: inline-block;
    }
    
    .plant-scientific-name {
        font-size: 1.3rem !important;
        color: #1B5E20 !important;
        margin-bottom: 5px !important;
        font-weight: 600 !important;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
    }
    
    /* AI Selection Button Styling */
    .stButton[data-testid="baseButton-secondary"] > button {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #4CAF50;
        color: #2E7D32;
        padding: 20px;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        white-space: pre-line;
        height: auto;
        min-height: 80px;
        transition: all 0.3s ease;
    }
    
    .stButton[data-testid="baseButton-secondary"] > button:hover {
        background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
        border-color: #2E7D32;
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.2);
    }
    
    .stButton[data-testid="baseButton-secondary"] > button:active,
    .stButton[data-testid="baseButton-secondary"] > button:focus {
        background: linear-gradient(135deg, #c8e6c9 0%, #dcedc8 100%);
        border-color: #1B5E20;
        color: #1B5E20;
    }
    
    /* Success/Warning/Error message styling */
    .stSuccess {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    
    .stWarning {
        background-color: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(76, 175, 80, 0.1);
        border-radius: 5px;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #4CAF50;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 0.8rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* AI Model Selection Styling */
    .ai-model-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #4CAF50;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .ai-model-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(76, 175, 80, 0.2);
    }
    
    .ai-model-selected {
        background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
        border-color: #2E7D32;
    }
    
    /* Radio button styling for AI selection */
    div[data-testid="stRadio"] > label {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2E7D32;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4CAF50;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

def create_app_header():
    """
    Create the main application header with AI model indicator
    """
    # Get current AI choice from session state
    ai_choice = st.session_state.get('ai_model_choice', '🌐 Web AI (Gemini)')
    ai_indicator = "🏠 Local AI" if "Local AI" in ai_choice else "🌐 Web AI"
    
    # Check API key status
    api_key_status = ""
    if "Web AI" in ai_choice:
        gemini_key_exists = 'gemini_api_key' in st.session_state and st.session_state.gemini_api_key
        weather_key_exists = 'openweather_api_key' in st.session_state and st.session_state.openweather_api_key
        
        if gemini_key_exists and weather_key_exists:
            api_key_status = "✅ All API Keys Configured"
        elif gemini_key_exists and not weather_key_exists:
            api_key_status = "⚠️ Weather API Key Missing"
        elif not gemini_key_exists and weather_key_exists:
            api_key_status = "⚠️ Gemini API Key Missing"
        else:
            api_key_status = "❌ API Keys Required"
    else:
        api_key_status = "🔒 Private Mode"
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🌱 Crop Recommendation AI Bot</h1>
        <p>Get personalized crop recommendations for sustainable agriculture in India</p>
        <div style="margin-top: 15px; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div style="padding: 8px 16px; background: rgba(255,255,255,0.2); border-radius: 20px;">
                <strong>AI Model: {ai_indicator}</strong>
            </div>
            <div style="padding: 8px 16px; background: rgba(255,255,255,0.2); border-radius: 20px;">
                <strong>{api_key_status}</strong>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_loading_animation():
    """
    Create a loading animation while fetching data
    """
    return st.empty()

def show_loading_message(placeholder, message="Fetching environmental data..."):
    """
    Show loading message with spinner
    """
    with placeholder.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.spinner(message):
                st.write("🌍 Analyzing soil conditions...")
                st.write("🌤️ Getting weather data...")
                st.write("💨 Checking air quality...")
                st.write("🤖 Generating AI recommendations...")

def create_success_message(message):
    """
    Create styled success message
    """
    st.markdown(f"""
    <div style="
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    ">
        ✅ {message}
    </div>
    """, unsafe_allow_html=True)

def create_error_message(message):
    """
    Create styled error message
    """
    st.markdown(f"""
    <div style="
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    ">
        ❌ {message}
    </div>
    """, unsafe_allow_html=True)

def add_footer():
    """
    Add footer with credits and links
    """
    st.markdown("""
    <div style="
        margin-top: 3rem;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        text-align: center;
    ">
        <p style="color: #6c757d; margin-bottom: 0.5rem;">
            Made with ❤️ for sustainable India 🇮🇳
        </p>
        <p style="color: #6c757d; font-size: 0.9rem;">
            Powered by Google Gemini AI • OpenWeatherMap • SoilGrids
        </p>
    </div>
    """, unsafe_allow_html=True)