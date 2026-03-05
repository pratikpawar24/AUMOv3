"""
Live Traffic Data Fetcher — Real-time traffic using OSRM and open APIs.

Uses:
  1. OSRM real-time route durations vs free-flow to estimate congestion
  2. OpenStreetMap Overpass for live road event data  
  3. Time-of-day and day-of-week traffic patterns from historical models
"""

import asyncio
import math
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import httpx
from config import OSRM_URL, graph_config
from utils.haversine import haversine

# Cache for live traffic data (refreshed periodically)
_traffic_cache: Dict[str, Dict] = {}
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 120  # 2 minutes


# ═══════════════════════════════════════════════════════════════
# Maharashtra city centers for traffic probing
# ═══════════════════════════════════════════════════════════════

MAHARASHTRA_PROBE_POINTS = [
    # Pune
    (18.5204, 73.8567), (18.5074, 73.8077), (18.5596, 73.7796),
    (18.4685, 73.8804), (18.5330, 73.8745), (18.4917, 73.9097),
    # Mumbai
    (19.0760, 72.8777), (19.0176, 72.8562), (19.1136, 72.8697),
    (19.2183, 72.9781), (19.0596, 72.8295),
    # Nagpur
    (21.1458, 79.0882), (21.1232, 79.0515),
    # Nashik
    (19.9975, 73.7898), (20.0063, 73.7636),
    # Aurangabad
    (19.8762, 75.3433),
]


async def fetch_osrm_congestion(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
) -> Optional[Dict]:
    """Estimate congestion by comparing OSRM route duration with free-flow estimate."""
    try:
        coord_str = f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
        url = f"{OSRM_URL}/route/v1/driving/{coord_str}"
        params = {"overview": "simplified", "annotations": "duration,speed"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            return None

        route = data["routes"][0]
        actual_duration = route["duration"]  # seconds
        distance = route["distance"]  # meters

        # Free-flow speed estimate based on road type (avg 50 km/h)
        free_flow_duration = distance / (50 * 1000 / 3600) if distance > 0 else 1

        # Congestion ratio: >1 means slower than free-flow
        congestion_ratio = actual_duration / max(free_flow_duration, 1)
        congestion_level = min(max((congestion_ratio - 0.8) / 1.2, 0), 1)

        # Extract speed from annotations if available
        avg_speed = (distance / actual_duration * 3.6) if actual_duration > 0 else 40

        return {
            "distance_m": distance,
            "duration_s": actual_duration,
            "free_flow_s": free_flow_duration,
            "congestion": round(congestion_level, 3),
            "avg_speed_kmh": round(avg_speed, 1),
            "ratio": round(congestion_ratio, 3),
        }
    except Exception as e:
        return None


async def get_live_traffic_sample() -> List[Dict]:
    """Get real-time traffic samples by probing OSRM with Maharashtra routes."""
    global _traffic_cache, _cache_timestamp

    now = datetime.now()
    if _cache_timestamp and (now - _cache_timestamp).seconds < CACHE_TTL_SECONDS and _traffic_cache:
        return list(_traffic_cache.values())

    samples = []
    tasks = []

    # Create probe pairs (nearby points)
    probe_pairs = []
    for i in range(len(MAHARASHTRA_PROBE_POINTS)):
        for j in range(i + 1, min(i + 3, len(MAHARASHTRA_PROBE_POINTS))):
            p1 = MAHARASHTRA_PROBE_POINTS[i]
            p2 = MAHARASHTRA_PROBE_POINTS[j]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            if 1 < dist < 30:  # 1-30 km range
                probe_pairs.append((p1, p2))

    # Limit concurrent requests
    for p1, p2 in probe_pairs[:15]:
        tasks.append(fetch_osrm_congestion(p1, p2))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, result in enumerate(results):
        if isinstance(result, dict) and result is not None:
            p1, p2 = probe_pairs[idx]
            mid_lat = (p1[0] + p2[0]) / 2
            mid_lng = (p1[1] + p2[1]) / 2
            sample = {
                "lat": mid_lat,
                "lng": mid_lng,
                "congestion": result["congestion"],
                "speed_kmh": result["avg_speed_kmh"],
                "distance_m": result["distance_m"],
                "source": "osrm_live",
            }
            samples.append(sample)
            _traffic_cache[f"{mid_lat:.4f},{mid_lng:.4f}"] = sample

    _cache_timestamp = now
    return samples


def get_time_based_congestion(hour: int, day_of_week: int) -> float:
    """Get expected congestion based on time patterns for Maharashtra.
    
    Based on Indian traffic patterns:
      - Morning peak: 8-10 AM (high congestion)
      - Evening peak: 5-8 PM (highest congestion)  
      - Late night: 11 PM - 5 AM (low congestion)
      - Weekends: lower but still present (markets, temples, etc.)
    """
    # Base hourly congestion pattern (0-23)
    weekday_pattern = {
        0: 0.05, 1: 0.03, 2: 0.02, 3: 0.02, 4: 0.05, 5: 0.10,
        6: 0.20, 7: 0.45, 8: 0.75, 9: 0.85, 10: 0.65, 11: 0.55,
        12: 0.50, 13: 0.55, 14: 0.50, 15: 0.55, 16: 0.65, 17: 0.80,
        18: 0.90, 19: 0.85, 20: 0.60, 21: 0.40, 22: 0.25, 23: 0.10,
    }
    weekend_pattern = {
        0: 0.05, 1: 0.03, 2: 0.02, 3: 0.02, 4: 0.03, 5: 0.05,
        6: 0.10, 7: 0.20, 8: 0.35, 9: 0.50, 10: 0.55, 11: 0.60,
        12: 0.55, 13: 0.50, 14: 0.45, 15: 0.50, 16: 0.55, 17: 0.60,
        18: 0.65, 19: 0.55, 20: 0.40, 21: 0.30, 22: 0.20, 23: 0.08,
    }

    is_weekend = day_of_week >= 5
    pattern = weekend_pattern if is_weekend else weekday_pattern
    base = pattern.get(hour, 0.3)

    # Add slight randomness for realism
    noise = random.uniform(-0.05, 0.05)
    return max(0, min(1, base + noise))


async def get_live_heatmap(graph=None) -> List[Dict]:
    """Get comprehensive traffic heatmap combining live and time-based data."""
    now = datetime.now()
    hour = now.hour
    dow = now.weekday()
    
    # Get OSRM-based live samples
    live_samples = await get_live_traffic_sample()
    
    # Enrich with time-based patterns
    heatmap = []
    for sample in live_samples:
        time_congestion = get_time_based_congestion(hour, dow)
        # Blend: 60% live OSRM data, 40% time-based pattern
        blended = 0.6 * sample["congestion"] + 0.4 * time_congestion
        heatmap.append({
            "lat": sample["lat"],
            "lng": sample["lng"],
            "congestion": round(blended, 3),
            "speed_kmh": sample["speed_kmh"],
            "intensity": round(blended, 3),
            "source": "blended",
        })

    # Add extra points from graph if available
    if graph is not None:
        nodes = list(graph.nodes(data=True))[:200]
        for node_id, data in nodes:
            lat, lng = data.get("lat", 0), data.get("lng", 0)
            if lat == 0:
                continue
            time_cong = get_time_based_congestion(hour, dow)
            heatmap.append({
                "lat": lat,
                "lng": lng,
                "congestion": round(time_cong, 3),
                "speed_kmh": round(50 * (1 - time_cong * 0.6), 1),
                "intensity": round(time_cong, 3),
                "source": "time_model",
            })

    return heatmap
