import streamlit as st
import folium
from streamlit_folium import st_folium
import time

def create_location_map(default_lat=20.5937, default_lon=78.9629):
    """
    Create an interactive map for location selection
    Default coordinates are center of India
    """
    st.markdown("### 🗺️ Interactive Map - Click to Select Location")
    st.markdown("*Click anywhere on the map to select your location, or use the search options below*")
    
    # Initialize session state for map coordinates
    if 'selected_lat' not in st.session_state:
        st.session_state.selected_lat = default_lat
    if 'selected_lon' not in st.session_state:
        st.session_state.selected_lon = default_lon
    if 'location_from_map' not in st.session_state:
        st.session_state.location_from_map = False
    
    # Create the folium map
    m = folium.Map(
        location=[st.session_state.selected_lat, st.session_state.selected_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add marker for selected location
    folium.Marker(
        [st.session_state.selected_lat, st.session_state.selected_lon],
        popup=f"Selected Location\nLat: {st.session_state.selected_lat:.4f}\nLon: {st.session_state.selected_lon:.4f}",
        tooltip="Click to see coordinates",
        icon=folium.Icon(color='red', icon='map-pin', prefix='fa')
    ).add_to(m)
    
    # Add some major Indian cities as reference points
    indian_cities = [
        {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "popup": "Mumbai - Financial Capital"},
        {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "popup": "New Delhi - National Capital"},
        {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946, "popup": "Bangalore - Silicon Valley of India"},
        {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "popup": "Chennai - Detroit of India"},
        {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "popup": "Kolkata - City of Joy"},
        {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "popup": "Pune - Oxford of the East"},
        {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "popup": "Hyderabad - Cyberabad"},
        {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "popup": "Ahmedabad - Manchester of India"}
    ]
    
    # Add city markers
    for city in indian_cities:
        folium.CircleMarker(
            location=[city["lat"], city["lon"]],
            radius=8,
            popup=city["popup"],
            color='blue',
            fill=True,
            fillColor='lightblue',
            fillOpacity=0.7,
            tooltip=f"Click to select {city['name']}"
        ).add_to(m)
    
    # Display the map and capture click events
    map_data = st_folium(
        m,
        width=700,
        height=400,
        returned_objects=["last_object_clicked", "last_clicked"]
    )
    
    # Handle map clicks
    if map_data["last_clicked"] is not None:
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]
        
        # Update session state
        st.session_state.selected_lat = clicked_lat
        st.session_state.selected_lon = clicked_lon
        st.session_state.location_from_map = True
        
        # Show success message
        st.success(f"📍 Location selected: {clicked_lat:.4f}, {clicked_lon:.4f}")
        st.rerun()
    
    # Display current selection
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📍 Latitude", f"{st.session_state.selected_lat:.4f}")
    with col2:
        st.metric("📍 Longitude", f"{st.session_state.selected_lon:.4f}")
    with col3:
        if st.session_state.location_from_map:
            st.success("✅ From Map")
        else:
            st.info("🎯 Default Center")
    
    return st.session_state.selected_lat, st.session_state.selected_lon

def create_quick_city_selector():
    """
    Create quick buttons for major Indian cities
    """
    st.markdown("### 🏙️ Quick City Selection")
    st.markdown("*Click on any city to quickly jump to that location*")
    
    # Define major cities with their coordinates
    cities = {
        "Mumbai": (19.0760, 72.8777),
        "Delhi": (28.6139, 77.2090),
        "Bangalore": (12.9716, 77.5946),
        "Chennai": (13.0827, 80.2707),
        "Kolkata": (22.5726, 88.3639),
        "Pune": (18.5204, 73.8567),
        "Hyderabad": (17.3850, 78.4867),
        "Ahmedabad": (23.0225, 72.5714)
    }
    
    # Create city selection buttons in rows
    cols = st.columns(4)
    for i, (city_name, (lat, lon)) in enumerate(cities.items()):
        with cols[i % 4]:
            if st.button(f"📍 {city_name}", key=f"city_{city_name}"):
                st.session_state.selected_lat = lat
                st.session_state.selected_lon = lon
                st.session_state.location_from_map = True
                st.success(f"Selected {city_name}!")
                st.rerun()

def create_coordinate_input():
    """
    Allow manual coordinate input
    """
    st.markdown("### 🎯 Manual Coordinate Input")
    st.markdown("*Enter exact latitude and longitude coordinates*")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        manual_lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=st.session_state.selected_lat,
            step=0.0001,
            format="%.4f",
            help="Latitude coordinates (North-South position)"
        )
    
    with col2:
        manual_lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=st.session_state.selected_lon,
            step=0.0001,
            format="%.4f",
            help="Longitude coordinates (East-West position)"
        )
    
    with col3:
        st.markdown("") # Spacer
        if st.button("📍 Use Coordinates", type="primary"):
            st.session_state.selected_lat = manual_lat
            st.session_state.selected_lon = manual_lon
            st.session_state.location_from_map = True
            st.success("Coordinates updated!")
            st.rerun()

def get_location_from_map():
    """
    Get the currently selected location from the map
    Returns tuple of (lat, lon) or None if no location selected
    """
    if hasattr(st.session_state, 'selected_lat') and hasattr(st.session_state, 'selected_lon'):
        return st.session_state.selected_lat, st.session_state.selected_lon
    return None

def create_map_interface():
    """
    Create the complete map-based location selection interface
    """
    st.markdown("## 🗺️ Location Selection")
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["🗺️ Interactive Map", "🏙️ Quick Cities", "🎯 Coordinates"])
    
    with tab1:
        lat, lon = create_location_map()
    
    with tab2:
        create_quick_city_selector()
        if hasattr(st.session_state, 'selected_lat'):
            st.info(f"Current selection: {st.session_state.selected_lat:.4f}, {st.session_state.selected_lon:.4f}")
    
    with tab3:
        create_coordinate_input()
    
    # Return current coordinates
    return get_location_from_map()

def create_location_summary():
    """
    Display a summary of the selected location
    """
    if hasattr(st.session_state, 'selected_lat') and st.session_state.location_from_map:
        st.markdown("### 📍 Selected Location Summary")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **Coordinates:**
            - Latitude: {st.session_state.selected_lat:.4f}
            - Longitude: {st.session_state.selected_lon:.4f}
            """)
        
        with col2:
            # Try to get location name (basic region identification)
            region = get_indian_region(st.session_state.selected_lat, st.session_state.selected_lon)
            st.info(f"""
            **Region Information:**
            - Estimated Region: {region}
            - Climate Zone: {get_climate_zone(st.session_state.selected_lat)}
            """)
    
    return True

def get_indian_region(lat, lon):
    """
    Get approximate Indian region based on coordinates
    """
    if lat >= 30:
        return "Northern India"
    elif lat >= 23:
        if lon <= 75:
            return "Western India"
        else:
            return "Northern/Central India"
    elif lat >= 15:
        if lon <= 75:
            return "Western/Central India"
        else:
            return "Central/Eastern India"
    elif lat >= 8:
        if lon <= 75:
            return "Southern India (West)"
        else:
            return "Southern India (East)"
    else:
        return "Southern India"

def get_climate_zone(lat):
    """
    Get approximate climate zone based on latitude
    """
    if lat >= 30:
        return "Temperate/Sub-tropical"
    elif lat >= 23:
        return "Sub-tropical"
    elif lat >= 15:
        return "Tropical"
    else:
        return "Tropical/Equatorial"
