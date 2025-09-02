import streamlit as st
import json
from datetime import datetime
import base64
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import google.generativeai as genai
import os
import tempfile
import subprocess
from pathlib import Path

def extract_number_from_text(text):
    """
    Extract numeric value from text (e.g., "25 kg" -> 25)
    Enhanced to handle more text formats and edge cases
    """
    if not text or text == 'N/A' or text == 'Unknown':
        return 25  # Default value
    
    import re
    # Convert to string and normalize
    text = str(text).lower().strip()
    
    # Handle special non-numeric cases from AI responses
    if any(phrase in text for phrase in ['not specified', 'not available', 'data not', 'unknown']):
        return 25  # Default when data is missing
    
    # Handle qualitative descriptions
    if 'excellent' in text or 'very high' in text:
        return 40
    elif 'high' in text or 'good' in text:
        return 35
    elif 'moderate' in text or 'medium' in text:
        return 25
    elif 'low' in text or 'poor' in text:
        return 15
    elif 'very low' in text:
        return 10
    
    # Look for patterns like "25 kg", "about 30 liters", "approximately 20-25 kg"
    number_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:kg|kilograms?|kilogram)',  # "25 kg" variations
        r'(\d+(?:\.\d+)?)\s*(?:l|liters?|litres?|liter|litre)',  # "30 liters" variations
        r'(\d+(?:\.\d+)?)\s*(?:m|meters?|metres?|meter|metre)',  # "5 meters" variations
        r'(\d+(?:\.\d+)?)\s*(?:₹|rs\.?|rupees?)',  # "₹500" or "Rs 500"
        r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)',     # "20-25" (take the average)
        r'(\d+(?:\.\d+)?)\s*(?:to|or)\s*(\d+(?:\.\d+)?)',  # "20 to 25"
        r'(?:about|approximately|around|roughly)\s*(\d+(?:\.\d+)?)',  # "about 25"
        r'(\d+(?:\.\d+)?)',                     # Any standalone number
    ]
    
    for pattern in number_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Take the first match and first group
            match = matches[0]
            if isinstance(match, tuple):
                # For ranges like "20-25", take the average
                try:
                    num1, num2 = float(match[0]), float(match[1])
                    return int((num1 + num2) / 2)
                except (ValueError, IndexError):
                    return int(float(match[0]))
            else:
                try:
                    return int(float(match))
                except ValueError:
                    continue
    
    return 25  # Default fallback

def create_comprehensive_report_download(recommendations, env_data):
    """
    Create a comprehensive downloadable report with all plantation data and visualizations
    """
    if not recommendations or not env_data:
        return None
    
    st.markdown("### 📊 Comprehensive Plantation Report")
    st.markdown("Download your personalized plantation guide with all the details you need for success.")
    
    # Create interactive visualizations
    create_plant_visualizations(recommendations, env_data)
    
    # Create the report content
    report_content = generate_detailed_report(recommendations, env_data)
    
    # Create download buttons for different formats
    st.markdown("---")
    st.markdown("### 📥 Download Options")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # JSON format for technical users
        json_data = json.dumps({
            'location': env_data.get('location', 'Unknown'),
            'environmental_data': env_data,
            'recommendations': recommendations,
            'generation_date': datetime.now().isoformat(),
            'report_version': '2.0'
        }, indent=2)
        
        st.download_button(
            label="📁 Download JSON Data",
            data=json_data,
            file_name=f"plantation_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            help="Technical data format for developers"
        )
    
    with col2:
        # Markdown format for easy reading
        st.download_button(
            label="📖 Download Markdown Report",
            data=report_content,
            file_name=f"plantation_guide_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            help="Human-readable plantation guide"
        )
    
    with col3:
        # CSV format for Excel users
        csv_data = generate_csv_summary(recommendations)
        st.download_button(
            label="📊 Download CSV Summary",
            data=csv_data,
            file_name=f"plant_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            help="Spreadsheet-compatible summary"
        )
    
    with col4:
        # Simple PDF report for everyone
        with st.spinner("Generating simple PDF report..."):
            pdf_data = generate_simple_pdf_report(recommendations, env_data)
            if pdf_data:
                st.download_button(
                    label="📄 Download Simple PDF",
                    data=pdf_data,
                    file_name=f"simple_plantation_guide_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    help="Easy-to-read PDF report for everyone"
                )
    
    return True

def create_plant_visualizations(recommendations, env_data):
    """
    Create interactive visualizations for the plant recommendations
    """
    if not recommendations:
        st.warning("⚠️ No recommendations available for visualization. Please generate recommendations first.")
        return
    
    # Debug information (can be removed in production)
    with st.expander("🔍 Debug Information", expanded=False):
        st.write(f"**Number of recommendations:** {len(recommendations)}")
        st.write("**Sample recommendation structure:**")
        if recommendations:
            st.json(recommendations[0])
    
    # Convert recommendations to DataFrame for easier plotting
    df = create_dataframe_from_recommendations(recommendations)
    
    if df.empty:
        st.error("❌ Failed to process recommendation data for visualization.")
        return
    
    st.markdown("### 📊 Plantation Analytics Dashboard")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["🌱 Plant Overview", "🌬️ Environmental Impact", "💰 Economic Analysis", "📈 Growth Characteristics"])
    
    with tab1:
        create_plant_overview_charts(df)
    
    with tab2:
        create_environmental_impact_charts(df)
    
    with tab3:
        create_economic_analysis_charts(df)
    
    with tab4:
        create_growth_characteristics_charts(df)

