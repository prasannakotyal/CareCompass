import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic


def get_nearby_places(location, place_type):
    geolocator = Nominatim(user_agent="nearby_search")
    
    try:
        location_info = geolocator.geocode(location)
        if location_info:
            user_coords = (location_info.latitude, location_info.longitude)
            
            query = f"{place_type} near {location}"
            places = geolocator.geocode(query, exactly_one=False, limit=None, timeout=10)
            
            if places:
                st.subheader(f"Nearby {place_type}s:")
                for place in places:
                    place_coords = (place.latitude, place.longitude)
                    place_distance = geodesic(user_coords, place_coords).kilometers
                    st.write(f" - {place.address} ({place_distance:.2f} km)")
                st.write("\n")
            else:
                st.write(f"No nearby {place_type} found.\n")
        else:
            st.write("Invalid location. Please try again.")
    except Exception as e:
        st.write(f"Error: {e}")


def nearby_places_app():
    st.title("Nearby Places Suggestion")

    # User input for location and place type
    location = st.text_input("Enter your location (e.g., city name, address):")
    place_type = st.selectbox("Select the type of place:", ["hospitals","malls", "pharmacy", "police stations", "restaurants"])

    # Button to trigger the nearby places suggestion
    if st.button("Get Nearby Places"):
        get_nearby_places(location, place_type)
