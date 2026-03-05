"""
Synthetic Traffic Data Generator for Maharashtra Road Network

Generates realistic traffic patterns based on:
  - Time of day (peak hours, off-peak, night)
  - Day of week (weekday vs weekend)
  - Road type (highway vs arterial vs residential)
  - Maharashtra-specific patterns (festival days, monsoon effects)
  - Random perturbations for variety
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

import numpy as np
import torch

from config import synthetic_config, model_config


def time_features(dt: datetime) -> Dict[str, float]:
    """Extract cyclical time features from datetime."""
    hour = dt.hour + dt.minute / 60.0
    day_of_week = dt.weekday()
    
    return {
        "hour_sin": math.sin(2 * math.pi * hour / 24),
        "hour_cos": math.cos(2 * math.pi * hour / 24),
        "day_sin": math.sin(2 * math.pi * day_of_week / 7),
        "day_cos": math.cos(2 * math.pi * day_of_week / 7),
        "is_weekend": 1.0 if day_of_week >= 5 else 0.0,
        "is_holiday": 0.0,
    }


def road_type_encoding(road_type: str) -> float:
    """Encode road type as numeric feature."""
    mapping = {
        "motorway": 1.0,
        "trunk": 0.85,
        "primary": 0.7,
        "secondary": 0.55,
        "tertiary": 0.4,
        "residential": 0.2,
        "service": 0.1,
        "shortcut": 0.5,
    }
    return mapping.get(road_type, 0.3)


def generate_traffic_pattern(
    hour: float, day_of_week: int, road_type: str, base_speed: float,
) -> Tuple[float, float, float]:
    """Generate realistic traffic (speed, volume, congestion) for a time.
    
    Maharashtra-specific patterns:
      - Morning peak: 7:30-9:30 AM
      - Evening peak: 5:30-8:00 PM
      - Lunch dip: 1:00-2:30 PM
      - Night calm: 11 PM - 5 AM
      - Weekend reduction: ~30% less traffic
    """
    is_weekend = day_of_week >= 5
    
    # Base volume pattern (0-1 scale)
    if 7.5 <= hour < 9.5:  # Morning peak
        volume_factor = 0.85 + 0.1 * math.sin(math.pi * (hour - 7.5) / 2)
    elif 17.5 <= hour < 20:  # Evening peak
        volume_factor = 0.9 + 0.08 * math.sin(math.pi * (hour - 17.5) / 2.5)
    elif 13 <= hour < 14.5:  # Lunch
        volume_factor = 0.55
    elif 9.5 <= hour < 17.5:  # Daytime
        volume_factor = 0.6 + 0.05 * math.sin(math.pi * (hour - 9.5) / 8)
    elif 5 <= hour < 7.5:  # Early morning
        volume_factor = 0.2 + 0.3 * ((hour - 5) / 2.5)
    elif 20 <= hour < 23:  # Evening wind-down
        volume_factor = 0.5 - 0.2 * ((hour - 20) / 3)
    else:  # Night
        volume_factor = 0.1
    
    # Weekend adjustment
    if is_weekend:
        if 10 <= hour < 20:
            volume_factor *= 0.8  # Less commuter traffic
        else:
            volume_factor *= 0.7
    
    # Road type adjustment
    road_multiplier = {
        "motorway": 1.2, "trunk": 1.1, "primary": 1.0,
        "secondary": 0.8, "tertiary": 0.6, "residential": 0.4,
    }
    volume_factor *= road_multiplier.get(road_type, 0.7)
    volume_factor = min(volume_factor, 1.0)
    
    # Speed: inversely related to volume (BPR-like)
    speed_factor = 1.0 - 0.6 * (volume_factor ** 2)
    speed = base_speed * max(speed_factor, 0.2)
    
    # Congestion
    congestion = min(1.0, volume_factor ** 1.3)
    
    # Volume (vehicles/hour)
    capacity = {"motorway": 2200, "trunk": 2000, "primary": 1800,
                "secondary": 1200, "tertiary": 800, "residential": 400}
    cap = capacity.get(road_type, 1000)
    volume = cap * volume_factor
    
    # Add noise
    speed += random.gauss(0, speed * 0.05)
    volume += random.gauss(0, volume * 0.08)
    congestion += random.gauss(0, 0.03)
    
    speed = max(5.0, speed)
    volume = max(0, volume)
    congestion = max(0.0, min(1.0, congestion))
    
    return speed, volume, congestion


def generate_sequence(
    start_time: datetime,
    road_type: str,
    base_speed: float,
    seq_len: int,
    interval_minutes: int = 15,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate a single training sequence.
    
    Returns:
      features: [seq_len, input_dim]
      targets: [output_dim]  (prediction for the next time step)
    """
    features_list = []
    
    for i in range(seq_len + 1):  # +1 for the target
        dt = start_time + timedelta(minutes=i * interval_minutes)
        hour = dt.hour + dt.minute / 60.0
        dow = dt.weekday()
        
        speed, volume, congestion = generate_traffic_pattern(
            hour, dow, road_type, base_speed
        )
        tf = time_features(dt)
        
        feature_vec = [
            speed / 120.0,            # normalized speed
            volume / 2200.0,          # normalized volume
            congestion,               # already 0-1
            tf["hour_sin"],
            tf["hour_cos"],
            tf["day_sin"],
            tf["day_cos"],
            tf["is_weekend"],
            tf["is_holiday"],
            road_type_encoding(road_type),
        ]
        features_list.append(feature_vec)
    
    features = np.array(features_list[:-1], dtype=np.float32)
    
    # Target: actual values for next time step
    last = features_list[-1]
    targets = np.array([
        last[0] * 120.0,   # denormalized speed
        last[1] * 2200.0,  # denormalized volume
        last[2],           # congestion
    ], dtype=np.float32)
    
    return features, targets


def generate_dataset(
    num_samples: int = None,
    seq_len: int = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Generate full synthetic dataset for training.
    
    Returns:
      X: [num_samples, seq_len, input_dim]
      y: [num_samples, output_dim]
    """
    if num_samples is None:
        num_samples = synthetic_config.num_samples
    if seq_len is None:
        seq_len = model_config.seq_len
    
    road_types = ["motorway", "trunk", "primary", "secondary", "tertiary", "residential"]
    base_speeds = {"motorway": 100, "trunk": 80, "primary": 60, 
                   "secondary": 45, "tertiary": 35, "residential": 25}
    
    X_list = []
    y_list = []
    
    base_date = datetime(2024, 1, 1)
    
    for i in range(num_samples):
        road_type = random.choice(road_types)
        base_speed = base_speeds[road_type]
        
        # Random start time within a year
        days_offset = random.randint(0, 365)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.choice([0, 15, 30, 45])
        
        start_time = base_date + timedelta(
            days=days_offset, hours=hours_offset, minutes=minutes_offset
        )
        
        features, targets = generate_sequence(
            start_time, road_type, base_speed, seq_len
        )
        
        X_list.append(features)
        y_list.append(targets)
    
    X = torch.from_numpy(np.array(X_list))
    y = torch.from_numpy(np.array(y_list))
    
    print(f"[DataGen] Generated {num_samples} samples: X{list(X.shape)}, y{list(y.shape)}")
    return X, y
