"""
COPERT IV Speed-Dependent Emission Calculator.

EF(v) in g CO₂/km:
    fuel_consumption(v) = 0.0667 + 0.0556/v + 0.000472·v²  [L/km]
    EF(v) = 2310 × fuel_consumption(v)  [g CO₂/km]

Per-ride total emissions:
    CO₂_ride = Σ_segments [length_km(s) × EF(v_avg(s))]

Carpool savings:
    CO₂_saved = Σᵢ (dᵢ × EF(vᵢ)) − d_shared × EF(v_shared)
    percentage_saved = CO₂_saved / Σᵢ (dᵢ × EF(vᵢ)) × 100
"""

from typing import List, Dict, Any, Union
from config import emission_config


def fuel_consumption(speed_kmh: float) -> float:
    """fuel_consumption(v) = 0.0667 + 0.0556/v + 0.000472·v²  [L/km]"""
    v = max(speed_kmh, 5.0)
    fc = emission_config.fuel_a + emission_config.fuel_b / v + emission_config.fuel_c * v ** 2
    return max(fc, 0.01)


def emission_factor(speed_kmh: float) -> float:
    """EF(v) = 2310 × fuel_consumption(v)  [g CO₂/km]"""
    fc = fuel_consumption(speed_kmh)
    return emission_config.co2_per_liter * fc


def emission_factor_by_fuel_type(speed_kmh: float, fuel_type: str = "petrol") -> float:
    """Emission factor adjusted for fuel type."""
    if fuel_type == "electric":
        return 0.0
    base_ef = emission_factor(speed_kmh)
    fuel_multipliers = {
        "petrol": 1.0,
        "diesel": 1.16,   # 2680/2310
        "hybrid": 0.5,
        "cng": 0.75,
        "electric": 0.0,
    }
    return base_ef * fuel_multipliers.get(fuel_type, 1.0)


def calculate_ride_emissions(
    distance_or_segments,
    duration_min: float = 30.0,
    fuel_type: str = "petrol",
) -> Dict[str, Any]:
    """Calculate total CO₂ emissions for a ride.
    
    Accepts either:
      - (distance_km: float, duration_min: float, fuel_type: str)
      - (segments: List[Dict], fuel_type: str)  — legacy list-of-segments style
    """
    if isinstance(distance_or_segments, list):
        # Legacy: list of segments
        total_co2 = 0.0
        total_dist = 0.0
        for seg in distance_or_segments:
            d = seg.get("distanceKm", 0.0)
            v = seg.get("avgSpeedKmh", 30.0)
            ef = emission_factor_by_fuel_type(v, fuel_type)
            total_co2 += d * ef
            total_dist += d
        return {
            "co2_grams": round(total_co2, 1),
            "distance_km": round(total_dist, 2),
            "fuel_type": fuel_type,
        }
    else:
        # Simple: distance_km + duration_min
        distance_km = float(distance_or_segments)
        avg_speed = (distance_km / (duration_min / 60.0)) if duration_min > 0 else 30.0
        avg_speed = max(min(avg_speed, 120.0), 5.0)
        ef = emission_factor_by_fuel_type(avg_speed, fuel_type)
        co2 = distance_km * ef
        return {
            "co2_grams": round(co2, 1),
            "distance_km": round(distance_km, 2),
            "avg_speed_kmh": round(avg_speed, 1),
            "fuel_type": fuel_type,
            "emission_factor": round(ef, 2),
        }


def calculate_carpool_savings(
    distance_or_trips,
    num_passengers_or_shared = None,
    avg_speed_kmh: float = 30.0,
    fuel_type: str = "petrol",
) -> Dict[str, float]:
    """Calculate CO₂ savings from carpooling vs solo driving.
    
    Accepts either:
      - (distance_km: float, num_passengers: int, avg_speed: float, fuel_type: str)
      - (individual_trips: List[Dict], shared_trip: Dict, fuel_type: str)  — legacy
    """
    if isinstance(distance_or_trips, list):
        # Legacy list-of-trips style
        individual_trips = distance_or_trips
        shared_trip = num_passengers_or_shared or {}
        individual_total = 0.0
        for trip in individual_trips:
            d = trip.get("distanceKm", 0.0)
            v = trip.get("avgSpeedKmh", 30.0)
            ef = emission_factor_by_fuel_type(v, fuel_type)
            individual_total += d * ef

        shared_d = shared_trip.get("distanceKm", 0.0)
        shared_v = shared_trip.get("avgSpeedKmh", 30.0)
        shared_ef = emission_factor_by_fuel_type(shared_v, fuel_type)
        shared_total = shared_d * shared_ef

        co2_saved = individual_total - shared_total
        percentage_saved = (co2_saved / individual_total * 100) if individual_total > 0 else 0.0

        return {
            "co2_saved_g": max(co2_saved, 0.0),
            "percentage_saved": max(percentage_saved, 0.0),
            "individual_total_g": individual_total,
            "shared_total_g": shared_total,
        }
    else:
        # Simple: distance_km + num_passengers
        distance_km = float(distance_or_trips)
        num_passengers = int(num_passengers_or_shared or 1)
        ef = emission_factor_by_fuel_type(avg_speed_kmh, fuel_type)
        solo_co2 = distance_km * ef * num_passengers
        shared_co2 = distance_km * ef
        co2_saved = solo_co2 - shared_co2
        percentage_saved = (co2_saved / solo_co2 * 100) if solo_co2 > 0 else 0.0

        return {
            "co2_saved_g": round(max(co2_saved, 0.0), 1),
            "percentage_saved": round(max(percentage_saved, 0.0), 1),
            "individual_total_g": round(solo_co2, 1),
            "shared_total_g": round(shared_co2, 1),
            "num_passengers": num_passengers,
        }


def co2_to_tree_days(co2_grams: float) -> float:
    """Convert CO₂ saved to equivalent tree-days (tree absorbs ~60.3 g/day)."""
    tree_absorption_per_day_g = 22000.0 / 365.0
    return co2_grams / tree_absorption_per_day_g
