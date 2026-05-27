"""
solver.py — KetKet Paket Backend
Handles OSRM distance/duration matrix fetching and OR-Tools TSP optimization.
"""

import requests
import math
from typing import List, Tuple, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

class Stop:
    """Represents a delivery stop (kurir position or package destination)."""
    def __init__(
        self,
        name: str,
        address: str,
        lat: float,
        lng: float,
        recipient: str = "",
        stop_id: Optional[str] = None,
    ):
        self.name = name
        self.address = address
        self.lat = lat
        self.lng = lng
        self.recipient = recipient
        self.stop_id = stop_id or name


# ---------------------------------------------------------------------------
# Dummy Surabaya Data (hardcoded, ready to run)
# ---------------------------------------------------------------------------

DUMMY_COURIER_POSITION = Stop(
    name="Posisi Kurir",
    address="Jl. Mulyorejo No. 15, Surabaya",
    lat=-7.2756,
    lng=112.7843,
    recipient="",
    stop_id="KURIR",
)

DUMMY_PACKAGES: List[Stop] = [
    Stop(
        name="Rumah 1",
        address="Jl. Klampis Anom No. 12, Surabaya",
        lat=-7.2869,
        lng=112.7932,
        recipient="Bpk. Slamet Rahardjo",
        stop_id="PKG_001",
    ),
    Stop(
        name="Rumah 2",
        address="Jl. Dharmahusada Indah Barat No. 5, Surabaya",
        lat=-7.2703,
        lng=112.7721,
        recipient="Ibu Dewi Kusuma",
        stop_id="PKG_002",
    ),
    Stop(
        name="Kantor Pusat",
        address="Jl. Basuki Rahmat No. 102, Surabaya",
        lat=-7.2637,
        lng=112.7522,
        recipient="Bpk. Hendra Wijaya",
        stop_id="PKG_003",
    ),
    Stop(
        name="Gudang Timur",
        address="Jl. Kenjeran No. 441, Surabaya",
        lat=-7.2452,
        lng=112.7998,
        recipient="Ibu Sari Indrawati",
        stop_id="PKG_004",
    ),
    Stop(
        name="Apartemen Waterplace",
        address="Jl. Citraland Boulevard, Surabaya",
        lat=-7.2941,
        lng=112.6892,
        recipient="Bpk. Doni Firmansyah",
        stop_id="PKG_005",
    ),
    Stop(
        name="Toko Elektronik",
        address="Jl. Pemuda No. 33, Surabaya",
        lat=-7.2575,
        lng=112.7488,
        recipient="Ibu Ratna Sari",
        stop_id="PKG_006",
    ),
    Stop(
        name="Perumahan Graha",
        address="Jl. Rungkut Madya No. 50, Surabaya",
        lat=-7.3201,
        lng=112.7814,
        recipient="Bpk. Agus Priyono",
        stop_id="PKG_007",
    ),
]


# ---------------------------------------------------------------------------
# OSRM Distance/Duration Matrix
# ---------------------------------------------------------------------------

OSRM_BASE_URL = "http://router.project-osrm.org/table/v1/driving"

def _build_coordinate_string(stops: List[Stop]) -> str:
    """Format coordinates as 'lng,lat;lng,lat;...' for OSRM."""
    return ";".join(f"{s.lng},{s.lat}" for s in stops)


