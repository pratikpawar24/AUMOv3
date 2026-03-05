"""
AUMOv3 AI Service — FastAPI Application

Endpoints:
  POST /api/route          — Calculate optimal route (AUMORoute™)
  POST /api/multi-route    — Compare multiple route strategies
  POST /api/match          — Find carpool matches (DBSCAN + scoring)
  POST /api/traffic/predict — Predict traffic for road segments
  GET  /api/traffic/heatmap — Get traffic heatmap data
  POST /api/emissions      — Calculate CO₂ emissions
  POST /api/reroute        — Dynamic rerouting with live traffic
  GET  /api/poi            — Search Maharashtra POIs
  GET  /api/poi/map        — Get POIs for map bounds
  GET  /api/poi/types      — Get POI type definitions
  POST /api/train          — Trigger model training
  GET  /api/health         — Health check
"""

import os
import asyncio
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import torch
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from config import (
    model_config, graph_config, routing_config,
    CORS_ORIGINS, API_PORT, MODEL_PATH,
)
from algorithms.graph_builder import build_graph, build_synthetic_graph, find_nearest_node
from algorithms.astar import (
    astar_route, dynamic_reroute, get_traffic_overlay,
    ContractionHierarchies,
)
from algorithms.emissions import (
    calculate_ride_emissions, calculate_carpool_savings, co2_to_tree_days,
)
from algorithms.matching import (
    find_matches, batch_match,
    RideOffer, RideRequest,
)
from algorithms.maharashtra_poi import (
    search_pois, get_pois_for_map, get_poi_types, get_cities,
    ALL_MAHARASHTRA_POIS,
)
from models.lstm_model import TrafficLSTM, load_model, predict_traffic
from models.data_generator import time_features, road_type_encoding


# ═══════════════════════════════════════════════════════════════
# App Initialization
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AUMOv3 AI Service",
    description="AI-powered routing, traffic prediction, and carpool matching for Maharashtra",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(",") if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
state = {
    "graph": None,
    "ch": None,
    "model": None,
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "ready": False,
    "training": False,
}


