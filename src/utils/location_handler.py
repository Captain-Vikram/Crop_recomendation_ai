import geocoder
import re

def get_lat_lon(location_input, method="pin_code"):
    """
    Convert location input (PIN code or city name) to latitude/longitude
    """
    try:
        if method == "pin_code":
            return get_lat_lon_from_pin(location_input)
        elif method == "gps":
            return get_gps_location()
        elif method == "city":
            return get_lat_lon_from_city(location_input)
        else:
            return None, None
    except Exception as e:
        print(f"Error getting location: {e}")
        return None, None

def get_lat_lon_from_pin(pin_code):
    """
    Convert Indian PIN code to latitude/longitude
    """
    if not pin_code or len(pin_code) != 6 or not pin_code.isdigit():
        return None, None
    
    try:
        # First try the approximate location (more reliable)
        coords = get_approximate_location_from_pin(pin_code)
        if coords != (20.5937, 78.9629):  # If not default fallback
            return coords
        
        # If approximate fails, use geocoding with proper headers
        return geocode_pin_code_with_headers(pin_code)
    except Exception as e:
        print(f"Error in get_lat_lon: {e}")
        return get_approximate_location_from_pin(pin_code)

def get_lat_lon_from_city(city_name):
    """
    Get latitude/longitude from city name
    """
    try:
        # Use custom geocoding with proper headers
        return geocode_city_with_headers(city_name)
    except Exception as e:
        print(f"Error in get_lat_lon_from_city: {e}")
        return 20.5937, 78.9629  # Default to center of India

