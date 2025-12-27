"""Overpass API service for finding nearby healthcare facilities."""

import asyncio
from math import atan2, cos, radians, sin, sqrt
from typing import Optional

import httpx

# Multiple Overpass API endpoints for redundancy
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

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


def build_query(
    lat: float, lon: float, radius: int = 5000, amenities: list[str] | None = None
) -> str:
    """
    Build Overpass QL query to find healthcare facilities.

    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default 5km)
        amenities: List of amenity types to search for

    Returns:
        Overpass QL query string
    """
    if amenities is None:
        amenities = HEALTHCARE_AMENITIES

    amenity_queries = []
    for amenity in amenities:
        amenity_queries.append(
            f'nwr["amenity"="{amenity}"](around:{radius},{lat},{lon});'
        )

    return f"""
    [out:json][timeout:25];
    (
      {chr(10).join(amenity_queries)}
    );
    out body center;
    """


async def query_overpass_with_retry(query: str, max_retries: int = 3) -> Optional[dict]:
    """
    Query Overpass API with retry logic across multiple endpoints.

    Args:
        query: Overpass QL query string
        max_retries: Maximum number of retry attempts

    Returns:
        JSON response data or None if all attempts fail
    """
    for attempt in range(max_retries):
        # Rotate through endpoints
        endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    endpoint,
                    data={"data": query},
                    headers={
                        "User-Agent": "CareCompass/1.0",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            print(f"Overpass API timeout on {endpoint} (attempt {attempt + 1})")
        except httpx.HTTPStatusError as e:
            print(
                f"Overpass API HTTP error {e.response.status_code} on {endpoint} (attempt {attempt + 1})"
            )
            # For 504 Gateway Timeout or 429 Too Many Requests, try another endpoint
            if e.response.status_code in (504, 429, 503):
                await asyncio.sleep(1)  # Brief delay before retry
                continue
        except Exception as e:
            print(f"Overpass API error on {endpoint}: {e} (attempt {attempt + 1})")

        # Brief delay before retry
        if attempt < max_retries - 1:
            await asyncio.sleep(0.5)

    return None


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
    # Build optimized query with only requested amenities
    query = build_query(lat, lon, radius, amenity_filter)

    # Query with retry logic
    data = await query_overpass_with_retry(query)

    if data is None:
        return []

    # Parse results
    places = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        amenity = tags.get("amenity", "unknown")

        # Apply filter if specified (should already be filtered by query, but double-check)
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