def fetch_osrm_matrix(
    stops: List[Stop],
) -> Tuple[List[List[int]], List[List[int]]]:
    """
    Fetch real road-based distance (meters) and duration (seconds) matrices
    from the free public OSRM API.

    Returns:
        distance_matrix: N×N list of lists (meters, int)
        duration_matrix: N×N list of lists (seconds, int)

    Falls back to haversine straight-line distances if OSRM is unreachable.
    """
    coords = _build_coordinate_string(stops)
    url = f"{OSRM_BASE_URL}/{coords}"
    params = {
        "annotations": "distance,duration",
        "sources": "all",
        "destinations": "all",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != "Ok":
            raise ValueError(f"OSRM error: {data.get('message', 'unknown')}")

        # OSRM returns floats; convert to int
        raw_dist = data["distances"]
        raw_dur = data["durations"]

        n = len(stops)
        dist_matrix = []
        dur_matrix = []

        for i in range(n):
            dist_row = []
            dur_row = []
            for j in range(n):
                d = raw_dist[i][j]
                t = raw_dur[i][j]
                dist_row.append(int(d) if d is not None else 0)
                dur_row.append(int(t) if t is not None else 0)
            dist_matrix.append(dist_row)
            dur_matrix.append(dur_row)

        return dist_matrix, dur_matrix

    except Exception as exc:
        # Graceful fallback: haversine distances, assume 40 km/h avg speed
        print(f"[OSRM fallback] {exc}")
        return _haversine_matrix(stops)


def _haversine(s1: Stop, s2: Stop) -> int:
    """Straight-line distance in meters between two stops."""
    R = 6_371_000
    phi1, phi2 = math.radians(s1.lat), math.radians(s2.lat)
    dphi = math.radians(s2.lat - s1.lat)
    dlam = math.radians(s2.lng - s1.lng)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return int(2 * R * math.asin(math.sqrt(a)))


def _haversine_matrix(
    stops: List[Stop],
) -> Tuple[List[List[int]], List[List[int]]]:
    n = len(stops)
    dist_matrix = [[0] * n for _ in range(n)]
    dur_matrix = [[0] * n for _ in range(n)]
    speed_ms = 40_000 / 3600  # 40 km/h in m/s

    for i in range(n):
        for j in range(n):
            if i != j:
                d = _haversine(stops[i], stops[j])
                dist_matrix[i][j] = d
                dur_matrix[i][j] = int(d / speed_ms)

    return dist_matrix, dur_matrix


# ---------------------------------------------------------------------------
# OR-Tools TSP Solver
# ---------------------------------------------------------------------------

def solve_tsp(
    stops: List[Stop],
    dist_matrix: List[List[int]],
    depot_index: int = 0,
    time_limit_seconds: int = 10,
) -> Dict[str, Any]:
    """
    Solve TSP with Google OR-Tools.

    Args:
        stops:               All stops (index 0 = courier / depot).
        dist_matrix:         N×N integer distance matrix.
        depot_index:         Index of the starting point (courier position).
        time_limit_seconds:  OR-Tools search time budget.

    Returns dict with keys:
        route_indices   – ordered list of stop indices (starts and ends at depot)
        route_stops     – corresponding Stop objects (excl. depot duplicate at end)
        total_distance  – total route distance in meters
        status          – "optimal" | "feasible" | "no_solution"
    """
    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp
    except ImportError:
        # Fallback: nearest-neighbour greedy if OR-Tools not installed
        return _greedy_tsp(stops, dist_matrix, depot_index)

    n = len(stops)
    manager = pywrapcp.RoutingIndexManager(n, 1, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        i = manager.IndexToNode(from_idx)
        j = manager.IndexToNode(to_idx)
        return dist_matrix[i][j]

    transit_cb_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_idx)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = time_limit_seconds

    solution = routing.SolveWithParameters(search_params)

    if not solution:
        return _greedy_tsp(stops, dist_matrix, depot_index)

    # Extract route
    route_indices = []
    idx = routing.Start(0)
    while not routing.IsEnd(idx):
        route_indices.append(manager.IndexToNode(idx))
        idx = solution.Value(routing.NextVar(idx))
    route_indices.append(manager.IndexToNode(idx))  # back to depot

    total_distance = sum(
        dist_matrix[route_indices[i]][route_indices[i + 1]]
        for i in range(len(route_indices) - 1)
    )

    status = "optimal" if routing.status() == 1 else "feasible"

    return {
        "route_indices": route_indices,
        "route_stops": [stops[i] for i in route_indices[:-1]],  # excl. return
        "total_distance": total_distance,
        "status": status,
    }


def _greedy_tsp(
    stops: List[Stop],
    dist_matrix: List[List[int]],
    depot_index: int = 0,
) -> Dict[str, Any]:
    """Nearest-neighbour heuristic fallback when OR-Tools is unavailable."""
    n = len(stops)
    unvisited = set(range(n))
    unvisited.discard(depot_index)
    route = [depot_index]
    current = depot_index
    total = 0

    while unvisited:
        nearest = min(unvisited, key=lambda j: dist_matrix[current][j])
        total += dist_matrix[current][nearest]
        route.append(nearest)
        unvisited.discard(nearest)
        current = nearest

    total += dist_matrix[current][depot_index]
    route.append(depot_index)

    return {
        "route_indices": route,
        "route_stops": [stops[i] for i in route[:-1]],
        "total_distance": total,
        "status": "greedy",
    }


# ---------------------------------------------------------------------------
# Utility helpers used by app.py
# ---------------------------------------------------------------------------

def estimate_savings(
    original_stops: List[Stop],
    optimized_indices: List[int],
    dist_matrix: List[List[int]],
) -> Dict[str, Any]:
    """
    Compare naive sequential route vs optimised route.
    Returns distance saved (m), fuel saved (Rp), time saved (min).
    """
    n = len(original_stops)
    # Naive: visit in original list order 0→1→2→…→n-1→0
    naive_dist = sum(dist_matrix[i][i + 1] for i in range(n - 1)) + dist_matrix[n - 1][0]

    optimised_dist = sum(
        dist_matrix[optimized_indices[i]][optimized_indices[i + 1]]
        for i in range(len(optimized_indices) - 1)
    )

    saved_m = max(0, naive_dist - optimised_dist)
    # Fuel: assume 1 litre per 12 km, Rp 12.500/litre → Rp 1.042/km
    fuel_rp = int((saved_m / 1000) * 1_042)
    # Time: assume avg speed 25 km/h in city → 2.4 min/km
    time_min = int((saved_m / 1000) * 2.4)

    return {
        "distance_saved_m": saved_m,
        "distance_saved_km": round(saved_m / 1000, 1),
        "fuel_saved_rp": fuel_rp,
        "time_saved_min": time_min,
    }


def build_google_maps_url(destination: Stop) -> str:
    """Build a Google Maps turn-by-turn navigation URL for a destination."""
    return (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={destination.lat},{destination.lng}"
        f"&travelmode=driving"
    )
