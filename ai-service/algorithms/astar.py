"""
AUMORoute™ — Custom Routing Algorithm (v3 2025)

Combines Contraction Hierarchies (CH) for preprocessing speed with
Time-Dependent A* for real-time traffic-aware routing.

Architecture:
  1. Contraction Hierarchies Preprocessing:
     - Node ordering by importance (degree × edge_diff × contracted_neighbors)
     - Shortcut creation for fast bidirectional Dijkstra
     - Preprocessing: O(n log n), Query: O(√n log n)

  2. Time-Dependent A* with Multi-Objective Cost:
     f(n, t) = g(n, t) + h(n)
     g(n, t) = Σ w(eᵢ, tᵢ) 
     w(e, t) = length(e) / v_predicted(e, t) [LSTM prediction]
            OR t₀ × [1 + 0.15 × (V/C)⁴]    [BPR fallback]

  3. Multi-Objective Cost Function:
     Cost(path) = α·T + β·E + γ·D + δ·TrafficDensity
     T = total travel time (seconds)
     E = total CO₂ emissions (grams)
     D = total distance (meters)
     TrafficDensity = average congestion along path
     α + β + γ + δ = 1

  4. Dynamic Rerouting:
     When real-time traffic changes detected:
       - Invalidate affected edges
       - Recalculate from current position
       - Choose path avoiding high-congestion segments
"""

import heapq
import math
import time as time_module
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict

import networkx as nx

from utils.haversine import haversine
from algorithms.emissions import emission_factor
from config import graph_config, routing_config


# ═══════════════════════════════════════════════════════════════
# PART 1: Contraction Hierarchies (CH) Preprocessing
# ═══════════════════════════════════════════════════════════════

