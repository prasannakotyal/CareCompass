"""Overpass API service for finding nearby healthcare facilities."""

from typing import Optional
from math import radians, sin, cos, sqrt, atan2

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Healthcare amenity types to search for
HEALTHCARE_AMENITIES = ["hospital", "pharmacy", "clinic", "doctors", "dentist"]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using Haversine formula.

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def build_query(lat: float, lon: float, radius: int = 5000) -> str:
    """
    Build Overpass QL query to find healthcare facilities.

    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default 5km)

    Returns:
        Overpass QL query string
    """
    amenity_queries = []
    for amenity in HEALTHCARE_AMENITIES:
        amenity_queries.append(
            f'nwr["amenity"="{amenity}"](around:{radius},{lat},{lon});'
        )

    return f"""
    [out:json][timeout:30];
    (
      {chr(10).join(amenity_queries)}
    );
    out body center;
    """


async def find_nearby_healthcare(
    lat: float,
    lon: float,
    radius: int = 5000,
    amenity_filter: Optional[list[str]] = None,
) -> list[dict]:
    """
    Find nearby healthcare facilities using Overpass API.

    Args:
        lat: User's latitude
        lon: User's longitude
        radius: Search radius in meters (default 5km)
        amenity_filter: Optional list of specific amenity types to include

    Returns:
        List of places with name, type, distance, address, etc.
    """
    query = build_query(lat, lon, radius)

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.get(
                OVERPASS_URL,
                params={"data": query},
                headers={"User-Agent": "CareCompass/1.0"},
            )
            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException:
        print("Overpass API timeout")
        return []
    except httpx.HTTPStatusError as e:
        print(f"Overpass API HTTP error: {e.response.status_code}")
        return []
    except Exception as e:
        print(f"Overpass API error: {e}")
        return []

    # Parse results
    places = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        amenity = tags.get("amenity", "unknown")

        # Apply filter if specified
        if amenity_filter and amenity not in amenity_filter:
            continue

        # Get coordinates
        if element["type"] == "node":
            place_lat = element.get("lat")
            place_lon = element.get("lon")
        else:
            center = element.get("center", {})
            place_lat = center.get("lat")
            place_lon = center.get("lon")

        if not place_lat or not place_lon:
            continue

        # Calculate distance
        distance = haversine_distance(lat, lon, place_lat, place_lon)

        # Build address string
        address_parts = []
        if tags.get("addr:housenumber"):
            address_parts.append(tags["addr:housenumber"])
        if tags.get("addr:street"):
            address_parts.append(tags["addr:street"])
        if tags.get("addr:city"):
            address_parts.append(tags["addr:city"])
        if tags.get("addr:postcode"):
            address_parts.append(tags["addr:postcode"])

        place = {
            "id": element.get("id"),
            "name": tags.get("name", "Unknown"),
            "type": amenity,
            "distance_km": round(distance, 2),
            "address": ", ".join(address_parts) if address_parts else None,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "website": tags.get("website") or tags.get("contact:website"),
            "opening_hours": tags.get("opening_hours"),
            "emergency": tags.get("emergency") == "yes",
            "lat": place_lat,
            "lon": place_lon,
        }
        places.append(place)

    # Sort by distance
    places.sort(key=lambda x: x["distance_km"])

    return places


def get_amenity_types() -> list[dict]:
    """Get list of searchable amenity types with display names."""
    return [
        {"value": "hospital", "label": "Hospitals"},
        {"value": "pharmacy", "label": "Pharmacies"},
        {"value": "clinic", "label": "Clinics"},
        {"value": "doctors", "label": "Doctor's Offices"},
        {"value": "dentist", "label": "Dentists"},
    ]
