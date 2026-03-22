"""
Enhanced Local AI Model Manager Component
Handles model detection, information display, and selection UI
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
import requests


class LocalAIManager:
    """Unified manager for Local AI model operations and UI"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1234"):
        self.base_url = base_url
        self.connection_cache = None
        self.cache_timeout = 0
    
    def check_connection(self, force_refresh: bool = False) -> bool:
        """Check if LM Studio is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"LM Studio connection error: {e}")
            return False
    
    def get_all_models(self) -> List[str]:
        """Get list of available models from LM Studio"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['id'] for model in models_data.get('data', [])]
            return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def get_model_details(self, model_id: str) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        try:
            response = requests.get(f"{self.base_url}/v1/models/{model_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching model details: {e}")
            return None
    
    def get_active_model(self) -> Optional[str]:
        """Get the currently active/loaded model"""
        models = self.get_all_models()
        return models[0] if models else None
    
    def get_model_info_display(self, model_id: str) -> Dict[str, Any]:
        """Get display-friendly model information"""
        try:
            details = self.get_model_details(model_id)
            if not details:
                return self._get_default_model_info(model_id)
            
            # Extract useful info for display
            info = {
                'id': model_id,
                'name': model_id.replace('_', ' ').replace('-', ' ').title(),
                'full_name': model_id,
                'size': 'Unknown',
                'type': self._infer_model_type(model_id),
                'is_specialized': self._is_specialized_model(model_id),
                'description': self._get_model_description(model_id),
                'capabilities': self._get_model_capabilities(model_id),
                'parameters': self._extract_parameters(model_id)
            }
            
            return info
        except Exception as e:
            print(f"Error getting model display info: {e}")
            return self._get_default_model_info(model_id)
    
    def _infer_model_type(self, model_id: str) -> str:
        """Infer model type from model ID"""
        model_lower = model_id.lower()
        
        if 'crop' in model_lower or 'agri' in model_lower or 'plant' in model_lower:
            return "🌾 Agricultural Specialist"
        elif 'llama' in model_lower:
            return "🦙 LLaMA Model"
        elif 'mistral' in model_lower:
            return "⚡ Mistral Model"
        elif 'neural' in model_lower or 'neural' in model_lower:
            return "🧠 Neural Model"
        elif 'phi' in model_lower:
            return "🔬 Phi Model"
        else:
            return "🤖 Language Model"
    
    def _is_specialized_model(self, model_id: str) -> bool:
        """Check if model is specialized for agriculture/crops"""
        keywords = ['crop', 'agri', 'plant', 'farm', 'soil', 'recommend']
        return any(kw in model_id.lower() for kw in keywords)
    
    def _get_model_description(self, model_id: str) -> str:
        """Get a user-friendly description of the model"""
        if self._is_specialized_model(model_id):
            return "✅ Specialized for crop and plant recommendations"
        else:
            return "General-purpose language model"
    
    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """Get model capabilities"""
        capabilities = [
            "Plant recommendations",
            "Agricultural advice",
            "Soil analysis guidance"
        ]
        
        if self._is_specialized_model(model_id):
            capabilities.extend([
                "Crop selection optimization",
                "Region-specific insights"
            ])
        
        return capabilities
    
    def _extract_parameters(self, model_id: str) -> Dict[str, str]:
        """Extract model parameters from ID"""
        params = {}
        model_lower = model_id.lower()
        
        # Extract size if mentioned
        if '3b' in model_lower:
            params['size'] = "3B Parameters"
        elif '7b' in model_lower:
            params['size'] = "7B Parameters"
        elif '13b' in model_lower:
            params['size'] = "13B Parameters"
        elif '70b' in model_lower:
            params['size'] = "70B Parameters"
        else:
            params['size'] = "Unknown Size"
        
        params['type'] = model_id.split('-')[0].title()
        
        return params
    
    def _get_default_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get default model info when details can't be fetched"""
        return {
            'id': model_id,
            'name': model_id.replace('_', ' ').replace('-', ' ').title(),
            'full_name': model_id,
            'type': self._infer_model_type(model_id),
            'is_specialized': self._is_specialized_model(model_id),
            'description': self._get_model_description(model_id),
            'capabilities': self._get_model_capabilities(model_id),
            'parameters': self._extract_parameters(model_id)
        }


