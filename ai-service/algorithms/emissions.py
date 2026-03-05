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

from typing import List, Dict, Any
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
    segments: List[Dict[str, float]],
    fuel_type: str = "petrol",
) -> float:
    """Calculate total CO₂ emissions for a ride."""
    total_co2 = 0.0
    for seg in segments:
        distance_km = seg.get("distanceKm", 0.0)
        avg_speed = seg.get("avgSpeedKmh", 30.0)
        ef = emission_factor_by_fuel_type(avg_speed, fuel_type)
        total_co2 += distance_km * ef
    return total_co2


def calculate_carpool_savings(
    individual_trips: List[Dict[str, float]],
    shared_trip: Dict[str, float],
    fuel_type: str = "petrol",
) -> Dict[str, float]:
    """Calculate CO₂ savings from carpooling vs solo driving."""
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


def co2_to_tree_days(co2_grams: float) -> float:
    """Convert CO₂ saved to equivalent tree-days (tree absorbs ~60.3 g/day)."""
    tree_absorption_per_day_g = 22000.0 / 365.0
    return co2_grams / tree_absorption_per_day_g
