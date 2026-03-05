"""
AUMOv3 AI Gateway Service — FastAPI Application (Space 1)

Lightweight gateway that handles routing, emissions, and matching locally,
while proxying ML predictions to Space 2 (AUMOV3.1) and
POI/places requests to Space 3 (AUMOv3.2).

NO PyTorch dependency — fast startup for HuggingFace Spaces.

Endpoints:
  POST /api/route              — Calculate optimal route (AUMORoute™)
  POST /api/multi-route        — Compare multiple route strategies
  POST /api/routes/alternatives — K alternative routes (Yen's algorithm)
  POST /api/match              — Find carpool matches (DBSCAN + scoring)
  POST /api/traffic/predict    — Proxy to ML service (Space 2)
  GET  /api/traffic/heatmap    — Live traffic heatmap (OSRM + time model)
  GET  /api/traffic/live       — Real-time traffic from OSRM corridors
  POST /api/emissions          — Calculate CO₂ emissions
  POST /api/reroute            — Dynamic rerouting with live traffic
  GET  /api/poi                — Proxy to Data service (Space 3)
  GET  /api/poi/map            — Proxy to Data service (Space 3)
  GET  /api/poi/types          — Proxy to Data service (Space 3)
  GET  /api/poi/cities         — Proxy to Data service (Space 3)
  POST /api/places/search      — Proxy to Data service (Space 3)
  GET  /api/places/nearby      — Proxy to Data service (Space 3)
  GET  /api/places/stops       — Proxy to Data service (Space 3)
  POST /api/train              — Proxy to ML service (Space 2)
  GET  /api/health             — Health check
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from config import (
    model_config, graph_config, routing_config,
    CORS_ORIGINS, API_PORT,
    ML_SERVICE_URL, DATA_SERVICE_URL,
)
from algorithms.graph_builder import build_graph, build_synthetic_graph, find_nearest_node
from algorithms.astar import (
    astar_route, dynamic_reroute, get_traffic_overlay,
    ContractionHierarchies, yen_k_shortest_paths,
)
from algorithms.emissions import (
    calculate_ride_emissions, calculate_carpool_savings, co2_to_tree_days,
)
from algorithms.matching import (
    find_matches,
    RideOffer, RideRequest,
)
from utils.live_traffic import get_live_traffic_sample, get_live_heatmap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aumov3-gateway")


# ═══════════════════════════════════════════════════════════════
# App Initialization
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AUMOv3 AI Gateway",
    description="AI-powered routing, traffic prediction, and carpool matching for Maharashtra",
    version="3.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state — NO PyTorch, NO model
state = {
    "graph": None,
    "ch": None,
    "ready": False,
}


# ═══════════════════════════════════════════════════════════════
# Startup — lightweight, no PyTorch
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    """Initialize graph and CH preprocessing (no ML model loading)."""
    logger.info("=" * 60)
    logger.info("  AUMOv3 AI Gateway Starting...")
    logger.info(f"  ML Service: {ML_SERVICE_URL}")
    logger.info(f"  Data Service: {DATA_SERVICE_URL}")
    logger.info("=" * 60)

    # Build road graph
    try:
        logger.info("[Startup] Building road graph...")
        G = await build_graph()
        if G is None or len(G.nodes()) == 0:
            logger.warning("[Startup] OSM fetch failed, using synthetic graph")
            G = build_synthetic_graph(graph_config.osm_bbox)
        state["graph"] = G
        logger.info(f"[Startup] Graph: {len(G.nodes())} nodes, {len(G.edges())} edges")
    except Exception as e:
        logger.error(f"[Startup] Graph error: {e}, using synthetic")
        state["graph"] = build_synthetic_graph(graph_config.osm_bbox)

    # Contraction Hierarchies
    if routing_config.ch_enabled and state["graph"]:
        try:
            logger.info("[Startup] Running CH preprocessing...")
            ch = ContractionHierarchies(state["graph"])
            ch.preprocess()
            state["ch"] = ch
            logger.info("[Startup] CH preprocessing done")
        except Exception as e:
            logger.warning(f"[Startup] CH preprocessing error: {e}")

    state["ready"] = True
    logger.info(f"[Startup] Gateway ready on port {API_PORT}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# Proxy Helper
# ═══════════════════════════════════════════════════════════════

async def proxy_request(
    service_url: str,
    path: str,
    method: str = "GET",
    json_body: dict = None,
    params: dict = None,
) -> dict:
    """Proxy a request to another service."""
    url = f"{service_url}{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                resp = await client.get(url, params=params)
            else:
                resp = await client.post(url, json=json_body, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(503, f"Service unavailable at {service_url}")
    except httpx.TimeoutException:
        raise HTTPException(504, f"Service timeout at {service_url}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, f"Upstream error: {e.response.text[:200]}")
    except Exception as e:
        raise HTTPException(502, f"Proxy error: {str(e)[:200]}")


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


# ═══════════════════════════════════════════════════════════════
# LOCAL Endpoints (routing, emissions, matching)
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "service": "AUMOv3 AI Gateway",
        "version": "3.0.0",
        "status": "running",
        "ml_service": ML_SERVICE_URL,
        "data_service": DATA_SERVICE_URL,
    }


@app.get("/api/health")
async def health():
    # Check sub-services health
    ml_ok = False
    data_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{ML_SERVICE_URL}/api/health")
            ml_ok = r.status_code == 200
    except:
        pass
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{DATA_SERVICE_URL}/api/health")
            data_ok = r.status_code == 200
    except:
        pass

    return {
        "status": "healthy" if state["ready"] else "initializing",
        "graph_nodes": len(state["graph"].nodes()) if state["graph"] else 0,
        "graph_edges": len(state["graph"].edges()) if state["graph"] else 0,
        "ch_ready": state["ch"] is not None,
        "ml_service": "connected" if ml_ok else "unavailable",
        "data_service": "connected" if data_ok else "unavailable",
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

    overlay = get_traffic_overlay(G, result["path_nodes"], current_time=dep_time)
    result["trafficOverlay"] = overlay

    co2 = calculate_ride_emissions(result["distanceKm"], result.get("durationMin", 30))
    result["co2Details"] = co2
    result["treeDaysEquivalent"] = co2_to_tree_days(co2.get("co2_grams", 0))

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
        "fastest":     {"alpha": 0.7, "beta": 0.1, "gamma": 0.1, "delta": 0.1},
        "eco":         {"alpha": 0.2, "beta": 0.6, "gamma": 0.1, "delta": 0.1},
        "shortest":    {"alpha": 0.1, "beta": 0.1, "gamma": 0.7, "delta": 0.1},
        "balanced":    {"alpha": 0.4, "beta": 0.3, "gamma": 0.15, "delta": 0.15},
        "low_traffic": {"alpha": 0.2, "beta": 0.1, "gamma": 0.1, "delta": 0.6},
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

    tree_days = co2_to_tree_days(emissions.get("co2_grams", 0))

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


@app.post("/api/routes/alternatives")
async def alternative_routes(req: RouteRequest):
    """Find K alternative routes using Yen's K-shortest paths algorithm."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    G = state["graph"]
    start_node = find_nearest_node(G, req.origin_lat, req.origin_lng)
    goal_node = find_nearest_node(G, req.dest_lat, req.dest_lng)

    if start_node is None or goal_node is None:
        raise HTTPException(404, "Could not find nodes near the given coordinates")

    dep_time = datetime.fromisoformat(req.departure_time) if req.departure_time else datetime.now()

    routes = yen_k_shortest_paths(
        G, start_node, goal_node,
        departure_time=dep_time,
        K=3,
        alpha=req.alpha, beta=req.beta,
        gamma=req.gamma, delta=req.delta,
        ch=state["ch"],
    )

    if not routes:
        raise HTTPException(404, "No routes found between the given points")

    for r in routes:
        overlay = get_traffic_overlay(G, r["path_nodes"], current_time=dep_time)
        r["trafficOverlay"] = overlay
        co2 = calculate_ride_emissions(r["distanceKm"], r.get("durationMin", 30))
        r["co2Details"] = co2
        r["treeDaysEquivalent"] = co2_to_tree_days(co2.get("co2_grams", 0))

    return {"success": True, "routes": routes, "count": len(routes)}


