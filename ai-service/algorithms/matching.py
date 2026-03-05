"""
Carpool Matching Algorithm — DBSCAN + Multi-Factor Scoring

Architecture:
  1. Spatial Clustering (DBSCAN):
     - Cluster ride offers by pickup proximity
     - ε = 2 km, MinPts = 2
     - Uses haversine distance metric

  2. Multi-Factor Compatibility Score:
     S = 0.35·RouteOverlap + 0.25·TimeCompat + 0.15·PrefMatch + 0.25·Proximity
     
     RouteOverlap: How much the detour adds to the driver's route
     TimeCompat: How close the departure times are  
     PrefMatch: Smoking, music, gender preferences
     Proximity: How close pickup/dropoff points are

  3. Carpool CO₂ Savings:
     Savings = (N-1)/N × single_trip_emissions
     where N = number of passengers sharing the ride
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import DBSCAN

from utils.haversine import haversine_km
from algorithms.emissions import calculate_ride_emissions, calculate_carpool_savings
from config import matching_config


@dataclass
class RideOffer:
    """A ride offer from a driver."""
    id: str
    driver_id: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: datetime
    seats_available: int
    route_distance_km: float
    route_duration_min: float
    preferences: Dict[str, Any]  # smoking, music, gender, etc.
    polyline: Optional[List[List[float]]] = None


@dataclass
class RideRequest:
    """A ride request from a passenger."""
    id: str
    passenger_id: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: datetime
    preferences: Dict[str, Any]


@dataclass
class MatchResult:
    """Result of matching a request to an offer."""
    offer_id: str
    request_id: str
    score: float
    route_overlap: float
    time_compatibility: float
    preference_match: float
    proximity_score: float
    pickup_detour_km: float
    dropoff_detour_km: float
    co2_savings_g: float
    estimated_fare: float


# ═══════════════════════════════════════════════════════════════
# STEP 1: Spatial Clustering
# ═══════════════════════════════════════════════════════════════

def cluster_rides(
    offers: List[RideOffer],
    eps_km: float = None,
    min_samples: int = None,
) -> Dict[int, List[RideOffer]]:
    """Cluster ride offers using DBSCAN on pickup locations.
    
    Uses haversine distance in km for DBSCAN metric.
    """
    if eps_km is None:
        eps_km = matching_config.dbscan_eps_km
    if min_samples is None:
        min_samples = matching_config.dbscan_min_samples

    if not offers:
        return {}

    # Extract coordinates
    coords = np.array([[o.origin_lat, o.origin_lng] for o in offers])
    
    # Convert eps from km to radians for haversine metric
    eps_rad = eps_km / 6371.0  # Earth radius in km

    db = DBSCAN(
        eps=eps_rad,
        min_samples=min_samples,
        metric="haversine",
        algorithm="ball_tree",
    )
    
    # DBSCAN expects radians
    coords_rad = np.radians(coords)
    labels = db.fit_predict(coords_rad)

    clusters: Dict[int, List[RideOffer]] = {}
    for i, label in enumerate(labels):
        if label == -1:
            # Noise points get their own "cluster" for individual matching
            clusters[-(i + 1)] = [offers[i]]
        else:
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(offers[i])

    return clusters


# ═══════════════════════════════════════════════════════════════
# STEP 2: Compatibility Scoring
# ═══════════════════════════════════════════════════════════════

def calculate_route_overlap(
    offer: RideOffer, request: RideRequest,
) -> Tuple[float, float, float]:
    """Calculate how well the request fits into the offer's route.
    
    Returns: (overlap_score, pickup_detour_km, dropoff_detour_km)
    
    overlap_score in [0, 1]:
      1.0 = no detour needed
      0.0 = detour exceeds maximum allowed
    """
    max_detour = matching_config.max_detour_km

    # Distance from offer origin to request pickup
    pickup_detour = haversine_km(
        offer.origin_lat, offer.origin_lng,
        request.origin_lat, request.origin_lng,
    )

    # Distance from offer dest to request dropoff
    dropoff_detour = haversine_km(
        offer.dest_lat, offer.dest_lng,
        request.dest_lat, request.dest_lng,
    )

    # Total detour ratio
    total_detour = pickup_detour + dropoff_detour
    if offer.route_distance_km <= 0:
        return 0.0, pickup_detour, dropoff_detour

    detour_ratio = total_detour / offer.route_distance_km

    # Score: 1.0 if no detour, decreasing as detour increases
    if total_detour > max_detour:
        overlap = 0.0
    else:
        overlap = max(0.0, 1.0 - detour_ratio)

    return overlap, pickup_detour, dropoff_detour


def calculate_time_compatibility(
    offer: RideOffer, request: RideRequest,
) -> float:
    """Calculate time compatibility score.
    
    Returns score in [0, 1]:
      1.0 = exact same departure time
      0.0 = departure times differ by > max_time_diff
    """
    max_diff = matching_config.max_time_diff_minutes
    
    diff_minutes = abs((offer.departure_time - request.departure_time).total_seconds()) / 60.0
    
    if diff_minutes > max_diff:
        return 0.0

    return 1.0 - (diff_minutes / max_diff)


def calculate_preference_match(
    offer: RideOffer, request: RideRequest,
) -> float:
    """Calculate preference compatibility.
    
    Checks: smoking, music, gender_preference, pet_friendly, quiet_ride
    Each matching preference adds to score.
    """
    pref_keys = ["smoking", "music", "gender_preference", "pet_friendly", "quiet_ride"]
    
    o_prefs = offer.preferences or {}
    r_prefs = request.preferences or {}
    
    total_prefs = 0
    matched = 0
    
    for key in pref_keys:
        if key in r_prefs:
            total_prefs += 1
            o_val = o_prefs.get(key)
            r_val = r_prefs.get(key)
            
            if o_val is not None and r_val is not None:
                if key == "gender_preference":
                    if r_val == "any" or o_val == r_val:
                        matched += 1
                elif o_val == r_val:
                    matched += 1
            elif o_val is None:
                # If driver hasn't set preference, consider it flexible
                matched += 0.5
    
    if total_prefs == 0:
        return 1.0  # No preferences = fully compatible

    return matched / total_prefs


def calculate_proximity_score(
    offer: RideOffer, request: RideRequest,
) -> float:
    """Calculate proximity score based on pickup and dropoff distances.
    
    Returns score in [0, 1]:
      1.0 = very close (<0.5 km)
      0.0 = too far (>max_walk_km)
    """
    max_walk = matching_config.max_walk_km

    pickup_dist = haversine_km(
        offer.origin_lat, offer.origin_lng,
        request.origin_lat, request.origin_lng,
    )
    dropoff_dist = haversine_km(
        offer.dest_lat, offer.dest_lng,
        request.dest_lat, request.dest_lng,
    )

    avg_dist = (pickup_dist + dropoff_dist) / 2.0

    if avg_dist > max_walk:
        return 0.0

    return max(0.0, 1.0 - (avg_dist / max_walk))


def compute_match_score(
    offer: RideOffer, request: RideRequest,
) -> Optional[MatchResult]:
    """Compute the full multi-factor match score.
    
    S = w₁·RouteOverlap + w₂·TimeCompat + w₃·PrefMatch + w₄·Proximity
    """
    w = matching_config.score_weights

    route_overlap, pickup_detour, dropoff_detour = calculate_route_overlap(offer, request)
    time_compat = calculate_time_compatibility(offer, request)
    pref_match = calculate_preference_match(offer, request)
    proximity = calculate_proximity_score(offer, request)

    # All components must meet minimum threshold
    if route_overlap == 0 and time_compat == 0:
        return None

    score = (
        w.route_overlap * route_overlap +
        w.time_compatibility * time_compat +
        w.preference_match * pref_match +
        w.proximity * proximity
    )

    if score < matching_config.min_match_score:
        return None

    # Calculate CO₂ savings
    request_distance_km = haversine_km(
        request.origin_lat, request.origin_lng,
        request.dest_lat, request.dest_lng,
    )
    savings = calculate_carpool_savings(request_distance_km, num_passengers=2)

    # Estimate fare (simple distance-based)
    base_fare = 30.0  # INR
    per_km = 12.0  # INR/km
    estimated_fare = base_fare + per_km * request_distance_km

    return MatchResult(
        offer_id=offer.id,
        request_id=request.id,
        score=round(score, 4),
        route_overlap=round(route_overlap, 4),
        time_compatibility=round(time_compat, 4),
        preference_match=round(pref_match, 4),
        proximity_score=round(proximity, 4),
        pickup_detour_km=round(pickup_detour, 2),
        dropoff_detour_km=round(dropoff_detour, 2),
        co2_savings_g=round(savings["total_saved_g"], 1),
        estimated_fare=round(estimated_fare, 2),
    )


# ═══════════════════════════════════════════════════════════════
# STEP 3: Full Matching Pipeline
# ═══════════════════════════════════════════════════════════════

def find_matches(
    request: RideRequest,
    offers: List[RideOffer],
    top_k: int = 10,
) -> List[MatchResult]:
    """Find the best matching ride offers for a request.
    
    Pipeline:
      1. Filter offers by time window
      2. Cluster remaining offers by location
      3. Score each offer against request
      4. Return top-k matches sorted by score
    """
    # Step 1: Time filter (within max_time_diff of request)
    max_diff = timedelta(minutes=matching_config.max_time_diff_minutes)
    time_filtered = [
        o for o in offers
        if abs(o.departure_time - request.departure_time) <= max_diff
        and o.seats_available > 0
    ]

    if not time_filtered:
        return []

    # Step 2: Score all remaining offers
    matches: List[MatchResult] = []
    for offer in time_filtered:
        result = compute_match_score(offer, request)
        if result is not None:
            matches.append(result)

    # Step 3: Sort by score descending
    matches.sort(key=lambda m: m.score, reverse=True)

    return matches[:top_k]


def batch_match(
    requests: List[RideRequest],
    offers: List[RideOffer],
    top_k: int = 5,
) -> Dict[str, List[MatchResult]]:
    """Batch match multiple requests against all offers.
    
    Returns: {request_id: [MatchResult, ...]}
    """
    results: Dict[str, List[MatchResult]] = {}

    # Pre-cluster offers for efficiency
    clusters = cluster_rides(offers)

    for request in requests:
        matches = find_matches(request, offers, top_k=top_k)
        results[request.id] = matches

    return results