def create_dataframe_from_recommendations(recommendations):
    """
    Convert recommendations to pandas DataFrame with enhanced data validation
    """
    data = []
    for plant in recommendations:
        # Get plant basic info
        scientific_name = plant.get('scientific_name', 'Unknown Plant')
        plant_name = scientific_name[:20] + '...' if len(scientific_name) > 20 else scientific_name
        
        # Get air quality benefits with fallbacks
        air_benefits = plant.get('air_quality_benefits', {})
        co2_text = air_benefits.get('co2_absorption') or air_benefits.get('carbon_absorption') or '25 kg'
        oxygen_text = air_benefits.get('oxygen_production') or air_benefits.get('o2_production') or '25 liters'
        
        # Get economic benefits with fallbacks
        economic_benefits = plant.get('economic_benefits', {})
        economics = plant.get('economics', {})  # Alternative key
        plantation_guide = plant.get('plantation_guide', {})
        
        initial_cost_text = (economic_benefits.get('initial_cost') or 
                           economics.get('initial_cost') or 
                           plantation_guide.get('cost') or 
                           '₹400')
        
        maintenance_cost_text = (economic_benefits.get('maintenance_cost_annual') or 
                               economics.get('maintenance_cost') or 
                               economic_benefits.get('annual_maintenance') or 
                               '₹600')
        
        # Get growth characteristics with fallbacks
        growth_chars = plant.get('growth_characteristics', {})
        growth_info = plant.get('growth_info', {})  # Alternative key
        
        growth_rate = (growth_chars.get('growth_rate') or 
                      growth_info.get('growth_rate') or 
                      plant.get('growth_rate') or 
                      'Medium')
        
        mature_height_text = (growth_chars.get('mature_height') or 
                            growth_chars.get('height') or 
                            growth_info.get('mature_height') or 
                            plant.get('mature_height') or 
                            '5 meters')
        
        space_req_text = (growth_chars.get('space_requirements') or 
                         growth_chars.get('space_required') or 
                         growth_info.get('space_requirements') or 
                         plant.get('space_requirements') or 
                         '3x3 meters')
        
        # Extract numeric values with validation
        co2_value = extract_number_from_text(co2_text)
        oxygen_value = extract_number_from_text(oxygen_text)
        initial_cost = extract_number_from_text(initial_cost_text)
        maintenance_cost = extract_number_from_text(maintenance_cost_text)
        mature_height = extract_number_from_text(mature_height_text)
        space_required = extract_number_from_text(space_req_text)
        
        # Validate environmental score
        env_score = plant.get('environmental_impact_score')
        if env_score is None or env_score == 'N/A':
            env_score = 7.5
        else:
            try:
                env_score = float(env_score)
                if env_score < 0 or env_score > 10:
                    env_score = 7.5
            except (ValueError, TypeError):
                env_score = 7.5
        
        row = {
            'Plant Name': plant_name,
            'Local Name': plant.get('local_name', 'N/A'),
            'Type': plant.get('plant_type', 'Tree'),
            'Environmental Score': env_score,
            'CO2 Absorption': max(co2_value, 1),  # Ensure minimum value
            'Oxygen Production': max(oxygen_value, 1),  # Ensure minimum value
            'Initial Cost': max(initial_cost, 100),  # Ensure minimum value
            'Annual Maintenance': max(maintenance_cost, 50),  # Ensure minimum value
            'Growth Rate': growth_rate,
            'Mature Height': max(mature_height, 1),  # Ensure minimum value
            'Space Required': max(space_required, 1)  # Ensure minimum value
        }
        data.append(row)
    
    return pd.DataFrame(data)

def create_plant_overview_charts(df):
    """
    Create overview charts for plant recommendations with improved data validation
    """
    # Validate DataFrame
    if df.empty:
        st.warning("No plant data available for overview.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Environmental Score Radar Chart
        if 'Environmental Score' in df.columns and not df['Environmental Score'].empty:
            # Ensure environmental scores are valid
            df['Environmental Score'] = pd.to_numeric(df['Environmental Score'], errors='coerce').fillna(7.5)
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=df['Environmental Score'].tolist(),
                theta=df['Plant Name'].tolist(),
                fill='toself',
                name='Environmental Impact',
                line_color='green',
                fillcolor='rgba(0, 150, 0, 0.3)',
                hovertemplate='<b>%{theta}</b><br>Environmental Score: %{r}/10<extra></extra>'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10]
                    )),
                showlegend=True,
                title="🌿 Environmental Impact Scores",
                title_x=0.5,
                height=400
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("No environmental score data available.")
    
    with col2:
        # Plant Type Distribution
        if 'Type' in df.columns and not df['Type'].empty:
            type_counts = df['Type'].value_counts()
            
            if not type_counts.empty:
                fig_pie = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="🌳 Plant Type Distribution",
                    color_discrete_sequence=['#2E8B57', '#90EE90', '#228B22', '#32CD32']
                )
                
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(height=400)
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No plant type data available.")
        else:
            st.info("No plant type data available.")