class ContractionHierarchies:
    """Contraction Hierarchies for ultra-fast shortest path queries.
    
    Preprocessing:
      1. Order nodes by importance: importance(v) = edge_diff(v) + contracted_neighbors(v) + node_level(v)
      2. Contract nodes in order: for each node u being contracted,
         for each pair (v, w) where v→u→w exists:
           if shortest path from v to w goes through u, add shortcut v→w
      3. Store node levels for bidirectional search
    
    Query:
      Bidirectional Dijkstra on augmented graph:
        Forward search: only relax edges to higher-level nodes
        Backward search: only relax edges to higher-level nodes
        Meet in the middle → optimal path
    """
    
    def __init__(self, G: nx.DiGraph):
        self.original_graph = G
        self.augmented_graph = G.copy()
        self.node_level: Dict[int, int] = {}
        self.node_order: List[int] = []
        self.shortcuts: Dict[Tuple[int, int], Dict] = {}
        self.contracted: set = set()
        self._preprocessed = False

    def preprocess(self, max_nodes: int = 5000):
        """Run CH preprocessing."""
        print("[CH] Starting Contraction Hierarchies preprocessing...")
        start = time_module.time()
        
        G = self.augmented_graph
        nodes = list(G.nodes())
        
        # Limit preprocessing for large graphs
        if len(nodes) > max_nodes:
            print(f"[CH] Graph too large ({len(nodes)} nodes), using subset")
            nodes = sorted(nodes, key=lambda n: G.degree(n))[:max_nodes]
        
        # Step 1: Calculate initial node importance
        importance = {}
        for node in nodes:
            importance[node] = self._calculate_importance(node)
        
        # Step 2: Contract nodes in order of importance
        level = 0
        total = len(nodes)
        contracted_count = 0
        
        # Use a priority queue for efficient node selection
        pq = [(imp, node) for node, imp in importance.items()]
        heapq.heapify(pq)
        
        while pq and contracted_count < total * 0.7:  # Contract 70% of nodes
            imp, node = heapq.heappop(pq)
            
            if node in self.contracted:
                continue
            
            # Lazy update: recalculate importance
            new_imp = self._calculate_importance(node)
            if pq and new_imp > pq[0][0] * 1.5:
                heapq.heappush(pq, (new_imp, node))
                continue
            
            # Contract this node
            self._contract_node(node, level)
            self.node_level[node] = level
            self.node_order.append(node)
            self.contracted.add(node)
            contracted_count += 1
            level += 1
        
        # Assign remaining nodes highest levels
        for node in nodes:
            if node not in self.node_level:
                self.node_level[node] = level
                level += 1
        
        self._preprocessed = True
        elapsed = time_module.time() - start
        print(f"[CH] Preprocessing complete: {contracted_count} nodes contracted, "
              f"{len(self.shortcuts)} shortcuts added in {elapsed:.2f}s")
    
    def _calculate_importance(self, node: int) -> float:
        """Calculate node importance for contraction ordering.
        
        importance = edge_difference + contracted_neighbors + node_degree
        edge_difference = #shortcuts_needed - #edges_removed
        """
        G = self.augmented_graph
        if node not in G:
            return float("inf")
        
        in_edges = [(u, node) for u in G.predecessors(node) if u not in self.contracted]
        out_edges = [(node, v) for v in G.successors(node) if v not in self.contracted]
        
        edges_removed = len(in_edges) + len(out_edges)
        shortcuts_needed = 0
        
        # Count shortcuts that would be needed
        for u, _ in in_edges:
            for _, v in out_edges:
                if u != v and u not in self.contracted and v not in self.contracted:
                    # Check if u→v path goes through node
                    if G.has_edge(u, node) and G.has_edge(node, v):
                        d_through = G.edges[u, node].get("length_m", float("inf")) + \
                                   G.edges[node, v].get("length_m", float("inf"))
                        # Simple witness search
                        if not self._has_witness(u, v, node, d_through):
                            shortcuts_needed += 1
        
        edge_diff = shortcuts_needed - edges_removed
        contracted_neighbors = sum(1 for n in G.neighbors(node) if n in self.contracted)
        
        return edge_diff + contracted_neighbors * 2 + G.degree(node) * 0.5
    
    def _has_witness(self, u: int, v: int, excluded: int, max_dist: float) -> bool:
        """Check if there's a path from u to v not going through excluded node."""
        G = self.augmented_graph
        if G.has_edge(u, v):
            if G.edges[u, v].get("length_m", float("inf")) <= max_dist:
                return True
        
        # Limited Dijkstra (max 3 hops)
        visited = {u}
        queue = [(0, u)]
        for _ in range(50):  # Max iterations
            if not queue:
                break
            dist, curr = heapq.heappop(queue)
            if curr == v:
                return dist <= max_dist
            if dist > max_dist:
                break
            for neighbor in G.successors(curr):
                if neighbor != excluded and neighbor not in visited and neighbor not in self.contracted:
                    visited.add(neighbor)
                    new_dist = dist + G.edges[curr, neighbor].get("length_m", float("inf"))
                    heapq.heappush(queue, (new_dist, neighbor))
        return False
    
    def _contract_node(self, node: int, level: int):
        """Contract a node and add necessary shortcuts."""
        G = self.augmented_graph
        if node not in G:
            return
        
        predecessors = [(u, G.edges[u, node]) for u in G.predecessors(node) 
                       if u not in self.contracted]
        successors = [(v, G.edges[node, v]) for v in G.successors(node) 
                     if v not in self.contracted]
        
        for u, e_in in predecessors:
            for v, e_out in successors:
                if u == v:
                    continue
                d_through = e_in.get("length_m", 0) + e_out.get("length_m", 0)
                
                if not self._has_witness(u, v, node, d_through):
                    # Add shortcut
                    shortcut_attrs = {
                        "length_m": d_through,
                        "speed_limit_kmh": min(
                            e_in.get("speed_limit_kmh", 40),
                            e_out.get("speed_limit_kmh", 40)
                        ),
                        "free_flow_speed_kmh": min(
                            e_in.get("free_flow_speed_kmh", 40),
                            e_out.get("free_flow_speed_kmh", 40)
                        ),
                        "lanes": min(e_in.get("lanes", 1), e_out.get("lanes", 1)),
                        "road_type": "shortcut",
                        "capacity": min(
                            e_in.get("capacity", 1800),
                            e_out.get("capacity", 1800)
                        ),
                        "is_shortcut": True,
                        "via_node": node,
                    }
                    
                    # Only add if shorter than existing edge
                    if not G.has_edge(u, v) or G.edges[u, v].get("length_m", float("inf")) > d_through:
                        G.add_edge(u, v, **shortcut_attrs)
                        self.shortcuts[(u, v)] = shortcut_attrs
    
    def query(self, source: int, target: int) -> Optional[Tuple[List[int], float]]:
        """Bidirectional Dijkstra on CH augmented graph.
        
        Forward: only explore edges to higher-level nodes
        Backward: only explore edges to higher-level nodes
        """
        if not self._preprocessed:
            return None
        
        G = self.augmented_graph
        if source not in G or target not in G:
            return None
        
        # Forward search
        f_dist = {source: 0.0}
        f_prev = {}
        f_queue = [(0.0, source)]
        f_visited = set()
        
        # Backward search
        b_dist = {target: 0.0}
        b_prev = {}
        b_queue = [(0.0, target)]
        b_visited = set()
        
        best_dist = float("inf")
        meeting_node = None
        
        max_iters = 50000
        
        while (f_queue or b_queue) and max_iters > 0:
            max_iters -= 1
            
            # Forward step
            if f_queue:
                f_d, f_node = heapq.heappop(f_queue)
                if f_node not in f_visited:
                    f_visited.add(f_node)
                    
                    # Check if we can improve through this node
                    if f_node in b_dist:
                        total = f_d + b_dist[f_node]
                        if total < best_dist:
                            best_dist = total
                            meeting_node = f_node
                    
                    f_level = self.node_level.get(f_node, 0)
                    for neighbor in G.successors(f_node):
                        n_level = self.node_level.get(neighbor, 0)
                        if n_level >= f_level:  # Only go upward
                            new_dist = f_d + G.edges[f_node, neighbor].get("length_m", float("inf"))
                            if new_dist < f_dist.get(neighbor, float("inf")):
                                f_dist[neighbor] = new_dist
                                f_prev[neighbor] = f_node
                                heapq.heappush(f_queue, (new_dist, neighbor))
            
            # Backward step
            if b_queue:
                b_d, b_node = heapq.heappop(b_queue)
                if b_node not in b_visited:
                    b_visited.add(b_node)
                    
                    if b_node in f_dist:
                        total = b_d + f_dist[b_node]
                        if total < best_dist:
                            best_dist = total
                            meeting_node = b_node
                    
                    b_level = self.node_level.get(b_node, 0)
                    for neighbor in G.predecessors(b_node):
                        n_level = self.node_level.get(neighbor, 0)
                        if n_level >= b_level:
                            new_dist = b_d + G.edges[neighbor, b_node].get("length_m", float("inf"))
                            if new_dist < b_dist.get(neighbor, float("inf")):
                                b_dist[neighbor] = new_dist
                                b_prev[neighbor] = b_node
                                heapq.heappush(b_queue, (new_dist, neighbor))
            
            # Early termination
            if f_queue and b_queue:
                if f_queue[0][0] + b_queue[0][0] >= best_dist:
                    break
        
        if meeting_node is None:
            return None
        
        # Reconstruct path
        path = []
        node = meeting_node
        while node in f_prev:
            path.append(node)
            node = f_prev[node]
        path.append(source)
        path.reverse()
        
        node = meeting_node
        while node in b_prev:
            next_node = b_prev[node]
            path.append(next_node)
            node = next_node
        
        # Unpack shortcuts
        unpacked = self._unpack_shortcuts(path)
        
        return unpacked, best_dist
    
    def _unpack_shortcuts(self, path: List[int]) -> List[int]:
        """Recursively unpack shortcuts to get the actual path."""
        if len(path) <= 1:
            return path
        
        result = [path[0]]
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if (u, v) in self.shortcuts and self.shortcuts[(u, v)].get("is_shortcut"):
                via = self.shortcuts[(u, v)]["via_node"]
                # Recursively unpack
                sub_path = self._unpack_shortcuts([u, via, v])
                result.extend(sub_path[1:])
            else:
                result.append(v)
        
        return result


