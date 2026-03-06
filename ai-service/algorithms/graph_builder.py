"""
OSM Graph Builder — Build road network graph from OpenStreetMap data.

Graph construction: G = (V, E)
    V = {OSM nodes (intersections)}
    E = {OSM ways (road segments)}
    Each edge e: {length_m, speed_limit, lanes, road_type, oneway, capacity}
"""

import math
import httpx
import numpy as np
import networkx as nx
from typing import Dict, Any, Optional, Tuple, List
from utils.haversine import haversine
from config import graph_config

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

ROAD_SPEED_LIMITS: Dict[str, float] = {
    "motorway": 120.0, "motorway_link": 80.0,
    "trunk": 100.0, "trunk_link": 60.0,
    "primary": 80.0, "primary_link": 50.0,
    "secondary": 60.0, "secondary_link": 40.0,
    "tertiary": 50.0, "tertiary_link": 30.0,
    "residential": 30.0, "living_street": 20.0,
    "unclassified": 40.0, "service": 20.0,
}

ROAD_LANES: Dict[str, int] = {
    "motorway": 3, "trunk": 2, "primary": 2, "secondary": 2,
    "tertiary": 1, "residential": 1, "unclassified": 1, "service": 1,
}

CAPACITY_PER_LANE_HOUR = 1800


def build_overpass_query(bbox: Tuple[float, float, float, float]) -> str:
    south, west, north, east = bbox
    return f"""
    [out:json][timeout:30];
    (
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"]({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """


async def fetch_osm_data(bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
    """Fetch road data from Overpass API with short timeout."""
    query = build_overpass_query(bbox)
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(OVERPASS_URL, data={"data": query})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"[GraphBuilder] Overpass API error: {e}")
        return {"elements": []}


def parse_speed_limit(tags: Dict[str, str], highway_type: str) -> float:
    if "maxspeed" in tags:
        try:
            speed_str = tags["maxspeed"].replace("mph", "").replace("km/h", "").strip()
            return float(speed_str)
        except (ValueError, AttributeError):
            pass
    return ROAD_SPEED_LIMITS.get(highway_type, 40.0)


def parse_lanes(tags: Dict[str, str], highway_type: str) -> int:
    if "lanes" in tags:
        try:
            return int(tags["lanes"])
        except (ValueError, AttributeError):
            pass
    return ROAD_LANES.get(highway_type, 1)


