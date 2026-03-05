"""AUMO v3 AI Service Configuration."""
import os
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class ModelConfig:
    input_dim: int = 10
    hidden_dim_1: int = 128
    hidden_dim_2: int = 64
    output_dim: int = 3
    forecast_steps: int = 6
    dropout: float = 0.3
    lookback: int = 12
    epochs: int = 30
    batch_size: int = 64
    learning_rate: float = 0.001


@dataclass
class GraphConfig:
    # Maharashtra bounding box (covers major cities)
    osm_bbox: Tuple[float, float, float, float] = field(default_factory=lambda: (
        float(os.getenv("OSM_BBOX", "15.60,72.60,21.50,80.90").split(",")[0]),
        float(os.getenv("OSM_BBOX", "15.60,72.60,21.50,80.90").split(",")[1]),
        float(os.getenv("OSM_BBOX", "15.60,72.60,21.50,80.90").split(",")[2]),
        float(os.getenv("OSM_BBOX", "15.60,72.60,21.50,80.90").split(",")[3]),
    ))
    v_max_kmh: float = 120.0
    bpr_alpha: float = 0.15
    bpr_beta: float = 4.0


@dataclass
class MatchingConfig:
    dbscan_eps_km: float = 2.0
    dbscan_min_pts: int = 2
    max_detour_ratio: float = 0.3
    min_match_score: float = 0.4
    w_route_overlap: float = 0.35
    w_time_compat: float = 0.25
    w_pref_match: float = 0.15
    w_proximity: float = 0.25
    t_max_seconds: float = 1800.0


@dataclass
class RoutingConfig:
    default_alpha: float = 0.4   # time weight
    default_beta: float = 0.3    # emissions weight
    default_gamma: float = 0.15  # distance weight
    default_delta: float = 0.15  # traffic density weight
    ch_enabled: bool = True      # Contraction Hierarchies
    dynamic_reroute: bool = True


@dataclass
class EmissionConfig:
    fuel_a: float = 0.0667
    fuel_b: float = 0.0556
    fuel_c: float = 0.000472
    co2_per_liter: float = 2310.0


@dataclass
class SyntheticDataConfig:
    num_days: int = 90
    num_segments: int = 50
    timestep_minutes: int = 5


# Instantiate configs
model_config = ModelConfig()
graph_config = GraphConfig()
matching_config = MatchingConfig()
routing_config = RoutingConfig()
emission_config = EmissionConfig()
synthetic_config = SyntheticDataConfig()

# Environment variables
OSRM_URL = os.getenv("OSRM_URL", "https://router.project-osrm.org")
MODEL_PATH = os.getenv("MODEL_PATH", "saved_models/traffic_lstm.pt")
API_KEY = os.getenv("API_KEY", "aumo-ai-api-key-change-in-production")

IS_HF_SPACE = os.getenv("SPACE_ID") is not None
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "https://*.vercel.app",
    "https://*.huggingface.co",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]
