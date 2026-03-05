"""OSRM HTTP client for routing."""

import httpx
from typing import List, Tuple, Optional, Dict, Any
from config import OSRM_URL

MAX_RETRIES = 2
TIMEOUT_SECONDS = 45.0


async def get_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    waypoints: Optional[List[Tuple[float, float]]] = None,
    alternatives: bool = True,
) -> Dict[str, Any]:
    """Get route from OSRM."""
    points = [origin]
    if waypoints:
        points.extend(waypoints)
    points.append(destination)

    coord_str = ";".join(f"{lng},{lat}" for lat, lng in points)
    url = f"{OSRM_URL}/route/v1/driving/{coord_str}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "alternatives": "true" if alternatives else "false",
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("code") == "Ok":
                    return data
                return {"routes": [], "code": data.get("code", "Error")}
        except Exception as e:
            if attempt == MAX_RETRIES:
                print(f"[OSRM] Route failed after {MAX_RETRIES + 1} attempts: {e}")
                return {"routes": [], "code": "Error"}
            print(f"[OSRM] Retry {attempt + 1}: {e}")

    return {"routes": [], "code": "Error"}


async def get_distance_matrix(
    origins: List[Tuple[float, float]],
    destinations: List[Tuple[float, float]],
) -> Dict[str, Any]:
    """Get distance/duration matrix from OSRM table service."""
    all_coords = origins + destinations
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in all_coords)
    sources = ";".join(str(i) for i in range(len(origins)))
    destinations_idx = ";".join(str(i + len(origins)) for i in range(len(destinations)))

    url = f"{OSRM_URL}/table/v1/driving/{coord_str}"
    params = {"sources": sources, "destinations": destinations_idx}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"[OSRM] Table error: {e}")
        return {"code": "Error", "durations": [], "distances": []}


def decode_osrm_geometry(geometry: dict) -> List[Tuple[float, float]]:
    """Convert OSRM GeoJSON geometry to list of (lat, lng) tuples."""
    if geometry.get("type") == "LineString":
        return [(coord[1], coord[0]) for coord in geometry["coordinates"]]
    return []