def build_graph_from_osm_data(osm_data: Dict[str, Any]) -> nx.DiGraph:
    """Build a NetworkX directed graph from OSM data."""
    G = nx.DiGraph()
    elements = osm_data.get("elements", [])

    nodes: Dict[int, Dict[str, float]] = {}
    ways: List[Dict[str, Any]] = []

    for el in elements:
        if el["type"] == "node":
            nodes[el["id"]] = {"lat": el["lat"], "lon": el["lon"]}
        elif el["type"] == "way":
            ways.append(el)

    node_refs: Dict[int, int] = {}
    for way in ways:
        for node_id in way.get("nodes", []):
            node_refs[node_id] = node_refs.get(node_id, 0) + 1

    for node_id, coords in nodes.items():
        G.add_node(node_id, lat=coords["lat"], lng=coords["lon"])

    for way in ways:
        tags = way.get("tags", {})
        highway_type = tags.get("highway", "unclassified")
        speed_limit = parse_speed_limit(tags, highway_type)
        lanes = parse_lanes(tags, highway_type)
        oneway = tags.get("oneway", "no") == "yes"
        capacity = lanes * CAPACITY_PER_LANE_HOUR

        way_nodes = way.get("nodes", [])
        for i in range(len(way_nodes) - 1):
            n1, n2 = way_nodes[i], way_nodes[i + 1]
            if n1 not in nodes or n2 not in nodes:
                continue

            lat1, lng1 = nodes[n1]["lat"], nodes[n1]["lon"]
            lat2, lng2 = nodes[n2]["lat"], nodes[n2]["lon"]
            length_m = haversine(lat1, lng1, lat2, lng2)

            edge_attrs = {
                "length_m": length_m,
                "speed_limit_kmh": speed_limit,
                "free_flow_speed_kmh": speed_limit,
                "lanes": lanes, "road_type": highway_type,
                "oneway": oneway, "capacity": capacity,
                "osm_way_id": way["id"],
            }
            G.add_edge(n1, n2, **edge_attrs)
            if not oneway:
                G.add_edge(n2, n1, **edge_attrs)

    print(f"[GraphBuilder] Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


async def build_graph(bbox: Optional[Tuple[float, float, float, float]] = None) -> nx.DiGraph:
    if bbox is None:
        bbox = graph_config.osm_bbox
    print(f"[GraphBuilder] Fetching OSM data for bbox: {bbox}")
    osm_data = await fetch_osm_data(bbox)
    if not osm_data.get("elements"):
        print("[GraphBuilder] No OSM data received, building synthetic graph")
        return build_synthetic_graph(bbox)
    return build_graph_from_osm_data(osm_data)


def build_synthetic_graph(
    bbox: Tuple[float, float, float, float],
    grid_size: int = 25,
) -> nx.DiGraph:
    """Build a synthetic grid graph when OSM data is unavailable."""
    G = nx.DiGraph()
    south, west, north, east = bbox
    lat_step = (north - south) / (grid_size - 1)
    lng_step = (east - west) / (grid_size - 1)

    import random
    random.seed(42)

    node_id = 1
    node_grid: Dict[Tuple[int, int], int] = {}
    for i in range(grid_size):
        for j in range(grid_size):
            lat = south + i * lat_step
            lng = west + j * lng_step
            G.add_node(node_id, lat=lat, lng=lng)
            node_grid[(i, j)] = node_id
            node_id += 1

    road_types = ["primary", "secondary", "tertiary", "residential"]
    for i in range(grid_size):
        for j in range(grid_size):
            n1 = node_grid[(i, j)]
            for di, dj in [(0, 1), (1, 0), (1, 1), (-1, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < grid_size and 0 <= nj < grid_size:
                    n2 = node_grid[(ni, nj)]
                    lat1, lng1 = G.nodes[n1]["lat"], G.nodes[n1]["lng"]
                    lat2, lng2 = G.nodes[n2]["lat"], G.nodes[n2]["lng"]
                    length_m = haversine(lat1, lng1, lat2, lng2)
                    road_type = random.choice(road_types)
                    speed_limit = ROAD_SPEED_LIMITS.get(road_type, 40.0)
                    lanes = ROAD_LANES.get(road_type, 1)
                    edge_attrs = {
                        "length_m": length_m,
                        "speed_limit_kmh": speed_limit,
                        "free_flow_speed_kmh": speed_limit,
                        "lanes": lanes, "road_type": road_type,
                        "oneway": False,
                        "capacity": lanes * CAPACITY_PER_LANE_HOUR,
                        "osm_way_id": 0,
                    }
                    G.add_edge(n1, n2, **edge_attrs)
                    G.add_edge(n2, n1, **edge_attrs)

    print(f"[GraphBuilder] Synthetic graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def find_nearest_node(G: nx.DiGraph, lat: float, lng: float) -> Optional[int]:
    """Find the nearest graph node using vectorized numpy distance (fast)."""
    coords = getattr(G, '_spatial_coords', None)
    node_ids = getattr(G, '_spatial_ids', None)
    if coords is not None and node_ids is not None:
        # Vectorized Euclidean distance on lat/lng (good enough for small areas)
        diffs = coords - np.array([lat, lng])
        dists = np.sum(diffs ** 2, axis=1)
        idx = np.argmin(dists)
        return node_ids[idx]
    # Fallback: linear scan
    min_dist = float("inf")
    nearest = None
    for node_id, data in G.nodes(data=True):
        dist = haversine(lat, lng, data["lat"], data["lng"])
        if dist < min_dist:
            min_dist = dist
            nearest = node_id
    return nearest


def build_spatial_index(G: nx.DiGraph):
    """Build a numpy-based spatial index on the graph for nearest-node lookups.
    
    Pure-numpy replacement for scipy.spatial.cKDTree — no scipy needed.
    Uses brute-force vectorized distance (fast enough for <100k nodes).
    """
    node_ids = []
    coords = []
    for nid, data in G.nodes(data=True):
        node_ids.append(nid)
        coords.append([data["lat"], data["lng"]])
    if coords:
        arr = np.array(coords)
        G._spatial_coords = arr
        G._spatial_ids = node_ids
        print(f"[GraphBuilder] Spatial index built for {len(node_ids)} nodes")
    return G