def create_environmental_impact_charts(df):
    """
    Create environmental impact visualizations with improved data validation
    """
    # Validate DataFrame
    if df.empty:
        st.warning("No data available for environmental impact analysis.")
        return
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['CO2 Absorption', 'Oxygen Production', 'Environmental Score']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(25)
    
    # Air Quality Benefits Comparison
    fig_air = make_subplots(
        rows=1, cols=2,
        subplot_titles=('CO2 Absorption (kg/year)', 'Oxygen Production (L/day)'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # CO2 Absorption Bar Chart
    fig_air.add_trace(
        go.Bar(
            x=df['Plant Name'],
            y=df['CO2 Absorption'],
            name='CO2 Absorption',
            marker_color='darkgreen',
            text=[f"{val:.0f}" for val in df['CO2 Absorption']],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>CO2 Absorption: %{y} kg/year<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Oxygen Production Bar Chart
    fig_air.add_trace(
        go.Bar(
            x=df['Plant Name'],
            y=df['Oxygen Production'],
            name='Oxygen Production',
            marker_color='lightgreen',
            text=[f"{val:.0f}" for val in df['Oxygen Production']],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Oxygen Production: %{y} L/day<extra></extra>'
        ),
        row=1, col=2
    )
    
    fig_air.update_xaxes(tickangle=45)
    fig_air.update_layout(
        title_text="🌬️ Air Quality Benefits Comparison",
        title_x=0.5,
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig_air, use_container_width=True)
    
    # Environmental Impact Summary Cards with validation
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_co2 = max(df['CO2 Absorption'].sum(), 1)  # Ensure minimum value
        st.metric(
            label="🏭 Total CO2 Absorption",
            value=f"{total_co2:,.0f} kg/year",
            delta=f"≈ {total_co2/1000:.1f} tons annually"
        )
    
    with col2:
        total_oxygen = max(df['Oxygen Production'].sum(), 1)  # Ensure minimum value
        st.metric(
            label="💨 Total Oxygen Production",
            value=f"{total_oxygen:,.0f} L/day",
            delta=f"≈ {total_oxygen*365/1000:.0f}k L/year"
        )
    
    with col3:
        avg_env_score = df['Environmental Score'].mean()
        if pd.isna(avg_env_score) or avg_env_score == 0:
            avg_env_score = 7.5
        st.metric(
            label="📊 Avg Environmental Score",
            value=f"{avg_env_score:.1f}/10",
            delta="Excellent sustainability rating" if avg_env_score >= 7 else "Good sustainability rating"
        )
    
    with col4:
        total_plants = len(df)
        st.metric(
            label="🌱 Total Plants",
            value=f"{total_plants}",
            delta="Diverse ecosystem" if total_plants >= 5 else "Growing ecosystem"
        )

def create_economic_analysis_charts(df):
    """
    Create economic analysis visualizations
    """
    # Cost Analysis
    fig_cost = go.Figure()
    
    # Initial Cost
    fig_cost.add_trace(go.Bar(
        name='Initial Cost (₹)',
        x=df['Plant Name'],
        y=df['Initial Cost'],
        marker_color='lightcoral',
        text=df['Initial Cost'],
        textposition='auto'
    ))
    
    # Annual Maintenance Cost
    fig_cost.add_trace(go.Bar(
        name='Annual Maintenance (₹)',
        x=df['Plant Name'],
        y=df['Annual Maintenance'],
        marker_color='salmon',
        text=df['Annual Maintenance'],
        textposition='auto'
    ))
    
    fig_cost.update_layout(
        title='💰 Cost Analysis Comparison',
        title_x=0.5,
        xaxis_title='Plant Species',
        yaxis_title='Cost (₹)',
        barmode='group',
        height=500
    )
    
    fig_cost.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig_cost, use_container_width=True)
    
    # Economic Summary
    col1, col2 = st.columns(2)
    
    with col1:
        # Cost Distribution Pie Chart
        total_initial = df['Initial Cost'].sum()
        total_maintenance = df['Annual Maintenance'].sum()
        
        fig_cost_pie = px.pie(
            values=[total_initial, total_maintenance],
            names=['Initial Investment', 'Annual Maintenance'],
            title="💸 Cost Distribution",
            color_discrete_sequence=['#FF6B6B', '#FFA07A']
        )
        
        st.plotly_chart(fig_cost_pie, use_container_width=True)
    
    with col2:
        # Economic Metrics
        st.markdown("#### 📊 Economic Summary")
        
        total_initial_cost = df['Initial Cost'].sum()
        total_annual_maintenance = df['Annual Maintenance'].sum()
        cost_per_plant = total_initial_cost / max(len(df), 1)  # Prevent division by zero
        
        st.metric("💰 Total Initial Investment", f"₹{total_initial_cost:,.0f}")
        st.metric("🔧 Total Annual Maintenance", f"₹{total_annual_maintenance:,.0f}")
        st.metric("🌱 Average Cost per Plant", f"₹{cost_per_plant:,.0f}")
        
        # 5-Year projection
        five_year_cost = total_initial_cost + (total_annual_maintenance * 5)
        st.metric("📈 5-Year Total Investment", f"₹{five_year_cost:,.0f}")

def create_growth_characteristics_charts(df):
    """
    Create growth characteristics visualizations with improved data validation
    """
    # Validate DataFrame
    if df.empty:
        st.warning("No data available for growth characteristics analysis.")
        return
    
    # Ensure numeric columns are properly typed
    numeric_columns = ['Mature Height', 'Space Required']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(5)
    
    # Growth Rate Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        growth_counts = df['Growth Rate'].value_counts()
        
        if not growth_counts.empty:
            fig_growth = px.bar(
                x=growth_counts.index,
                y=growth_counts.values,
                title="📈 Growth Rate Distribution",
                color=growth_counts.values,
                color_continuous_scale='Greens',
                text=growth_counts.values
            )
            
            fig_growth.update_traces(textposition='auto')
            fig_growth.update_layout(
                xaxis_title='Growth Rate',
                yaxis_title='Number of Plants',
                showlegend=False
            )
            
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("No growth rate data available.")
    
    with col2:
        # Mature Height vs Space Requirements Scatter
        if len(df) > 0:
            fig_scatter = px.scatter(
                df,
                x='Space Required',
                y='Mature Height',
                size='Environmental Score',
                color='Type',
                hover_name='Plant Name',
                title="🌳 Height vs Space Requirements",
                labels={
                    'Space Required': 'Space Required (sq meters)',
                    'Mature Height': 'Mature Height (meters)'
                }
            )
            
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No height/space data available.")
    
    # Space Planning Visualization
    st.markdown("#### 🗺️ Space Planning Guide")
    
    # Create metrics with validation
    total_space = max(df['Space Required'].sum(), 1)
    avg_height = df['Mature Height'].mean()
    if pd.isna(avg_height) or avg_height == 0:
        avg_height = 5.0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📏 Total Space Required",
            value=f"{total_space:,.0f} sq meters",
            delta=f"≈ {total_space/10000:.2f} hectares"
        )
    
    with col2:
        st.metric(
            label="📊 Average Mature Height",
            value=f"{avg_height:.1f} meters",
            delta="Excellent canopy coverage" if avg_height >= 8 else "Good canopy coverage"
        )
    
    with col3:
        density = len(df) / max(total_space, 1)
        st.metric(
            label="🌱 Planting Density",
            value=f"{density:.3f} plants/sq meter",
            delta="Optimal spacing" if density <= 0.5 else "Dense planting"
        )

def generate_detailed_report(recommendations, env_data):
    """
    Generate a comprehensive markdown report
    """
    report = f"""# 🌿 Comprehensive Plantation Guide & Report

**Generated on:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
**Location:** {env_data.get('location', 'Unknown Location')}
**Report Version:** 2.0 (AI-Enhanced with Agentic Insights)

---

## 📍 Environmental Analysis Summary

### 🌡️ Climate Conditions
- **Temperature:** {env_data.get('temperature', 'N/A')}°C
- **Humidity:** {env_data.get('humidity', 'N/A')}%
- **Annual Rainfall:** {env_data.get('rainfall', 'N/A')}mm
- **Climate Type:** {env_data.get('climate_type', 'N/A')}

### 🧪 Soil Characteristics
- **pH Level:** {env_data.get('soil_ph', 'N/A')}
- **Soil Texture:** {env_data.get('soil_texture', 'N/A')}
- **Organic Carbon:** {env_data.get('soil_organic_carbon', 'N/A')}%

### 🌬️ Air Quality Status
- **Air Quality Index:** {env_data.get('aqi', 106)} ({env_data.get('aqi_rating', 3)}/5 rating)
- **PM2.5 Level:** {env_data.get('pm2_5', 'N/A')} μg/m³

---

## 🌱 AI-Recommended Plants ({len(recommendations)} Species)

"""
    
    for i, plant in enumerate(recommendations, 1):
        report += generate_plant_section(plant, i)
    
    report += f"""
---

## 📋 Implementation Timeline

### Month 1-2: Preparation Phase
- Soil testing and preparation
- Sapling procurement
- Site layout planning
- Initial infrastructure setup

### Month 3-6: Planting Phase
- Plant according to seasonal recommendations
- Establish watering schedule
- Install support systems
- Begin monitoring routine

### Month 7-12: Establishment Phase
- Regular maintenance and care
- Pest and disease monitoring
- Growth tracking
- Adjustments based on plant response

### Year 2+: Maturation Phase
- Reduced intervention
- Harvest planning (if applicable)
- Expansion planning
- Long-term maintenance

---

## 📈 Expected Environmental Impact

### 🌬️ Air Quality Improvement
- **Total CO2 Absorption:** {sum(extract_number_from_text(p.get('air_quality_benefits', {}).get('co2_absorption', '25 kg')) for p in recommendations)} kg/year
- **Total Oxygen Production:** {sum(extract_number_from_text(p.get('air_quality_benefits', {}).get('oxygen_production', '25 liters')) for p in recommendations)} liters/day
- **Estimated AQI Improvement:** 5-15 points in local vicinity

### 🌱 Biodiversity Benefits
- Native species support
- Wildlife habitat creation
- Pollinator attraction
- Ecosystem restoration

### 💰 Economic Returns
- Property value enhancement: 5-15%
- Energy savings from natural cooling
- Potential income from fruits/timber
- Long-term maintenance cost reduction

---

## 🎯 Success Metrics & Monitoring

### Growth Indicators
- Plant height and spread measurements
- Leaf health and color assessment
- Root development evaluation
- Overall vigor scoring

### Environmental Measurements
- Local temperature reduction
- Air quality improvement
- Soil health enhancement
- Water retention improvement

### Economic Tracking
- Initial investment costs
- Ongoing maintenance expenses
- Property value changes
- Additional income generation

---

## 📞 Expert Consultation & Support

### When to Seek Help
- Unusual plant behavior or health issues
- Pest or disease outbreaks
- Extreme weather damage
- Growth rate concerns

### Resources
- Local agricultural extension offices
- Urban forestry departments
- Online plant health databases
- Community gardening groups

---

## 📚 Additional Resources

### Recommended Reading
- "Urban Forest Management in India" - Government Guidelines
- Local climate-specific planting guides
- Sustainable gardening practices

### Online Tools
- Plant health monitoring apps
- Weather tracking for gardening
- Soil testing services
- Local nursery directories

---

*This report was generated by the Crop & Afforestation AI Bot using advanced environmental analysis and machine learning recommendations. For best results, consult with local experts and adapt recommendations based on micro-climate conditions.*

**Report ID:** CR-{datetime.now().strftime('%Y%m%d%H%M')}-{hash(str(recommendations)) % 10000:04d}
"""
    
    return report

def generate_plant_section(plant, index):
    """
    Generate detailed section for each plant
    """
    section = f"""
### {index}. {plant.get('scientific_name', 'Unknown Plant')}

#### 🌱 **{plant.get('common_name', 'N/A')}**  
**Local Name:** {plant.get('local_name', 'N/A')}  
**Family:** {plant.get('family', 'N/A')}  
**Type:** {plant.get('plant_type', 'N/A')}  
**Environmental Impact Score:** {plant.get('environmental_impact_score', 'N/A')}/10

#### 🔍 Suitability Analysis
{plant.get('suitability_analysis', 'Well-suited for local conditions.')}

#### 🌬️ Air Quality Benefits
- **Pollution Reduction:** {plant.get('air_quality_benefits', {}).get('pollution_reduction', 'Improves air quality')}
- **Oxygen Production:** {plant.get('air_quality_benefits', {}).get('oxygen_production', 'N/A')}
- **CO2 Absorption:** {plant.get('air_quality_benefits', {}).get('co2_absorption', 'N/A')}
- **AQI Improvement:** {plant.get('air_quality_benefits', {}).get('aqi_improvement', 'N/A')}

#### 🌱 Plantation Guide
- **Best Season:** {plant.get('plantation_guide', {}).get('best_season', 'Spring/Early Monsoon')}
- **Soil Preparation:** {plant.get('plantation_guide', {}).get('soil_preparation', 'Standard preparation required')}
- **Planting Method:** {plant.get('plantation_guide', {}).get('planting_method', 'Follow standard practices')}
- **Initial Care:** {plant.get('plantation_guide', {}).get('initial_care', 'Regular watering and monitoring')}

#### 💧 Watering Schedule
- **Seedling Stage:** {plant.get('watering_patterns', {}).get('seedling_stage', 'Daily watering')}
- **Young Plant:** {plant.get('watering_patterns', {}).get('young_plant', 'Alternate day watering')}
- **Mature Plant:** {plant.get('watering_patterns', {}).get('mature_plant', 'Weekly watering')}
- **Water Conservation:** {plant.get('watering_patterns', {}).get('water_conservation_tips', 'Use mulching')}

#### 📈 Growth Characteristics
- **Mature Height:** {plant.get('growth_characteristics', {}).get('mature_height', '5-10 meters')}
- **Spread:** {plant.get('growth_characteristics', {}).get('mature_spread', '4-8 meters')}
- **Growth Rate:** {plant.get('growth_characteristics', {}).get('growth_rate', 'Medium')}
- **Lifespan:** {plant.get('growth_characteristics', {}).get('lifespan', '20-50 years')}
- **Space Required:** {plant.get('growth_characteristics', {}).get('space_requirements', '3x3 meters')}

#### 💰 Economic Analysis
- **Initial Cost:** {plant.get('economic_benefits', {}).get('initial_cost', '₹200-500')}
- **Annual Maintenance:** {plant.get('economic_benefits', {}).get('maintenance_cost_annual', '₹300-800')}
- **Property Value Impact:** {plant.get('economic_benefits', {}).get('property_value_impact', '5-15% increase')}
- **Economic Returns:** {plant.get('economic_benefits', {}).get('economic_returns', 'Environmental benefits')}

#### ⚠️ Challenges & Solutions
- **Common Problems:** {plant.get('challenges_and_solutions', {}).get('common_problems', 'Standard plant issues')}
- **Pest Management:** {plant.get('challenges_and_solutions', {}).get('pest_management', 'Natural methods')}
- **Disease Prevention:** {plant.get('challenges_and_solutions', {}).get('disease_prevention', 'Regular monitoring')}
- **Troubleshooting:** {plant.get('challenges_and_solutions', {}).get('troubleshooting', 'Quick response to issues')}

#### 🎯 Goal Alignment
{plant.get('user_goal_alignment', 'Aligns well with environmental objectives.')}

#### 🎁 Additional Benefits
{plant.get('additional_uses', 'Environmental and aesthetic value.')}

---
"""
    return section

def generate_csv_summary(recommendations):
    """
    Generate CSV summary for spreadsheet analysis
    """
    csv_content = "Plant Name,Local Name,Type,Environmental Score,CO2 Absorption (kg/year),Oxygen Production (L/day),Initial Cost,Maintenance Cost (annual),Growth Rate,Mature Height,Space Required\n"
    
    for plant in recommendations:
        name = plant.get('scientific_name', 'Unknown').replace(',', ';')
        local_name = plant.get('local_name', 'N/A').replace(',', ';')
        plant_type = plant.get('plant_type', 'N/A')
        env_score = plant.get('environmental_impact_score', 7.5)
        co2 = extract_number_from_text(plant.get('air_quality_benefits', {}).get('co2_absorption', '25 kg'))
        oxygen = extract_number_from_text(plant.get('air_quality_benefits', {}).get('oxygen_production', '25 liters'))
        cost = plant.get('economic_benefits', {}).get('initial_cost', '₹400').replace(',', ';')
        maintenance = plant.get('economic_benefits', {}).get('maintenance_cost_annual', '₹600').replace(',', ';')
        growth_rate = plant.get('growth_characteristics', {}).get('growth_rate', 'Medium')
        height = plant.get('growth_characteristics', {}).get('mature_height', '8 meters').replace(',', ';')
        space = plant.get('growth_characteristics', {}).get('space_requirements', '3x3 meters').replace(',', ';')
        
        csv_content += f"{name},{local_name},{plant_type},{env_score},{co2},{oxygen},{cost},{maintenance},{growth_rate},{height},{space}\n"
    
    return csv_content

def generate_simple_pdf_report(recommendations, env_data):
    """
    Generate a simple, user-friendly PDF report using ReportLab directly
    """
    try:
        # Skip AI LaTeX generation and go directly to ReportLab for better reliability
        print("Generating PDF report using ReportLab...")
        
        # Create enhanced PDF with actual recommendation data
        pdf_data = create_enhanced_reportlab_pdf(recommendations, env_data)
        
        return pdf_data
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None

def create_enhanced_reportlab_pdf(recommendations, env_data):
    """
    Create a professional PDF using ReportLab with real recommendation data
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import darkgreen, black, lightgrey
        from reportlab.lib import colors
        import io
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=72)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=darkgreen,
            spaceAfter=30,
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=darkgreen,
            spaceAfter=20,
            alignment=1,  # Center alignment
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=darkgreen,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=darkgreen,
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Build content using real data
        story = []
        
        # Title and subtitle
        location = env_data.get('location', 'Your Location')
        story.append(Paragraph("🌱 Your Personal Plantation Guide", title_style))
        story.append(Paragraph(f"Customized for {location}", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Introduction
        story.append(Paragraph("Welcome to Your Personalized Plantation Guide", heading_style))
        story.append(Paragraph(
            f"This report has been specially created for your location in {location}. "
            "Our AI system has analyzed your area's climate, soil, and air quality to recommend the best plants "
            "that will thrive and provide maximum environmental benefits for your specific conditions.",
            normal_style
        ))
        story.append(Spacer(1, 15))
        
        # Environmental Summary using real data
        story.append(Paragraph("🌍 Your Location's Environmental Summary", heading_style))
        
        # Create environmental data table with real values
        env_table_data = [
            ["Parameter", "Value", "Suitability"],
            ["Temperature", f"{env_data.get('temperature', 25)}°C", "Good for tropical plants"],
            ["Humidity", f"{env_data.get('humidity', 65)}%", "Optimal moisture levels"],
            ["Annual Rainfall", f"{env_data.get('rainfall', 1000)}mm", "Adequate water supply"],
            ["Air Quality Index", f"{env_data.get('aqi', 106)} ({env_data.get('aqi_rating', 3)}/5)", "Plants will help improve air quality"],
            ["Climate Type", env_data.get('climate_type', 'Tropical'), "Suitable for diverse vegetation"]
        ]
        
        env_table = Table(env_table_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        env_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(env_table)
        story.append(Spacer(1, 20))
        
        # Plant Recommendations using real AI data
        story.append(Paragraph("🌿 Top Recommended Plants for Your Area", heading_style))
        
        # Use actual recommendations from AI (limit to top 5 for comprehensive coverage)
        for i, plant in enumerate(recommendations[:5], 1):
            if plant.get('error'):
                continue  # Skip error entries
                
            # Extract plant information
            scientific_name = plant.get('scientific_name', 'Unknown')
            common_name = plant.get('common_name', 'Unknown')
            local_name = plant.get('local_name', 'N/A')
            plant_type = plant.get('plant_type', 'Plant')
            
            # Create display name
            display_name = f"{common_name}"
            if local_name and local_name != 'N/A':
                display_name += f" ({local_name})"
            
            story.append(Paragraph(f"{i}. {display_name}", subheading_style))
            
            # Add plant details
            story.append(Paragraph(f"<b>Scientific Name:</b> {scientific_name}", normal_style))
            story.append(Paragraph(f"<b>Type:</b> {plant_type}", normal_style))
            
            # Suitability score and analysis
            suitability_score = plant.get('suitability_score', '7/10')
            story.append(Paragraph(f"<b>Suitability Score:</b> {suitability_score}", normal_style))
            
            # Benefits (shortened for PDF)
            benefits = plant.get('air_quality_benefits', {})
            pollution_reduction = benefits.get('pollution_reduction', 'Air purification')
            if len(pollution_reduction) > 100:
                pollution_reduction = pollution_reduction[:97] + "..."
            story.append(Paragraph(f"<b>Air Quality Benefits:</b> {pollution_reduction}", normal_style))
            
            # Care instructions (simplified)
            watering = plant.get('watering_patterns', {}).get('mature_plant', 'Regular watering as needed')
            if len(watering) > 80:
                watering = watering[:77] + "..."
            story.append(Paragraph(f"<b>Care Instructions:</b> {watering}", normal_style))
            
            # Cost and space
            cost = plant.get('economic_benefits', {}).get('initial_cost', '₹300-500')
            space = plant.get('growth_characteristics', {}).get('space_requirements', '3x3 meters')
            story.append(Paragraph(f"<b>Approximate Cost:</b> {cost}", normal_style))
            story.append(Paragraph(f"<b>Space Required:</b> {space}", normal_style))
            
            story.append(Spacer(1, 12))
        
        # Next Steps
        story.append(Paragraph("📋 Your Next Steps", heading_style))
        next_steps = [
            "1. Choose 1-2 plants from the recommendations above based on your space and budget",
            "2. Visit your local nursery to purchase healthy saplings",
            "3. Prepare the planting area according to space requirements",
            "4. Plant during the recommended season (typically post-monsoon or pre-monsoon)",
            "5. Follow the care instructions and monitor growth regularly",
            "6. Join local gardening communities for ongoing support and tips"
        ]
        
        for step in next_steps:
            story.append(Paragraph(step, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Benefits summary
        story.append(Paragraph("🌟 Benefits You'll Enjoy", heading_style))
        benefits_text = (
            "By following this plantation guide, you'll contribute to cleaner air, "
            "reduced pollution, increased biodiversity, and a healthier environment. "
            "Your plants will also provide natural cooling, potentially reduce your "
            "electricity bills, and increase your property value over time."
        )
        story.append(Paragraph(benefits_text, normal_style))
        
        story.append(Spacer(1, 15))
        
        # Final encouragement
        story.append(Paragraph("🌱 Start Your Green Journey Today!", heading_style))
        story.append(Paragraph(
            f"These recommendations are specifically tailored for {location} and will thrive in your local conditions. "
            "Every plant you grow is a step towards a sustainable future. "
            "Start small, be consistent, and watch your green space flourish!",
            normal_style
        ))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph("Happy Planting! 🌿", subtitle_style))
        
        # Add footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')} | AI-Powered Plantation Recommendations", footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print("Enhanced PDF generated successfully using ReportLab with real data")
        return pdf_data
        
    except ImportError as ie:
        print(f"ReportLab not available: {ie}")
        return create_basic_text_report(recommendations, env_data)
    except Exception as e:
        print(f"Error creating enhanced PDF: {e}")
        return create_basic_text_report(recommendations, env_data)

def create_basic_text_report(recommendations, env_data):
    """
    Create a basic text report if PDF generation fails completely
    """
    try:
        location = env_data.get('location', 'Your Location')
        
        text_content = f"""
PLANTATION REPORT FOR {location.upper()}
{'=' * (len(location) + 25)}

Dear Plant Enthusiast,

Thank you for using our AI-powered plantation recommendation system!

ENVIRONMENTAL CONDITIONS:
- Temperature: {env_data.get('temperature', 25)}°C
- Humidity: {env_data.get('humidity', 65)}%
- Rainfall: {env_data.get('rainfall', 1000)}mm/year
- Air Quality Index: {env_data.get('aqi', 106)} ({env_data.get('aqi_rating', 3)}/5)

TOP RECOMMENDED PLANTS:
"""
        
        for i, plant in enumerate(recommendations[:5], 1):
            if plant.get('error'):
                continue
            
            text_content += f"""
{i}. {plant.get('common_name', 'Unknown')} ({plant.get('local_name', 'N/A')})
   - Type: {plant.get('plant_type', 'Plant')}
   - Suitability: {plant.get('suitability_score', '7/10')}
   - Benefits: {plant.get('air_quality_benefits', {}).get('pollution_reduction', 'Air purification')[:80]}...
   - Cost: {plant.get('economic_benefits', {}).get('initial_cost', '₹300-500')}
"""
        
        text_content += """

NEXT STEPS:
1. Visit your local nursery
2. Choose plants suitable for your space and budget
3. Follow proper planting and care instructions
4. Monitor growth and adjust care as needed

Happy Planting! 🌱

Note: This is a simplified text version. For the full interactive experience,
please visit our web application.
"""
        
        return text_content.encode('utf-8')
        
    except Exception as e:
        print(f"Error creating basic text report: {e}")
        return b"Error generating report. Please try again."

# LaTeX-related functions removed - using ReportLab directly for better reliability

def convert_latex_to_pdf(latex_content):
    """
    Convert LaTeX content to PDF using pdflatex or fallback to ReportLab
    """
    try:
        # Skip LaTeX attempt for now and go directly to ReportLab for better reliability
        print("Using ReportLab for PDF generation (LaTeX not required)")
        return create_simple_reportlab_pdf(latex_content)
            
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        return None

def create_simple_reportlab_pdf(latex_content):
    """
    Create a professional PDF using ReportLab - enhanced version
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import darkgreen, black, lightgrey
        from reportlab.lib import colors
        import io
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=72)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=darkgreen,
            spaceAfter=30,
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=darkgreen,
            spaceAfter=20,
            alignment=1,  # Center alignment
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=darkgreen,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'SubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=darkgreen,
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Build content - we'll extract info from the LaTeX or use defaults
        story = []
        
        # Title and subtitle
        story.append(Paragraph("🌱 Your Personal Plantation Guide", title_style))
        story.append(Paragraph("Customized for Your Location", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Introduction
        story.append(Paragraph("Welcome to Your Personalized Plantation Guide", heading_style))
        story.append(Paragraph(
            "This report has been specially created based on your specific location and environmental conditions. "
            "Our AI system has analyzed your area's climate, soil, and air quality to recommend the best plants "
            "that will thrive and provide maximum environmental benefits.",
            normal_style
        ))
        story.append(Spacer(1, 15))
        
        # Environmental Summary
        story.append(Paragraph("🌍 Your Location's Environmental Summary", heading_style))
        env_data = [
            ["Parameter", "Value", "Impact"],
            ["Temperature", "25-30°C", "Suitable for tropical plants"],
            ["Humidity", "60-70%", "Good moisture levels"],
            ["Rainfall", "800-1200mm/year", "Adequate water supply"],
            ["Air Quality", "Moderate", "Plants will help improve air"],
        ]
        
        env_table = Table(env_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        env_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(env_table)
        story.append(Spacer(1, 20))
        
        # Plant Recommendations
        story.append(Paragraph("🌿 Top Recommended Plants for Your Area", heading_style))
        
        # Sample plant recommendations (in real implementation, these would come from the AI)
        plants = [
            {
                "name": "Neem Tree (नीम)",
                "type": "Tree",
                "benefits": "Excellent air purifier, natural pesticide, medicinal properties",
                "care": "Water regularly for first year, minimal maintenance after establishment",
                "cost": "₹300-500",
                "space": "4x4 meters"
            },
            {
                "name": "Tulsi (तुलसी)",
                "type": "Herb",
                "benefits": "Air purification, medicinal uses, spiritual significance",
                "care": "Daily watering, partial sunlight, regular pruning",
                "cost": "₹50-100",
                "space": "1x1 meter"
            },
            {
                "name": "Drumstick Tree (सहजन)",
                "type": "Tree",
                "benefits": "Nutritious leaves and pods, drought tolerant, fast growing",
                "care": "Minimal watering once established, harvest leaves regularly",
                "cost": "₹200-400",
                "space": "3x3 meters"
            }
        ]
        
        for i, plant in enumerate(plants, 1):
            story.append(Paragraph(f"{i}. {plant['name']}", subheading_style))
            story.append(Paragraph(f"<b>Type:</b> {plant['type']}", normal_style))
            story.append(Paragraph(f"<b>Benefits:</b> {plant['benefits']}", normal_style))
            story.append(Paragraph(f"<b>Care Instructions:</b> {plant['care']}", normal_style))
            story.append(Paragraph(f"<b>Approximate Cost:</b> {plant['cost']}", normal_style))
            story.append(Paragraph(f"<b>Space Required:</b> {plant['space']}", normal_style))
            story.append(Spacer(1, 12))
        
        # Next Steps
        story.append(Paragraph("📋 Your Next Steps", heading_style))
        next_steps = [
            "1. Choose 1-2 plants from the recommendations above based on your space and budget",
            "2. Visit your local nursery to purchase healthy saplings",
            "3. Prepare the planting area according to space requirements",
            "4. Plant during the recommended season (typically post-monsoon)",
            "5. Follow the care instructions and monitor growth regularly",
            "6. Join local gardening communities for ongoing support and tips"
        ]
        
        for step in next_steps:
            story.append(Paragraph(step, normal_style))
        
        story.append(Spacer(1, 20))
        
        # Final encouragement
        story.append(Paragraph("🌟 Final Note", heading_style))
        story.append(Paragraph(
            "Congratulations on taking this important step towards a greener environment! "
            "These plant recommendations are specifically selected for your location and will provide "
            "excellent air purification, environmental benefits, and personal satisfaction. "
            "Remember, every plant you grow contributes to a healthier planet. "
            "Start small, be consistent, and watch your green space flourish!",
            normal_style
        ))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph("Happy Planting! 🌱", subtitle_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print("PDF generated successfully using ReportLab")
        return pdf_data
        
    except ImportError as ie:
        print(f"ReportLab not available: {ie}")
        return create_basic_text_pdf()
    except Exception as e:
        print(f"Error creating ReportLab PDF: {e}")
        return create_basic_text_pdf()

def create_basic_text_pdf():
    """
    Create a very basic PDF if ReportLab fails
    """
    try:
        import io
        # This is a minimal fallback - in practice, you might want to use another library
        # or create a simple text file instead
        print("Creating basic text-based report...")
        
        # Create a simple text report as fallback
        text_content = """
PLANTATION REPORT
=================

Dear Plant Enthusiast,

Thank you for using our AI-powered plantation recommendation system!

Your personalized plant recommendations have been generated based on your 
specific location and environmental conditions.

RECOMMENDED PLANTS:
1. Neem Tree (नीम) - Excellent air purifier
2. Tulsi (तुलसी) - Medicinal herb with air purification
3. Drumstick Tree (सहजन) - Nutritious and drought tolerant

NEXT STEPS:
- Visit your local nursery
- Choose plants suitable for your space
- Follow proper planting and care instructions
- Monitor growth and adjust care as needed

For the complete interactive experience with detailed visualizations,
please ensure all dependencies are properly installed.

Happy Planting! 🌱

Note: This is a simplified version due to PDF generation limitations.
        """
        
        # For now, return the text content as bytes
        # In a real implementation, you might use a different PDF library
        return text_content.encode('utf-8')
        
    except Exception as e:
        print(f"Error creating basic PDF: {e}")
        return None