def geocode_pin_code_with_headers(pin_code):
    """
    Geocode PIN code using proper headers to avoid 403 errors
    """
    import requests
    import time
    
    try:
        time.sleep(1)  # Rate limiting
        
        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            'User-Agent': 'CropRecommendationBot/1.0 (educational-project)',
            'Accept': 'application/json',
            'Accept-Language': 'en'
        }
        
        params = {
            'q': f"{pin_code}, India",
            'format': 'json',
            'addressdetails': 1,
            'limit': 1
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
        
        # Fallback to approximate location
        return get_approximate_location_from_pin(pin_code)
        
    except Exception as e:
        print(f"Geocoding failed for PIN {pin_code}: {e}")
        return get_approximate_location_from_pin(pin_code)

def geocode_city_with_headers(city_name):
    """
    Geocode city name using proper headers to avoid 403 errors
    """
    import requests
    import time
    
    try:
        time.sleep(1)  # Rate limiting
        
        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            'User-Agent': 'CropRecommendationBot/1.0 (educational-project)',
            'Accept': 'application/json',
            'Accept-Language': 'en'
        }
        
        params = {
            'q': f"{city_name}, India",
            'format': 'json',
            'addressdetails': 1,
            'limit': 1
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
        
        # Fallback to default center of India
        return 20.5937, 78.9629
        
    except Exception as e:
        print(f"Geocoding failed for city {city_name}: {e}")
        return 20.5937, 78.9629

def get_gps_location():
    """
    Get current GPS location (simplified version)
    Note: This would need browser-based geolocation in a real Streamlit app
    """
    try:
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng[0], g.latlng[1]
        else:
            # Default to Delhi, India if GPS fails
            return 28.6139, 77.2090
    except:
        # Default to Delhi, India
        return 28.6139, 77.2090

def get_approximate_location_from_pin(pin_code):
    """
    Get approximate location based on PIN code ranges
    This is a simplified mapping of Indian PIN code regions
    """
    pin_int = int(pin_code)
    
    # Major Indian cities and regions by PIN code
    pin_regions = {
        (110000, 119999): (28.6139, 77.2090),  # Delhi
        (400000, 419999): (19.0760, 72.8777),  # Mumbai
        (560000, 579999): (12.9716, 77.5946),  # Bangalore
        (600000, 619999): (13.0827, 80.2707),  # Chennai
        (700000, 719999): (22.5726, 88.3639),  # Kolkata
        (500000, 519999): (17.3850, 78.4867),  # Hyderabad
        (411000, 419999): (18.5204, 73.8567),  # Pune
        (380000, 389999): (23.0225, 72.5714),  # Ahmedabad
        (302000, 309999): (26.9124, 75.7873),  # Jaipur
        (201000, 209999): (28.5355, 77.3910),  # Noida/Ghaziabad
        (462000, 479999): (23.2599, 77.4126),  # Bhopal
        (751000, 759999): (20.2961, 85.8245),  # Bhubaneswar
        (641000, 649999): (11.0168, 76.9558),  # Coimbatore
        (273000, 284999): (26.8467, 80.9462),  # Lucknow
        (484000, 499999): (23.1815, 79.9864),  # Jabalpur
        (422000, 425999): (19.9975, 73.7898),  # Nashik
        (390000, 396999): (22.3072, 73.1812),  # Vadodara
        (605000, 614999): (11.9416, 79.8083),  # Pondicherry
        (520000, 535999): (16.2160, 80.0406),  # Vijayawada
        (682000, 695999): (9.9312, 76.2673),   # Kochi
    }
    
    for (start, end), coords in pin_regions.items():
        if start <= pin_int <= end:
            return coords
    
    # Extended mapping for more PIN codes
    first_digit = pin_int // 100000
    region_centers = {
        1: (28.6139, 77.2090),  # Delhi region
        2: (28.5355, 77.3910),  # UP East
        3: (26.9124, 75.7873),  # Rajasthan
        4: (19.0760, 72.8777),  # Maharashtra/Mumbai
        5: (17.3850, 78.4867),  # Andhra Pradesh/Telangana
        6: (13.0827, 80.2707),  # Tamil Nadu
        7: (22.5726, 88.3639),  # West Bengal
        8: (22.5726, 88.3639),  # Eastern states
        9: (19.0760, 72.8777),  # Western states
    }
    
    return region_centers.get(first_digit, (20.5937, 78.9629))  # Center of India as final fallback

def validate_pin_code(pin_code):
    """
    Validate Indian PIN code format
    """
    if not pin_code:
        return False
    
    # Remove any spaces or special characters
    pin_code = re.sub(r'[^0-9]', '', pin_code)
    
    # Check if it's exactly 6 digits
    if len(pin_code) != 6 or not pin_code.isdigit():
        return False
    
    return True

def get_location_name(lat, lon):
    """
    Reverse geocoding to get location name from coordinates
    Uses custom implementation with proper headers to avoid 403 errors
    """
    try:
        # First try to get a descriptive name based on known coordinates
        known_locations = {
            (28.6139, 77.2090): "Delhi, India",
            (19.0760, 72.8777): "Mumbai, Maharashtra, India",
            (12.9716, 77.5946): "Bangalore, Karnataka, India",
            (13.0827, 80.2707): "Chennai, Tamil Nadu, India",
            (22.5726, 88.3639): "Kolkata, West Bengal, India",
            (17.3850, 78.4867): "Hyderabad, Telangana, India",
            (18.5204, 73.8567): "Pune, Maharashtra, India",
            (23.0225, 72.5714): "Ahmedabad, Gujarat, India",
            (26.9124, 75.7873): "Jaipur, Rajasthan, India",
            (28.5355, 77.3910): "Noida, Uttar Pradesh, India",
        }
        
        # Check if coordinates match any known location (with tolerance)
        for known_coord, location_name in known_locations.items():
            if abs(lat - known_coord[0]) < 0.1 and abs(lon - known_coord[1]) < 0.1:
                return location_name
        
        # Use custom reverse geocoding with proper headers
        return reverse_geocode_with_headers(lat, lon)
        
    except Exception as e:
        print(f"Error in get_location_name: {e}")
        return f"Location ({lat:.2f}, {lon:.2f}), India"

def reverse_geocode_with_headers(lat, lon):
    """
    Custom reverse geocoding function with proper headers to avoid 403 errors
    """
    import requests
    import time
    
    try:
        # Add delay to respect rate limits
        time.sleep(1)
        
        # Nominatim API endpoint
        url = "https://nominatim.openstreetmap.org/reverse"
        
        # Proper headers required by Nominatim
        headers = {
            'User-Agent': 'CropRecommendationBot/1.0 (educational-project)',
            'Accept': 'application/json',
            'Accept-Language': 'en'
        }
        
        # Parameters for reverse geocoding
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 10
        }
        
        # Make the request with proper headers
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'display_name' in data:
                return data['display_name']
        
        # If API fails, return approximate location based on Indian geography
        return get_approximate_location_name(lat, lon)
        
    except Exception as e:
        print(f"Reverse geocoding failed: {e}")
        return get_approximate_location_name(lat, lon)

def get_approximate_location_name(lat, lon):
    """
    Generate approximate location name based on Indian geography
    """
    # Define major regions of India
    if lat >= 30:
        region = "Northern India"
    elif lat >= 24:
        if lon >= 75:
            region = "North Central India"
        else:
            region = "Northwestern India"
    elif lat >= 20:
        if lon >= 80:
            region = "Eastern India"
        elif lon >= 75:
            region = "Central India"
        else:
            region = "Western India"
    elif lat >= 15:
        if lon >= 77:
            region = "South Central India"
        else:
            region = "Western Peninsular India"
    elif lat >= 10:
        if lon >= 77:
            region = "Southern India"
        else:
            region = "Southwestern India"
    else:
        region = "Far Southern India"
    
    return f"{region} ({lat:.2f}, {lon:.2f})"