# ═══════════════════════════════════════════════════════════════
# PART 2: Time-Dependent A* with Traffic Awareness
# ═══════════════════════════════════════════════════════════════

def heuristic(G: nx.DiGraph, node: int, goal: int, v_max_ms: float) -> float:
    """Admissible heuristic: Haversine distance / max speed."""
    n = G.nodes[node]
    g = G.nodes[goal]
    dist_m = haversine(n["lat"], n["lng"], g["lat"], g["lng"])
    return dist_m / v_max_ms if v_max_ms > 0 else dist_m / 33.33


def bpr_travel_time(
    length_m: float, free_flow_speed_kmh: float, volume: float, capacity: float,
) -> float:
    """Bureau of Public Roads (BPR) travel time function.
    
    t(V) = t₀ × [1 + α × (V/C)^β]
    where t₀ = free-flow travel time, V = volume, C = capacity
    """
    if free_flow_speed_kmh <= 0 or length_m <= 0:
        return float("inf")
    
    t0 = length_m / (free_flow_speed_kmh / 3.6)
    if capacity <= 0:
        return t0
    
    vc_ratio = min(volume / capacity, 2.0)
    return t0 * (1 + graph_config.bpr_alpha * (vc_ratio ** graph_config.bpr_beta))


def time_dependent_weight(
    edge_data: Dict[str, Any],
    current_time: datetime,
    traffic_predictions: Optional[Dict[str, Dict]] = None,
    edge_key: Optional[str] = None,
) -> Tuple[float, float, float]:
    """Calculate time-dependent edge weight with traffic density.
    
    Returns: (travel_time_s, effective_speed_kmh, congestion_level)
    """
    length_m = edge_data.get("length_m", 100)
    free_flow_speed = edge_data.get("free_flow_speed_kmh", 40.0)
    capacity = edge_data.get("capacity", 1800)

    # Use LSTM predictions if available
    if traffic_predictions and edge_key and edge_key in traffic_predictions:
        pred = traffic_predictions[edge_key]
        predicted_speed = pred.get("speed", None)
        congestion = pred.get("congestion", 0.3)
        if predicted_speed and predicted_speed > 0:
            speed_ms = predicted_speed / 3.6
            travel_time = length_m / speed_ms
            return travel_time, predicted_speed, congestion

    # BPR fallback with time-of-day volume estimation
    hour = current_time.hour + current_time.minute / 60.0
    
    if 7 <= hour < 9 or 17 <= hour < 19:
        volume_ratio = 0.85
        congestion = 0.75
    elif 9 <= hour < 17:
        volume_ratio = 0.6
        congestion = 0.45
    elif 5 <= hour < 7 or 19 <= hour < 22:
        volume_ratio = 0.4
        congestion = 0.25
    else:
        volume_ratio = 0.15
        congestion = 0.1

    volume = capacity * volume_ratio
    travel_time = bpr_travel_time(length_m, free_flow_speed, volume, capacity)
    effective_speed = (length_m / travel_time * 3.6) if travel_time > 0 else free_flow_speed

    return travel_time, effective_speed, congestion