# ═══════════════════════════════════════════════════════════════
# Startup
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    """Initialize graph, model, and CH preprocessing."""
    print("\n" + "=" * 60)
    print("  AUMOv3 AI Service Starting...")
    print("=" * 60)

    # Build road graph
    try:
        print("[Startup] Building road graph...")
        G = build_graph()
        if G is None or len(G.nodes()) == 0:
            print("[Startup] OSM fetch failed, using synthetic graph")
            G = build_synthetic_graph()
        state["graph"] = G
        print(f"[Startup] Graph: {len(G.nodes())} nodes, {len(G.edges())} edges")
    except Exception as e:
        print(f"[Startup] Graph error: {e}, using synthetic")
        state["graph"] = build_synthetic_graph()

    # Contraction Hierarchies
    if routing_config.use_ch and state["graph"]:
        try:
            print("[Startup] Running CH preprocessing...")
            ch = ContractionHierarchies(state["graph"])
            ch.preprocess()
            state["ch"] = ch
        except Exception as e:
            print(f"[Startup] CH preprocessing error: {e}")

    # Load traffic model
    try:
        model = load_model(MODEL_PATH, device=state["device"])
        state["model"] = model
    except Exception as e:
        print(f"[Startup] Model load error: {e}")
        state["model"] = TrafficLSTM().to(state["device"])

    state["ready"] = True
    print(f"\n[Startup] AI Service ready on port {API_PORT}")
    print(f"[Startup] Device: {state['device']}")
    print(f"[Startup] POIs loaded: {len(ALL_MAHARASHTRA_POIS)}")
    print("=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════
# Request / Response Models
# ═══════════════════════════════════════════════════════════════

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: Optional[str] = None
    alpha: float = Field(default=0.4, ge=0, le=1)
    beta: float = Field(default=0.3, ge=0, le=1)
    gamma: float = Field(default=0.15, ge=0, le=1)
    delta: float = Field(default=0.15, ge=0, le=1)
    avoid_congested: bool = True


class MultiRouteRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: Optional[str] = None


class MatchRequest(BaseModel):
    passenger_id: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: str
    preferences: Optional[Dict] = {}


class OfferData(BaseModel):
    id: str
    driver_id: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: str
    seats_available: int = 3
    route_distance_km: float = 10.0
    route_duration_min: float = 25.0
    preferences: Optional[Dict] = {}


class MatchBatchRequest(BaseModel):
    request: MatchRequest
    offers: List[OfferData]
    top_k: int = 10


class EmissionRequest(BaseModel):
    distance_km: float
    avg_speed_kmh: float = 35.0
    fuel_type: str = "petrol"
    num_passengers: int = 1


class RerouteRequest(BaseModel):
    current_lat: float
    current_lng: float
    dest_lat: float
    dest_lng: float
    departure_time: Optional[str] = None
    weights: Optional[Dict[str, float]] = None


class TrafficPredictRequest(BaseModel):
    segments: List[Dict]


class POISearchRequest(BaseModel):
    query: str = ""
    poi_type: str = ""
    city: str = ""
    lat: float = 0
    lng: float = 0
    radius_km: float = 50
    limit: int = 50


# ═══════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"service": "AUMOv3 AI", "status": "running", "version": "3.0.0"}


@app.get("/api/health")
async def health():
    return {
        "status": "healthy" if state["ready"] else "initializing",
        "graph_nodes": len(state["graph"].nodes()) if state["graph"] else 0,
        "graph_edges": len(state["graph"].edges()) if state["graph"] else 0,
        "ch_ready": state["ch"] is not None,
        "model_loaded": state["model"] is not None,
        "device": state["device"],
        "poi_count": len(ALL_MAHARASHTRA_POIS),
        "version": "3.0.0",
    }


@app.post("/api/route")
async def calculate_route(req: RouteRequest):
    """Calculate optimal route using AUMORoute™."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    G = state["graph"]
    
    start_node = find_nearest_node(G, req.origin_lat, req.origin_lng)
    goal_node = find_nearest_node(G, req.dest_lat, req.dest_lng)
    
    if start_node is None or goal_node is None:
        raise HTTPException(404, "Could not find nodes near the given coordinates")

    dep_time = datetime.fromisoformat(req.departure_time) if req.departure_time else datetime.now()

    result = astar_route(
        G, start_node, goal_node, dep_time,
        alpha=req.alpha, beta=req.beta,
        gamma=req.gamma, delta=req.delta,
        traffic_predictions=None,
        ch=state["ch"],
        avoid_congested=req.avoid_congested,
    )
    
    if result is None:
        raise HTTPException(404, "No route found between the given points")

    # Add traffic overlay
    overlay = get_traffic_overlay(G, result["path_nodes"], current_time=dep_time)
    result["trafficOverlay"] = overlay
    
    # CO₂ info
    co2 = calculate_ride_emissions(result["distanceKm"], result.get("durationMin", 30))
    result["co2Details"] = co2
    result["treeDaysEquivalent"] = co2_to_tree_days(co2["co2_grams"])

    return {"success": True, "route": result}


@app.post("/api/multi-route")
async def multi_route(req: MultiRouteRequest):
    """Compare routes with different optimization strategies."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    G = state["graph"]
    start_node = find_nearest_node(G, req.origin_lat, req.origin_lng)
    goal_node = find_nearest_node(G, req.dest_lat, req.dest_lng)
    
    if start_node is None or goal_node is None:
        raise HTTPException(404, "Could not find nodes near coordinates")

    dep_time = datetime.fromisoformat(req.departure_time) if req.departure_time else datetime.now()

    strategies = {
        "fastest":    {"alpha": 0.7, "beta": 0.1, "gamma": 0.1, "delta": 0.1},
        "eco":        {"alpha": 0.2, "beta": 0.6, "gamma": 0.1, "delta": 0.1},
        "shortest":   {"alpha": 0.1, "beta": 0.1, "gamma": 0.7, "delta": 0.1},
        "balanced":   {"alpha": 0.4, "beta": 0.3, "gamma": 0.15, "delta": 0.15},
        "low_traffic":{"alpha": 0.2, "beta": 0.1, "gamma": 0.1, "delta": 0.6},
    }

    routes = {}
    for name, weights in strategies.items():
        result = astar_route(
            G, start_node, goal_node, dep_time,
            **weights, ch=state["ch"],
        )
        if result:
            co2 = calculate_ride_emissions(result["distanceKm"], result.get("durationMin", 30))
            result["co2Details"] = co2
            routes[name] = result

    if not routes:
        raise HTTPException(404, "No routes found")

    return {"success": True, "routes": routes}


@app.post("/api/match")
async def match_rides(req: MatchBatchRequest):
    """Find carpool matches for a ride request."""
    request = RideRequest(
        id=f"req_{req.request.passenger_id}",
        passenger_id=req.request.passenger_id,
        origin_lat=req.request.origin_lat,
        origin_lng=req.request.origin_lng,
        dest_lat=req.request.dest_lat,
        dest_lng=req.request.dest_lng,
        departure_time=datetime.fromisoformat(req.request.departure_time),
        preferences=req.request.preferences or {},
    )

    offers = []
    for o in req.offers:
        offers.append(RideOffer(
            id=o.id,
            driver_id=o.driver_id,
            origin_lat=o.origin_lat,
            origin_lng=o.origin_lng,
            dest_lat=o.dest_lat,
            dest_lng=o.dest_lng,
            departure_time=datetime.fromisoformat(o.departure_time),
            seats_available=o.seats_available,
            route_distance_km=o.route_distance_km,
            route_duration_min=o.route_duration_min,
            preferences=o.preferences or {},
        ))

    matches = find_matches(request, offers, top_k=req.top_k)

    return {
        "success": True,
        "matches": [
            {
                "offerId": m.offer_id,
                "score": m.score,
                "routeOverlap": m.route_overlap,
                "timeCompatibility": m.time_compatibility,
                "preferenceMatch": m.preference_match,
                "proximityScore": m.proximity_score,
                "pickupDetourKm": m.pickup_detour_km,
                "dropoffDetourKm": m.dropoff_detour_km,
                "co2SavingsGrams": m.co2_savings_g,
                "estimatedFare": m.estimated_fare,
            }
            for m in matches
        ],
        "totalOffers": len(offers),
    }


@app.post("/api/traffic/predict")
async def predict_traffic_endpoint(req: TrafficPredictRequest):
    """Predict traffic for road segments."""
    if state["model"] is None:
        raise HTTPException(503, "Model not loaded")

    model = state["model"]
    device = state["device"]
    results = []

    for seg in req.segments:
        now = datetime.now()
        tf = time_features(now)
        speed = seg.get("current_speed", 40) / 120.0
        volume = seg.get("current_volume", 500) / 2200.0
        congestion = seg.get("current_congestion", 0.3)
        rt = road_type_encoding(seg.get("road_type", "primary"))

        feature_vec = [
            speed, volume, congestion,
            tf["hour_sin"], tf["hour_cos"],
            tf["day_sin"], tf["day_cos"],
            tf["is_weekend"], tf["is_holiday"],
            rt,
        ]
        
        seq = torch.tensor([feature_vec] * model_config.seq_len, dtype=torch.float32)
        pred = predict_traffic(model, seq, device)
        
        results.append({
            "segment_id": seg.get("id", "unknown"),
            "predicted_speed": round(pred["speed"], 1),
            "predicted_volume": round(pred["volume"], 0),
            "congestion_level": round(pred["congestion"], 3),
        })

    return {"success": True, "predictions": results}


@app.get("/api/traffic/heatmap")
async def traffic_heatmap():
    """Get traffic heatmap data for map visualization."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    G = state["graph"]
    now = datetime.now()
    heatmap_data = []

    for node_id in list(G.nodes())[:500]:
        node = G.nodes[node_id]
        
        neighbors = list(G.successors(node_id))
        if not neighbors:
            continue

        avg_congestion = 0.0
        for n in neighbors[:3]:
            edge = G.edges[node_id, n]
            from algorithms.astar import time_dependent_weight
            _, _, cong = time_dependent_weight(edge, now)
            avg_congestion += cong
        avg_congestion /= min(len(neighbors), 3)

        heatmap_data.append({
            "lat": node["lat"],
            "lng": node["lng"],
            "intensity": round(avg_congestion, 3),
        })

    return {"success": True, "heatmap": heatmap_data}


@app.post("/api/emissions")
async def calculate_emissions(req: EmissionRequest):
    """Calculate CO₂ emissions and carpool savings."""
    emissions = calculate_ride_emissions(
        req.distance_km, req.distance_km / req.avg_speed_kmh * 60,
        req.fuel_type,
    )
    
    savings = calculate_carpool_savings(
        req.distance_km, req.num_passengers, req.avg_speed_kmh, req.fuel_type,
    )
    
    tree_days = co2_to_tree_days(emissions["co2_grams"])

    return {
        "success": True,
        "emissions": emissions,
        "carpoolSavings": savings,
        "treeDaysEquivalent": tree_days,
    }


@app.post("/api/reroute")
async def reroute(req: RerouteRequest):
    """Dynamic rerouting based on current traffic."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    dep_time = datetime.fromisoformat(req.departure_time) if req.departure_time else datetime.now()
    weights = req.weights or {"alpha": 0.4, "beta": 0.3, "gamma": 0.15, "delta": 0.15}

    result = dynamic_reroute(
        state["graph"],
        (req.current_lat, req.current_lng),
        (req.dest_lat, req.dest_lng),
        dep_time,
        current_traffic={},
        weights=weights,
        ch=state["ch"],
    )

    if result is None:
        raise HTTPException(404, "No alternative route found")

    co2 = calculate_ride_emissions(result["distanceKm"], result.get("durationMin", 30))
    result["co2Details"] = co2

    return {"success": True, "route": result}


@app.get("/api/poi")
async def poi_search(
    query: str = "",
    poi_type: str = "",
    city: str = "",
    lat: float = 0,
    lng: float = 0,
    radius_km: float = 50,
    limit: int = 50,
):
    """Search Maharashtra POIs."""
    results = search_pois(query, poi_type, city, lat, lng, radius_km, limit)
    return {"success": True, "pois": results, "total": len(results)}


@app.get("/api/poi/map")
async def poi_for_map(
    south: float = 15.6,
    north: float = 21.5,
    west: float = 72.6,
    east: float = 80.9,
    types: str = "",
    limit: int = 200,
):
    """Get POIs within map bounds."""
    bounds = {"south": south, "north": north, "west": west, "east": east}
    type_list = [t.strip() for t in types.split(",") if t.strip()] if types else None
    results = get_pois_for_map(bounds, type_list, limit)
    return {"success": True, "pois": results, "total": len(results)}


@app.get("/api/poi/types")
async def poi_types():
    """Get POI type definitions for frontend."""
    return {"success": True, "types": get_poi_types(), "cities": get_cities()}


@app.post("/api/train")
async def train_model(background_tasks: BackgroundTasks):
    """Trigger model training in background."""
    if state["training"]:
        raise HTTPException(409, "Training already in progress")

    def _train():
        state["training"] = True
        try:
            from models.trainer import Trainer
            trainer = Trainer(device=state["device"])
            trainer.train(epochs=30, num_samples=3000)
            state["model"] = trainer.model
        except Exception as e:
            print(f"[Train] Error: {e}")
        finally:
            state["training"] = False

    background_tasks.add_task(_train)
    return {"success": True, "message": "Training started in background"}


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_PORT,
        reload=True,
        log_level="info",
    )