def create_local_ai_selector() -> Tuple[str, bool]:
    """
    Create a comprehensive Local AI selection and info display component
    Returns: (selected_ai_model, lm_studio_available)
    """
    manager = LocalAIManager()
    lm_studio_available = manager.check_connection()
    
    # Store connection status in session
    st.session_state.lm_studio_available = lm_studio_available
    
    # Main AI selection header
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
    
    # Check LM Studio connection status
    if lm_studio_available:
        # Get available models
        available_models = manager.get_all_models()
        active_model = manager.get_active_model()
        
        # Create columns for AI selection
        col1, col2 = st.columns(2)
        
        with col1:
            web_ai_selected = st.button(
                "🌐 Web AI (Gemini)\n\nOnline • Comprehensive • Cloud-based",
                key="web_ai_selector_btn",
                width='stretch',
                help="Uses Google Gemini AI via internet connection"
            )
            if web_ai_selected:
                st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
                st.rerun()
        
        with col2:
            local_ai_selected = st.button(
                "🏠 Local AI (LM Studio)\n\nPrivate • Offline • Local processing",
                key="local_ai_selector_btn",
                width='stretch',
                help="Uses your local LM Studio model for complete privacy"
            )
            if local_ai_selected:
                st.session_state.ai_model_choice = "🏠 Local AI (LM Studio)"
                st.rerun()
        
        # Display current selection and model info
        st.markdown("---")
        current_ai = st.session_state.get('ai_model_choice', '🌐 Web AI (Gemini)')
        
        if "Local AI" in current_ai:
            st.success(f"✅ **Using:** {current_ai}")
            
            if available_models:
                st.info(f"📦 **Models Available:** {len(available_models)}")
                
                # Show model selector and details
                with st.expander("📋 View & Select Model", expanded=True):
                    selected_model_idx = 0
                    if active_model:
                        try:
                            selected_model_idx = available_models.index(active_model)
                        except ValueError:
                            pass
                    
                    selected_model = st.selectbox(
                        "Choose a model to use:",
                        available_models,
                        index=selected_model_idx,
                        key="model_selector",
                        help="Select which loaded model to use for recommendations"
                    )
                    
                    # Display model details
                    if selected_model:
                        model_info = manager.get_model_info_display(selected_model)
                        
                        # Model info display
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.markdown(f"**Model Type:** {model_info['type']}")
                            st.markdown(f"**Size:** {model_info['parameters'].get('size', 'Unknown')}")
                        
                        with col_info2:
                            if model_info['is_specialized']:
                                st.success(f"✅ {model_info['description']}")
                            else:
                                st.info(f"ℹ️ {model_info['description']}")
                        
                        # Display capabilities
                        st.markdown("**Capabilities:**")
                        for cap in model_info['capabilities']:
                            st.markdown(f"• {cap}")
                        
                        # Store selected model in session
                        st.session_state.selected_local_model = selected_model
                        
                        # Specialization indicator
                        if model_info['is_specialized']:
                            st.success("🎯 This model is specialized for agricultural recommendations!")
            else:
                st.warning("⚠️ No models are currently loaded in LM Studio")
                st.info("""
                **To load a model:**
                1. Open LM Studio
                2. Click 'Download' and search for llama-3.2-3b
                3. Once downloaded, select it and click 'Load'
                4. Make sure the server is running on http://127.0.0.1:1234
                """)
        else:
            st.success(f"✅ **Using:** {current_ai}")
            
            # Add Gemini model version selector
            st.markdown("**Select Gemini Model Version:**")
            
            gemini_models = {
                "🚀 Gemini 2.5 Flash": "gemini-2.5-flash",
                "💎 Gemini 2.5 Pro": "gemini-2.5-pro",
                "⚡ Gemini 2.0 Flash": "gemini-2.0-flash",
                "🚄 Gemini 2.0 Flash Lite": "gemini-2.0-flash-lite",
                "🔮 Gemini 3.1 Pro (Preview)": "gemini-3.1-pro-preview",
            }
            
            selected_model_display = st.selectbox(
                "Choose a Gemini model version:",
                options=list(gemini_models.keys()),
                index=0,  # Default to Gemini 2.0 Flash
                key="gemini_model_selector",
                help="Different Gemini versions offer different speeds, cost, and capabilities"
            )
            
            # Store selected model version
            selected_model_key = gemini_models[selected_model_display]
            st.session_state.gemini_model_version = selected_model_key
            
            # Display model info
            model_info = {
                "gemini-2.5-flash": {
                    "description": "Latest fast model - excellent balance of speed and quality",
                    "speed": "⚡ Very Fast",
                    "cost": "💰 Low",
                    "quality": "🎯 High quality"
                },
                "gemini-2.5-pro": {
                    "description": "Most capable model for complex reasoning tasks",
                    "speed": "⚡ Fast",
                    "cost": "💸 Higher",
                    "quality": "🏆 Excellent quality"
                },
                "gemini-2.0-flash": {
                    "description": "Previous generation fast model",
                    "speed": "⚡ Very Fast",
                    "cost": "💰 Low",
                    "quality": "🎯 Good quality"
                },
                "gemini-2.0-flash-lite": {
                    "description": "Lightweight model optimized for low latency",
                    "speed": "🚄 Ultra Fast",
                    "cost": "🪙 Very Low",
                    "quality": "📊 Standard quality"
                },
                "gemini-3.1-pro-preview": {
                    "description": "Cutting edge preview model",
                    "speed": "⚡ Fast",
                    "cost": "💰 Varies",
                    "quality": "🧪 Experimental"
                }
            }
            
            if selected_model_key in model_info:
                info = model_info[selected_model_key]
                st.info(f"**{info['description']}**\n\n{info['speed']} • {info['cost']} • {info['quality']}")
    
    else:
        # LM Studio not available
        st.button(
            "🌐 Web AI (Gemini)\n\nOnline • Comprehensive • Cloud-based",
            key="web_ai_only_selector_btn",
            width='stretch',
            disabled=False
        )
        st.session_state.ai_model_choice = "🌐 Web AI (Gemini)"
        
        st.markdown("---")
        st.warning("❌ **Local AI Not Available**")
        st.info("""
        **To enable Local AI:**
        1. Download and install [LM Studio](https://lmstudio.ai)
        2. Download a model (e.g., llama-3.2-3b or llama-3.2-3b-crop-recommender)
        3. Load the model in LM Studio
        4. Start the local server on `http://127.0.0.1:1234`
        5. Refresh this page
        
        **For Crop Recommendations:** Download "llama-3.2-3b-crop-recommender" for best results
        """)
    
    return st.session_state.get('ai_model_choice', '🌐 Web AI (Gemini)'), lm_studio_available