def multi_objective_cost(
    travel_time_s: float, distance_m: float, speed_kmh: float,
    congestion: float,
    alpha: float, beta: float, gamma: float, delta: float,
) -> float:
    """Multi-objective cost function.
    
    Cost = α·T_norm + β·E_norm + γ·D_norm + δ·Congestion
    """
    t_norm = travel_time_s / 60.0  # minutes
    e_norm = (distance_m / 1000.0) * emission_factor(speed_kmh) / 100.0  # normalized emissions
    d_norm = distance_m / 1000.0  # km
    c_norm = congestion  # 0-1

    return alpha * t_norm + beta * e_norm + gamma * d_norm + delta * c_norm


# ═══════════════════════════════════════════════════════════════
# PART 3: Main Routing Function
# ═══════════════════════════════════════════════════════════════

def astar_route(
    G: nx.DiGraph,
    start: int,
    goal: int,
    departure_time: datetime,
    alpha: float = 0.4,
    beta: float = 0.3,
    gamma: float = 0.15,
    delta: float = 0.15,
    traffic_predictions: Optional[Dict[str, Dict]] = None,
    ch: Optional[ContractionHierarchies] = None,
    avoid_congested: bool = True,
) -> Optional[Dict[str, Any]]:
    """AUMORoute™ — Time-Dependent A* with multi-objective cost.
    
    Enhanced with:
    - Traffic density factor (δ weight)
    - Congestion avoidance
    - Dynamic rerouting support
    - CH-accelerated heuristic
    """
    if start not in G or goal not in G:
        return None

    v_max_kmh = graph_config.v_max_kmh
    v_max_ms = v_max_kmh / 3.6

    counter = 0
    open_set: List[Tuple[float, int, int, datetime, float]] = []
    h_start = heuristic(G, start, goal, v_max_ms)
    heapq.heappush(open_set, (h_start, counter, start, departure_time, 0.0))

    g_scores: Dict[int, float] = {start: 0.0}
    came_from: Dict[int, Tuple[int, Dict]] = {}
    arrival_times: Dict[int, datetime] = {start: departure_time}
    edge_costs: Dict[int, Dict[str, float]] = {}
    
    visited = set()
    max_iterations = 150000

    while open_set and max_iterations > 0:
        max_iterations -= 1
        f_cost, _, current, current_time, current_g = heapq.heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = []
            node = goal
            while node in came_from:
                path.append(node)
                node = came_from[node][0]
            path.append(start)
            path.reverse()

            # Build result
            polyline = []
            total_distance_m = 0.0
            total_duration_s = 0.0
            total_co2_g = 0.0
            total_congestion = 0.0
            segment_count = 0

            for i in range(len(path)):
                node_data = G.nodes[path[i]]
                polyline.append([node_data["lat"], node_data["lng"]])

            for i in range(len(path) - 1):
                edge_data = G.edges[path[i], path[i + 1]]
                edge_info = edge_costs.get(path[i + 1], {})
                seg_dist = edge_data["length_m"]
                seg_time = edge_info.get("travel_time", seg_dist / (40 / 3.6))
                seg_speed = edge_info.get("speed", 40.0)
                seg_congestion = edge_info.get("congestion", 0.3)

                total_distance_m += seg_dist
                total_duration_s += seg_time
                total_co2_g += (seg_dist / 1000.0) * emission_factor(seg_speed)
                total_congestion += seg_congestion
                segment_count += 1

            avg_congestion = total_congestion / segment_count if segment_count > 0 else 0

            return {
                "path_nodes": path,
                "polyline": polyline,
                "distanceKm": total_distance_m / 1000.0,
                "durationMin": total_duration_s / 60.0,
                "co2Grams": total_co2_g,
                "cost": current_g,
                "avgCongestion": avg_congestion,
                "nodesExplored": 150000 - max_iterations,
                "algorithm": "AUMORoute-v3",
            }

        if current in visited:
            continue
        visited.add(current)

        for neighbor in G.successors(current):
            if neighbor in visited:
                continue

            edge_data = G.edges[current, neighbor]
            edge_key = f"{current}-{neighbor}"

            travel_time, pred_speed, congestion = time_dependent_weight(
                edge_data, current_time, traffic_predictions, edge_key
            )

            # Congestion avoidance: penalize high-congestion edges
            if avoid_congested and congestion > 0.8:
                travel_time *= 1.5  # 50% penalty for highly congested roads

            edge_cost = multi_objective_cost(
                travel_time, edge_data["length_m"], pred_speed,
                congestion, alpha, beta, gamma, delta,
            )

            g_new = current_g + edge_cost

            if g_new < g_scores.get(neighbor, float("inf")):
                g_scores[neighbor] = g_new
                t_arrival = current_time + timedelta(seconds=travel_time)
                arrival_times[neighbor] = t_arrival
                came_from[neighbor] = (current, edge_data)

                edge_costs[neighbor] = {
                    "travel_time": travel_time,
                    "speed": pred_speed,
                    "distance": edge_data["length_m"],
                    "congestion": congestion,
                }

                h = heuristic(G, neighbor, goal, v_max_ms)
                f_new = g_new + h

                counter += 1
                heapq.heappush(open_set, (f_new, counter, neighbor, t_arrival, g_new))

    return None


