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
    Create the main application header
    """
    st.markdown("""
    <div class="main-header">
        <h1>🌱 Crop & Afforestation AI Bot</h1>
        <p>Get personalized plant recommendations for sustainable urban afforestation in India</p>
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