def display_model_status(compact: bool = False):
    """
    Display current model status bar
    
    Args:
        compact: If True, display minimal status in sidebar
    """
    manager = LocalAIManager()
    lm_studio_available = manager.check_connection()
    current_ai = st.session_state.get('ai_model_choice', '🌐 Web AI (Gemini)')
    
    if compact:
        st.sidebar.markdown("### 🤖 AI Model Status")
        
        if "Local AI" in current_ai and lm_studio_available:
            st.sidebar.success("✅ Local AI Active")
            models = manager.get_all_models()
            if models:
                active = manager.get_active_model()
                if active:
                    model_info = manager.get_model_info_display(active)
                    st.sidebar.markdown(f"{model_info['type']}")
                    if model_info['is_specialized']:
                        st.sidebar.success("✅ Specialized")
        else:
            st.sidebar.success("✅ Web AI Active")
            st.sidebar.markdown("Google Gemini 1.5 Flash")
    
    else:
        if "Local AI" in current_ai and lm_studio_available:
            st.info(f"**Current Model:** {current_ai}")
            models = manager.get_all_models()
            if models:
                active = manager.get_active_model()
                if active:
                    model_info = manager.get_model_info_display(active)
                    st.markdown(f"**Type:** {model_info['type']}")
                    st.markdown(f"**Size:** {model_info['parameters'].get('size', 'Unknown')}")
        else:
            st.info(f"**Current Model:** {current_ai}")


def detect_and_display_available_models():
    """
    Auto-detect and display all available models with detailed information
    """
    manager = LocalAIManager()
    
    if not manager.check_connection():
        st.error("❌ LM Studio is not running")
        return []
    
    models = manager.get_all_models()
    
    if not models:
        st.warning("No models loaded in LM Studio")
        return []
    
    st.success(f"✅ Found {len(models)} model(s)")
    
    # Display each model
    for idx, model_id in enumerate(models, 1):
        model_info = manager.get_model_info_display(model_id)
        
        with st.expander(f"{idx}. {model_info['type']} - {model_id}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if model_info['is_specialized']:
                    st.success(f"✅ {model_info['description']}")
                else:
                    st.info(f"ℹ️ {model_info['description']}")
                
                st.markdown("**Capabilities:**")
                for cap in model_info['capabilities']:
                    st.markdown(f"• {cap}")
            
            with col2:
                st.markdown("**Specs:**")
                st.markdown(f"- {model_info['parameters'].get('size', 'Unknown')}")
                st.markdown(f"- Type: {model_info['parameters'].get('type', 'Unknown')}")
                
                # Make model selectable
                if st.button(f"Use This Model", key=f"use_model_{idx}"):
                    st.session_state.selected_local_model = model_id
                    st.success(f"Selected: {model_id}")
                    st.rerun()
    
    return models


def create_model_comparison_table():
    """
    Create a comparison table of Web AI vs Local AI
    """
    comparison_data = {
        'Feature': [
            'Processing Speed',
            'Privacy',
            'Internet Required',
            'Cost',
            'Accuracy',
            'Customization',
            'Specialized Models',
            'Offline Capability'
        ],
        '🌐 Gemini AI': [
            '⚡ Very Fast',
            '⚠️ Cloud-based',
            '✅ Yes',
            'API charges',
            '⭐⭐⭐⭐⭐',
            'Limited',
            '✅ Multiple',
            '❌ No'
        ],
        '🏠 Local AI': [
            '⚙️ Variable',
            '✅ Completely Private',
            '❌ No',
            'One-time setup',
            '⭐⭐⭐⭐',
            '✅ Full control',
            '✅ Customizable',
            '✅ Yes'
        ]
    }
    
    st.table(comparison_data)