@app.get("/api/traffic/heatmap")
async def traffic_heatmap():
    """Get real-time traffic heatmap using live OSRM data + time-based patterns."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    heatmap_data = await get_live_heatmap(graph=state["graph"])
    return {"success": True, "heatmap": heatmap_data, "source": "live_osrm+time_model"}


@app.get("/api/traffic/live")
async def live_traffic():
    """Get real-time traffic conditions from OSRM for key corridors."""
    if not state["ready"] or state["graph"] is None:
        raise HTTPException(503, "Service not ready")

    segments = await get_live_traffic_sample()
    return {"success": True, "segments": segments, "source": "osrm_live"}


# ═══════════════════════════════════════════════════════════════
# PROXIED Endpoints — ML Service (Space 2)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/traffic/predict")
async def predict_traffic_proxy(req: TrafficPredictRequest):
    """Proxy traffic prediction to ML service (Space 2)."""
    return await proxy_request(
        ML_SERVICE_URL, "/api/traffic/predict",
        method="POST", json_body=req.dict(),
    )


@app.post("/api/train")
async def train_model_proxy():
    """Proxy model training to ML service (Space 2)."""
    return await proxy_request(
        ML_SERVICE_URL, "/api/train",
        method="POST", json_body={},
    )


# ═══════════════════════════════════════════════════════════════
# PROXIED Endpoints — Data Service (Space 3)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/poi")
async def poi_search(
    query: str = "",
    type: str = "",
    city: str = "",
    lat: float = 0,
    lng: float = 0,
    radius_km: float = 50,
    limit: int = 50,
):
    """Proxy POI search to Data service (Space 3)."""
    params = {k: v for k, v in {
        "query": query, "type": type, "city": city,
        "lat": lat, "lng": lng, "radius_km": radius_km, "limit": limit,
    }.items() if v}
    return await proxy_request(DATA_SERVICE_URL, "/api/poi", params=params)


@app.get("/api/poi/map")
async def poi_for_map(
    south: float = 15.6,
    north: float = 21.5,
    west: float = 72.6,
    east: float = 80.9,
    types: str = "",
    limit: int = 200,
):
    """Proxy POI map to Data service (Space 3)."""
    return await proxy_request(
        DATA_SERVICE_URL, "/api/poi/map",
        method="POST",
        json_body={"south": south, "north": north, "west": west, "east": east,
                    "types": [t.strip() for t in types.split(",") if t.strip()],
                    "limit": limit},
    )


@app.get("/api/poi/types")
async def poi_types():
    """Proxy POI types to Data service (Space 3)."""
    return await proxy_request(DATA_SERVICE_URL, "/api/poi/types")


@app.get("/api/poi/cities")
async def poi_cities():
    """Proxy POI cities to Data service (Space 3)."""
    return await proxy_request(DATA_SERVICE_URL, "/api/poi/cities")


@app.post("/api/places/search")
async def places_search(request: Request):
    """Proxy places search to Data service (Space 3)."""
    body = await request.json()
    return await proxy_request(
        DATA_SERVICE_URL, "/api/places/search",
        method="POST", json_body=body,
    )


@app.get("/api/places/search")
async def places_search_get(
    query: str = "",
    lat: float = 0,
    lng: float = 0,
    radius_km: float = 5,
    city: str = "",
    limit: int = 50,
):
    """Proxy GET places search to Data service (Space 3)."""
    params = {k: v for k, v in {
        "query": query, "lat": lat, "lng": lng,
        "radius_km": radius_km, "city": city, "limit": limit,
    }.items() if v}
    return await proxy_request(DATA_SERVICE_URL, "/api/places/search", params=params)


@app.get("/api/places/nearby")
async def places_nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = 5000,
):
    """Proxy nearby places to Data service (Space 3)."""
    return await proxy_request(
        DATA_SERVICE_URL, "/api/places/nearby",
        params={"lat": lat, "lng": lng, "radius": radius},
    )


@app.get("/api/places/stops")
async def places_stops(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = 3000,
):
    """Proxy nearby stops to Data service (Space 3)."""
    return await proxy_request(
        DATA_SERVICE_URL, "/api/places/stops",
        params={"lat": lat, "lng": lng, "radius": radius},
    )


@app.get("/api/data/stats")
async def data_stats():
    """Proxy data stats to Data service (Space 3)."""
    return await proxy_request(DATA_SERVICE_URL, "/api/data/stats")


# ═══════════════════════════════════════════════════════════════
# Live Traffic Speed Proxy (to ML service)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/traffic/route-speed")
async def traffic_route_speed(request: Request):
    """Proxy route speed check to ML service (Space 2)."""
    body = await request.json()
    return await proxy_request(ML_SERVICE_URL, "/api/traffic/route-speed", method="POST", json_body=body)


@app.post("/api/traffic/live-segments")
async def traffic_live_segments(request: Request):
    """Proxy live segment speeds to ML service (Space 2)."""
    body = await request.json()
    return await proxy_request(ML_SERVICE_URL, "/api/traffic/live-segments", method="POST", json_body=body)


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=API_PORT,
        log_level="info",
    )