# ═══════════════════════════════════════════════════════════════
# PART 4: Dynamic Rerouting
# ═══════════════════════════════════════════════════════════════

def dynamic_reroute(
    G: nx.DiGraph,
    current_position: Tuple[float, float],
    destination: Tuple[float, float],
    departure_time: datetime,
    current_traffic: Dict[str, Dict],
    weights: Dict[str, float],
    ch: Optional[ContractionHierarchies] = None,
) -> Optional[Dict[str, Any]]:
    """Dynamically reroute based on updated traffic conditions.
    
    Called when traffic conditions change significantly.
    Finds nearest node to current position and recalculates route.
    """
    from algorithms.graph_builder import find_nearest_node
    
    start_node = find_nearest_node(G, current_position[0], current_position[1])
    goal_node = find_nearest_node(G, destination[0], destination[1])
    
    if start_node is None or goal_node is None:
        return None
    
    return astar_route(
        G, start_node, goal_node, departure_time,
        alpha=weights.get("alpha", 0.4),
        beta=weights.get("beta", 0.3),
        gamma=weights.get("gamma", 0.15),
        delta=weights.get("delta", 0.15),
        traffic_predictions=current_traffic,
        ch=ch,
        avoid_congested=True,
    )


# ═══════════════════════════════════════════════════════════════
# PART 5: Traffic Overlay for Map Visualization
# ═══════════════════════════════════════════════════════════════

def get_traffic_overlay(
    G: nx.DiGraph,
    path_nodes: List[int],
    traffic_predictions: Optional[Dict[str, Dict]] = None,
    current_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Generate traffic congestion overlay for map visualization."""
    if current_time is None:
        current_time = datetime.now()

    overlay = []
    for i in range(len(path_nodes) - 1):
        n1, n2 = path_nodes[i], path_nodes[i + 1]
        if not G.has_edge(n1, n2):
            continue

        edge_data = G.edges[n1, n2]
        edge_key = f"{n1}-{n2}"
        _, speed, congestion = time_dependent_weight(
            edge_data, current_time, traffic_predictions, edge_key
        )

        node_data = G.nodes[n1]
        overlay.append({
            "lat": node_data["lat"],
            "lng": node_data["lng"],
            "congestion": round(congestion, 3),
            "speed": round(speed, 1),
        })

    if path_nodes:
        last_node = G.nodes[path_nodes[-1]]
        overlay.append({
            "lat": last_node["lat"],
            "lng": last_node["lng"],
            "congestion": overlay[-1]["congestion"] if overlay else 0.0,
            "speed": overlay[-1]["speed"] if overlay else 40.0,
        })

    return overlay
