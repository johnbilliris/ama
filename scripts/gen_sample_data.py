"""Generate sample road network and population data JSON files."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# NODES (50)
# ---------------------------------------------------------------------------
# (id, name, lat, lng, type, is_assembly_area)
NODES_RAW = [
    # --- Cairns Urban Area (8 nodes) ---
    ("node-001", "Cairns CBD", -16.9186, 145.7781, "intersection", False),
    ("node-002", "Cairns North", -16.8780, 145.7554, "intersection", False),
    ("node-003", "Smithfield", -16.8333, 145.6950, "intersection", False),
    ("node-004", "Earlville", -16.9470, 145.7350, "intersection", False),
    ("node-005", "Edmonton", -17.0167, 145.7333, "intersection", False),
    ("node-006", "Mount Sheridan", -16.9800, 145.7350, "intersection", False),
    ("node-007", "Redlynch", -16.8800, 145.6870, "intersection", False),
    ("node-008", "Barron Gorge Junction", -16.8520, 145.6600, "intersection", False),
    # --- Northern Beaches to Port Douglas (6 nodes) ---
    ("node-009", "Trinity Beach", -16.7833, 145.6917, "intersection", False),
    ("node-010", "Palm Cove", -16.7450, 145.6700, "intersection", False),
    ("node-011", "Ellis Beach", -16.7200, 145.6350, "intersection", False),
    ("node-012", "Wangetti", -16.6550, 145.5700, "intersection", False),
    ("node-013", "Craiglie Junction", -16.5300, 145.4700, "intersection", False),
    ("node-014", "Port Douglas", -16.4833, 145.4500, "intersection", True),
    # --- Mossman / Daintree (7 nodes) ---
    ("node-015", "Mossman", -16.4589, 145.3726, "intersection", False),
    ("node-016", "Rex Range Junction", -16.5500, 145.3800, "intersection", False),
    ("node-017", "Daintree Ferry", -16.2667, 145.4083, "intersection", False),
    ("node-018", "Daintree Village", -16.2500, 145.4167, "intersection", False),
    ("node-019", "Cow Bay", -16.2400, 145.4300, "intersection", False),
    ("node-020", "Cape Tribulation", -16.1000, 145.4667, "intersection", False),
    ("node-021", "Wujal Wujal", -15.9167, 145.3333, "intersection", False),
    # --- Cooktown Area (3 nodes) ---
    ("node-022", "Rossville", -15.7500, 145.2300, "intersection", False),
    ("node-023", "Cooktown", -15.4748, 145.2467, "intersection", False),
    ("node-024", "Hope Vale", -15.3000, 145.1200, "intersection", False),
    # --- Atherton Tablelands (14 nodes) ---
    ("node-025", "Kuranda", -16.8167, 145.6333, "intersection", False),
    ("node-026", "Speewah", -16.8400, 145.6100, "intersection", False),
    ("node-027", "Koah", -16.8500, 145.5500, "intersection", False),
    ("node-028", "Mareeba", -16.9933, 145.4222, "intersection", True),
    ("node-029", "Mount Molloy", -16.6833, 145.3333, "intersection", False),
    ("node-030", "Walkamin", -17.1333, 145.4333, "intersection", False),
    ("node-031", "Tolga", -17.2000, 145.4700, "intersection", False),
    ("node-032", "Atherton", -17.2686, 145.4847, "intersection", True),
    ("node-033", "Yungaburra", -17.2667, 145.5833, "intersection", False),
    ("node-034", "Malanda", -17.3500, 145.5833, "intersection", False),
    ("node-035", "Herberton", -17.3833, 145.3833, "intersection", False),
    ("node-036", "Ravenshoe", -17.6000, 145.4833, "intersection", False),
    ("node-037", "Millaa Millaa", -17.5000, 145.6167, "intersection", False),
    ("node-038", "Kairi", -17.2100, 145.5500, "intersection", False),
    # --- South - Bruce Highway Corridor (9 nodes) ---
    ("node-039", "Gordonvale", -17.0833, 145.7833, "intersection", False),
    ("node-040", "Gillies Range Junction", -17.1000, 145.7200, "intersection", False),
    ("node-041", "Babinda", -17.3333, 145.9167, "intersection", False),
    ("node-042", "Innisfail", -17.5236, 146.0292, "intersection", True),
    ("node-043", "South Johnstone", -17.5950, 146.0000, "intersection", False),
    ("node-044", "Mourilyan", -17.5800, 146.0500, "intersection", False),
    ("node-045", "Mission Beach", -17.8667, 146.1000, "endpoint", False),
    ("node-046", "Tully", -17.9333, 145.9333, "intersection", False),
    ("node-047", "Cardwell", -18.2667, 146.0333, "endpoint", False),
    # --- Other connecting nodes (3 nodes) ---
    ("node-048", "Palmerston Highway Junction", -17.5200, 145.7500, "intersection", False),
    ("node-049", "Lake Eacham", -17.2900, 145.6200, "intersection", False),
    ("node-050", "Lakeland", -15.8700, 144.8600, "intersection", False),
]

# Build coordinate lookup
COORDS: dict[str, tuple[float, float]] = {}
for nid, _name, lat, lng, *_ in NODES_RAW:
    COORDS[nid] = (lat, lng)


def nid(idx: int) -> str:
    return f"node-{idx:03d}"


# ---------------------------------------------------------------------------
# EDGES  (from_idx, to_idx, name, capacity, surface, access, road_factor)
# road_factor multiplies straight-line distance to approximate road distance
# ---------------------------------------------------------------------------
EDGES_RAW: list[tuple] = [
    # =====================================================================
    # CAPTAIN COOK HIGHWAY — Cairns CBD northward to Port Douglas
    # =====================================================================
    (1, 2, "Mulgrave Road North", 1800, "sealed", ["wheelchair_accessible"], 1.2),
    (2, 3, "Captain Cook Highway", 1500, "sealed", ["wheelchair_accessible"], 1.3),
    (3, 9, "Captain Cook Highway North", 1200, "sealed", ["wheelchair_accessible"], 1.2),
    (9, 10, "Captain Cook Highway North", 1200, "sealed", ["wheelchair_accessible"], 1.2),
    (10, 11, "Captain Cook Highway North", 1000, "sealed", [], 1.3),
    (11, 12, "Captain Cook Highway North", 1000, "sealed", [], 1.4),
    (12, 13, "Captain Cook Highway North", 1000, "sealed", [], 1.3),
    (13, 14, "Port Douglas Road", 1200, "sealed", ["wheelchair_accessible"], 1.2),
    # =====================================================================
    # PORT DOUGLAS / MOSSMAN / DAINTREE
    # =====================================================================
    (13, 15, "Captain Cook Highway West", 1000, "sealed", [], 1.2),
    (14, 15, "Davidson Street", 800, "sealed", ["wheelchair_accessible"], 1.3),
    (15, 17, "Mossman-Daintree Road", 800, "sealed", [], 1.2),
    (15, 16, "Rex Range Road South", 600, "sealed", [], 1.3),
    (17, 18, "Daintree Village Road", 600, "sealed", [], 1.2),
    (17, 19, "Cape Tribulation Road South", 400, "sealed", [], 1.3),
    (18, 19, "Daintree-Cow Bay Road", 400, "sealed", [], 1.4),
    (19, 20, "Cape Tribulation Road North", 400, "sealed", [], 1.3),
    (20, 21, "Bloomfield Track South", 100, "unsealed", [], 1.8),
    # =====================================================================
    # COOKTOWN CORRIDOR
    # =====================================================================
    (21, 22, "Bloomfield Track North", 200, "unsealed", [], 1.5),
    (22, 23, "Cooktown Development Road South", 600, "sealed", [], 1.3),
    (23, 24, "Hope Vale Road", 400, "unsealed", [], 1.2),
    # =====================================================================
    # CAIRNS LOCAL NETWORK
    # =====================================================================
    (1, 4, "Mulgrave Road South", 2000, "sealed", ["wheelchair_accessible"], 1.2),
    (4, 6, "Bruce Highway South Section A", 1500, "sealed", ["wheelchair_accessible"], 1.2),
    (6, 5, "Bruce Highway South Section B", 1500, "sealed", ["wheelchair_accessible"], 1.2),
    (2, 7, "Redlynch Intake Road", 1200, "sealed", [], 1.3),
    (7, 8, "Barron Gorge Road", 800, "sealed", [], 1.4),
    (3, 7, "Kamerunga Road", 1000, "sealed", [], 1.2),
    (1, 7, "Cairns Western Arterial Road", 1000, "sealed", [], 1.3),
    (4, 5, "Edmonton Drive", 1200, "sealed", [], 1.2),
    (2, 4, "Sheridan Street South", 1500, "sealed", ["wheelchair_accessible"], 1.2),
    (3, 8, "Smithfield-Barron Gorge Road", 800, "sealed", [], 1.3),
    (1, 3, "Cairns Western Arterial North", 1200, "sealed", ["wheelchair_accessible"], 1.4),
    (8, 9, "Lake Placid-Trinity Beach Road", 600, "sealed", [], 1.4),
    (2, 9, "Cairns Northern Access Road", 800, "sealed", [], 1.5),
    (6, 39, "Mount Sheridan-Gordonvale Road", 1000, "sealed", [], 1.2),
    # =====================================================================
    # KENNEDY HIGHWAY — Cairns to Mareeba via Kuranda Range
    # =====================================================================
    (8, 25, "Kuranda Range Road", 600, "sealed", [], 1.8),
    (25, 26, "Kennedy Highway Section A", 600, "sealed", [], 1.3),
    (26, 27, "Kennedy Highway Section B", 600, "sealed", [], 1.3),
    (27, 28, "Kennedy Highway Section C", 800, "sealed", [], 1.3),
    (25, 27, "Speewah Bypass Road", 400, "unsealed", [], 1.5),
    # =====================================================================
    # REX RANGE / MOSSMAN TO TABLELANDS
    # =====================================================================
    (16, 29, "Mulligan Highway Section A", 600, "sealed", [], 1.3),
    (29, 28, "Mulligan Highway Section B", 800, "sealed", [], 1.2),
    # =====================================================================
    # MULLIGAN HIGHWAY NORTH — inland to Cooktown
    # =====================================================================
    (29, 50, "Mulligan Highway North", 600, "sealed", [], 1.2),
    (50, 23, "Cooktown Development Road", 600, "sealed", [], 1.2),
    # =====================================================================
    # TABLELANDS NETWORK
    # =====================================================================
    (28, 30, "Kennedy Highway South Section A", 800, "sealed", [], 1.2),
    (30, 31, "Kennedy Highway South Section B", 800, "sealed", [], 1.2),
    (31, 32, "Atherton-Tolga Road", 1000, "sealed", ["wheelchair_accessible"], 1.2),
    (32, 33, "Gillies Highway West Section A", 800, "sealed", [], 1.3),
    (33, 34, "Malanda-Yungaburra Road", 800, "sealed", [], 1.2),
    (34, 37, "Millaa Millaa Road", 600, "sealed", [], 1.3),
    (37, 36, "Millaa Millaa-Ravenshoe Road", 600, "sealed", [], 1.3),
    (32, 35, "Herberton Road", 600, "sealed", [], 1.3),
    (35, 36, "Herberton-Ravenshoe Road", 600, "sealed", [], 1.3),
    (33, 49, "Lake Eacham Road", 600, "sealed", [], 1.2),
    (38, 33, "Kairi-Yungaburra Road", 600, "sealed", [], 1.2),
    (31, 38, "Tolga-Kairi Road", 600, "sealed", [], 1.2),
    (49, 34, "Lake Eacham-Malanda Road", 600, "sealed", [], 1.2),
    (32, 34, "Atherton-Malanda Direct Road", 800, "sealed", [], 1.3),
    (35, 34, "Wild River Road", 400, "unsealed", [], 1.5),
    (30, 32, "Walkamin-Atherton Road", 600, "sealed", [], 1.3),
    (28, 31, "Mareeba-Tolga Road", 800, "sealed", [], 1.2),
    (28, 38, "Mareeba-Kairi Road", 600, "sealed", [], 1.3),
    (36, 46, "Tully Falls Road", 400, "unsealed", [], 1.6),
    (38, 49, "Kairi-Lake Eacham Road", 500, "sealed", [], 1.3),
    (31, 33, "Tolga-Yungaburra Road", 700, "sealed", [], 1.2),
    (32, 36, "Atherton-Ravenshoe Road", 600, "sealed", [], 1.3),
    (30, 35, "Walkamin-Herberton Road", 500, "sealed", [], 1.4),
    (34, 36, "Malanda-Ravenshoe Road", 500, "sealed", [], 1.3),
    # =====================================================================
    # GILLIES HIGHWAY
    # =====================================================================
    (39, 40, "Gillies Highway East Section", 600, "sealed", [], 1.5),
    (40, 33, "Gillies Highway West Section", 600, "sealed", [], 1.8),
    (40, 38, "Gillies Range-Kairi Connector", 500, "sealed", [], 1.5),
    (40, 30, "Gillies-Walkamin Connector", 500, "sealed", [], 1.4),
    # =====================================================================
    # BRUCE HIGHWAY SOUTH
    # =====================================================================
    (5, 39, "Bruce Highway South Section C", 1500, "sealed", ["wheelchair_accessible"], 1.2),
    (39, 41, "Bruce Highway South Section D", 1200, "sealed", ["wheelchair_accessible"], 1.2),
    (41, 42, "Bruce Highway South Section E", 1200, "sealed", ["wheelchair_accessible"], 1.2),
    (42, 43, "Bruce Highway South Section F", 1000, "sealed", [], 1.2),
    (43, 44, "South Johnstone-Mourilyan Road", 800, "sealed", [], 1.2),
    (42, 44, "Innisfail-Mourilyan Road", 1000, "sealed", [], 1.2),
    (44, 45, "Mission Beach Road North", 800, "sealed", [], 1.3),
    (43, 46, "Bruce Highway South Section G", 1000, "sealed", [], 1.2),
    (46, 47, "Bruce Highway South Section H", 1000, "sealed", ["wheelchair_accessible"], 1.2),
    (45, 46, "El Arish-Mission Beach Road", 600, "sealed", [], 1.3),
    # =====================================================================
    # PALMERSTON HIGHWAY
    # =====================================================================
    (42, 48, "Palmerston Highway East", 600, "sealed", [], 1.5),
    (48, 37, "Palmerston Highway West Section A", 600, "sealed", [], 1.5),
    (48, 49, "Palmerston Highway-Lake Eacham Road", 500, "sealed", [], 1.5),
    (48, 34, "Palmerston-Malanda Connector", 500, "sealed", [], 1.5),
    # =====================================================================
    # ADDITIONAL CROSS-CONNECTIONS
    # =====================================================================
    (27, 29, "Koah-Mount Molloy Road", 400, "unsealed", [], 1.4),
    (26, 8, "Speewah-Barron Road", 400, "sealed", [], 1.3),
    (10, 3, "Palm Cove-Smithfield Connector", 600, "sealed", [], 1.4),
    (41, 48, "Babinda-Palmerston Road", 500, "sealed", [], 1.5),
    (43, 45, "South Johnstone-Mission Beach Road", 600, "sealed", [], 1.4),
    (37, 49, "Millaa Millaa-Lake Eacham Road", 500, "sealed", [], 1.3),
    (50, 22, "Lakeland-Rossville Road", 400, "unsealed", [], 1.4),
    (7, 9, "Redlynch-Trinity Beach Road", 500, "sealed", [], 1.5),
    (5, 6, "Edmonton-Mount Sheridan Road", 1200, "sealed", [], 1.2),
    (4, 39, "Earlville-Gordonvale Road", 1000, "sealed", [], 1.3),
    (21, 50, "Wujal Wujal-Lakeland Road", 200, "unsealed", [], 1.6),
    (27, 16, "Koah-Rex Range Road", 400, "unsealed", [], 1.4),
    (44, 46, "Mourilyan-Tully Road", 800, "sealed", [], 1.3),
    (46, 45, "Tully-Mission Beach Road", 600, "sealed", [], 1.4),
    (1, 6, "Cairns Southern Bypass", 1500, "sealed", ["wheelchair_accessible"], 1.3),
    (7, 25, "Redlynch-Kuranda Road", 400, "sealed", [], 1.6),
    (25, 3, "Kuranda-Smithfield Connector", 500, "sealed", [], 1.5),
    (28, 32, "Mareeba-Atherton Direct", 1000, "sealed", ["wheelchair_accessible"], 1.2),
    (29, 15, "Mount Molloy-Mossman Road", 600, "sealed", [], 1.3),
    (40, 49, "Gillies Range-Lake Eacham Road", 400, "sealed", [], 1.5),
    # =====================================================================
    # ADDITIONAL EDGES — reaching ~120 target
    # =====================================================================
    (1, 5, "Bruce Highway Direct", 1500, "sealed", ["wheelchair_accessible"], 1.2),
    (9, 11, "Northern Beaches Bypass", 800, "sealed", [], 1.3),
    (13, 16, "Craiglie-Rex Range Road", 600, "sealed", [], 1.3),
    (17, 20, "Daintree Ferry-Cape Trib Direct", 300, "sealed", [], 1.5),
    (21, 23, "Coastal Track North", 150, "unsealed", [], 1.8),
    (26, 28, "Speewah-Mareeba Road", 500, "sealed", [], 1.3),
    (28, 35, "Mareeba-Herberton Road", 500, "sealed", [], 1.3),
    (30, 38, "Walkamin-Kairi Road", 500, "sealed", [], 1.2),
    (31, 49, "Tolga-Lake Eacham Road", 500, "sealed", [], 1.3),
    (40, 31, "Gillies Range-Tolga Connector", 400, "sealed", [], 1.5),
    (42, 46, "Innisfail-Tully Road", 1000, "sealed", [], 1.2),
    (45, 47, "Mission Beach-Cardwell Road", 600, "sealed", [], 1.3),
    (14, 16, "Port Douglas-Rex Range Road", 500, "sealed", [], 1.4),
    (2, 6, "Cairns North-Mount Sheridan Road", 800, "sealed", [], 1.3),
    (18, 20, "Daintree Village-Cape Trib Road", 400, "sealed", [], 1.4),
    (2, 8, "Cairns North-Barron Gorge Road", 600, "sealed", [], 1.4),
    (36, 47, "Ravenshoe-Cardwell Road", 400, "unsealed", [], 1.6),
]


def generate_road_network() -> dict:
    """Build the complete road network JSON structure."""
    # Build nodes
    nodes = []
    for nid_str, name, lat, lng, ntype, is_aa in NODES_RAW:
        nodes.append(
            {
                "id": nid_str,
                "name": name,
                "coordinates": {"lat": lat, "lng": lng},
                "type": ntype,
                "is_assembly_area": is_aa,
            }
        )

    # Deduplicate edges (keep first occurrence of each undirected pair)
    seen_pairs: set[tuple[int, int]] = set()
    clean_edges: list[tuple] = []
    for e in EDGES_RAW:
        pair = (min(e[0], e[1]), max(e[0], e[1]))
        if pair in seen_pairs or e[0] == e[1]:
            continue
        seen_pairs.add(pair)
        clean_edges.append(e)

    # Build edges with haversine distances
    edges = []
    for i, (f, t, name, cap, surface, access, rf) in enumerate(clean_edges, 1):
        fid = nid(f)
        tid = nid(t)
        lat1, lng1 = COORDS[fid]
        lat2, lng2 = COORDS[tid]
        straight = haversine(lat1, lng1, lat2, lng2)
        dist = round(straight * rf, 1)
        edges.append(
            {
                "id": f"edge-{i:03d}",
                "from_node": fid,
                "to_node": tid,
                "name": name,
                "distance_km": dist,
                "capacity_vehicles_per_hour": cap,
                "surface_type": surface,
                "accessibility_features": access,
                "closure_status": "open",
                "closure_reason": None,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lng1, lat1], [lng2, lat2]],
                },
            }
        )

    # Assembly areas
    assembly_areas = [
        {
            "assembly_area_id": "aa-001",
            "name": "Cairns Convention Centre",
            "coordinates": {"lat": -16.9220, "lng": 145.7740},
            "capacity_persons": 3000,
            "accessibility_features": [
                "wheelchair_accessible",
                "medical_facilities",
            ],
            "assigned_zones": [1, 2, 3],
            "node_id": "node-001",
        },
        {
            "assembly_area_id": "aa-002",
            "name": "Port Douglas Community Hall",
            "coordinates": {"lat": -16.4850, "lng": 145.4520},
            "capacity_persons": 1000,
            "accessibility_features": ["wheelchair_accessible"],
            "assigned_zones": [1, 2],
            "node_id": "node-014",
        },
        {
            "assembly_area_id": "aa-003",
            "name": "Atherton Showgrounds",
            "coordinates": {"lat": -17.2700, "lng": 145.4870},
            "capacity_persons": 2000,
            "accessibility_features": [
                "wheelchair_accessible",
                "medical_facilities",
                "helicopter_landing",
            ],
            "assigned_zones": [2, 3],
            "node_id": "node-032",
        },
        {
            "assembly_area_id": "aa-004",
            "name": "Innisfail Civic Centre",
            "coordinates": {"lat": -17.5250, "lng": 146.0310},
            "capacity_persons": 1500,
            "accessibility_features": [
                "wheelchair_accessible",
                "medical_facilities",
            ],
            "assigned_zones": [1, 2, 3],
            "node_id": "node-042",
        },
        {
            "assembly_area_id": "aa-005",
            "name": "Mareeba Rodeo Grounds",
            "coordinates": {"lat": -16.9950, "lng": 145.4250},
            "capacity_persons": 2500,
            "accessibility_features": [
                "wheelchair_accessible",
                "helicopter_landing",
            ],
            "assigned_zones": [2, 3],
            "node_id": "node-028",
        },
    ]

    # Validate references
    node_ids = {n["id"] for n in nodes}
    for e in edges:
        assert e["from_node"] in node_ids, f"Bad from_node: {e['from_node']}"
        assert e["to_node"] in node_ids, f"Bad to_node: {e['to_node']}"
    for a in assembly_areas:
        assert a["node_id"] in node_ids, f"Bad node_id: {a['node_id']}"

    return {
        "metadata": {
            "version": "1.0.0",
            "region": "Far North Queensland",
            "coordinate_system": "WGS84",
            "last_updated": "2026-04-16T00:00:00Z",
        },
        "nodes": nodes,
        "edges": edges,
        "assembly_areas": assembly_areas,
    }


def generate_population_data() -> dict:
    """Build the sample population JSON structure."""
    facilities = [
        {
            "facility_id": "fac-001",
            "name": "Cairns Aged Care Residence",
            "type": "aged_care",
            "coordinates": {"lat": -16.9300, "lng": 145.7700},
            "capacity": 80,
            "vulnerability_category": "elderly_aged_care",
            "special_considerations": ["wheelchair_users", "oxygen_supply"],
            "nearest_node_id": "node-001",
        },
        {
            "facility_id": "fac-002",
            "name": "TrinityCare Aged Care",
            "type": "aged_care",
            "coordinates": {"lat": -16.7900, "lng": 145.6900},
            "capacity": 60,
            "vulnerability_category": "elderly_aged_care",
            "special_considerations": ["wheelchair_users", "dementia_care"],
            "nearest_node_id": "node-009",
        },
        {
            "facility_id": "fac-003",
            "name": "Atherton Aged Care Facility",
            "type": "aged_care",
            "coordinates": {"lat": -17.2700, "lng": 145.4800},
            "capacity": 45,
            "vulnerability_category": "elderly_aged_care",
            "special_considerations": ["wheelchair_users"],
            "nearest_node_id": "node-032",
        },
        {
            "facility_id": "fac-004",
            "name": "Cairns Disability Support Centre",
            "type": "disability_care",
            "coordinates": {"lat": -16.9400, "lng": 145.7400},
            "capacity": 40,
            "vulnerability_category": "mobility_impaired",
            "special_considerations": [
                "wheelchair_users",
                "assisted_transport",
                "sensory_impairment",
            ],
            "nearest_node_id": "node-004",
        },
        {
            "facility_id": "fac-005",
            "name": "FNQ Disability Services Innisfail",
            "type": "disability_care",
            "coordinates": {"lat": -17.5300, "lng": 146.0300},
            "capacity": 25,
            "vulnerability_category": "mobility_impaired",
            "special_considerations": ["wheelchair_users", "assisted_transport"],
            "nearest_node_id": "node-042",
        },
        {
            "facility_id": "fac-006",
            "name": "Cairns Hospital",
            "type": "hospital",
            "coordinates": {"lat": -16.9200, "lng": 145.7720},
            "capacity": 531,
            "vulnerability_category": "medical_dependent",
            "special_considerations": [
                "critical_care_patients",
                "neonatal",
                "dialysis",
                "ventilator_dependent",
            ],
            "nearest_node_id": "node-001",
        },
        {
            "facility_id": "fac-007",
            "name": "Innisfail Hospital",
            "type": "hospital",
            "coordinates": {"lat": -17.5240, "lng": 146.0280},
            "capacity": 62,
            "vulnerability_category": "medical_dependent",
            "special_considerations": [
                "critical_care_patients",
                "dialysis",
            ],
            "nearest_node_id": "node-042",
        },
        {
            "facility_id": "fac-008",
            "name": "Atherton Hospital",
            "type": "hospital",
            "coordinates": {"lat": -17.2650, "lng": 145.4830},
            "capacity": 38,
            "vulnerability_category": "medical_dependent",
            "special_considerations": ["emergency_department"],
            "nearest_node_id": "node-032",
        },
        {
            "facility_id": "fac-009",
            "name": "Cairns State High School",
            "type": "school",
            "coordinates": {"lat": -16.9250, "lng": 145.7660},
            "capacity": 1200,
            "vulnerability_category": "children_schools_childcare",
            "special_considerations": ["minors", "bus_dependent"],
            "nearest_node_id": "node-001",
        },
        {
            "facility_id": "fac-010",
            "name": "Smithfield State High School",
            "type": "school",
            "coordinates": {"lat": -16.8350, "lng": 145.6930},
            "capacity": 950,
            "vulnerability_category": "children_schools_childcare",
            "special_considerations": ["minors", "bus_dependent"],
            "nearest_node_id": "node-003",
        },
        {
            "facility_id": "fac-011",
            "name": "Mossman State High School",
            "type": "school",
            "coordinates": {"lat": -16.4600, "lng": 145.3750},
            "capacity": 420,
            "vulnerability_category": "children_schools_childcare",
            "special_considerations": ["minors", "bus_dependent"],
            "nearest_node_id": "node-015",
        },
        {
            "facility_id": "fac-012",
            "name": "Edmonton Aged Care Village",
            "type": "aged_care",
            "coordinates": {"lat": -17.0200, "lng": 145.7350},
            "capacity": 55,
            "vulnerability_category": "elderly_aged_care",
            "special_considerations": [
                "wheelchair_users",
                "oxygen_supply",
                "limited_mobility",
            ],
            "nearest_node_id": "node-005",
        },
        {
            "facility_id": "fac-013",
            "name": "Mareeba Hospital",
            "type": "hospital",
            "coordinates": {"lat": -16.9950, "lng": 145.4250},
            "capacity": 30,
            "vulnerability_category": "medical_dependent",
            "special_considerations": ["emergency_department"],
            "nearest_node_id": "node-028",
        },
        {
            "facility_id": "fac-014",
            "name": "Gordonvale State School",
            "type": "school",
            "coordinates": {"lat": -17.0850, "lng": 145.7850},
            "capacity": 350,
            "vulnerability_category": "children_schools_childcare",
            "special_considerations": ["minors"],
            "nearest_node_id": "node-039",
        },
        {
            "facility_id": "fac-015",
            "name": "Tully Hospital",
            "type": "hospital",
            "coordinates": {"lat": -17.9340, "lng": 145.9350},
            "capacity": 24,
            "vulnerability_category": "medical_dependent",
            "special_considerations": ["emergency_department"],
            "nearest_node_id": "node-046",
        },
    ]

    population_density = [
        {
            "area_name": "Cairns CBD",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.7600, -16.9300],
                        [145.7950, -16.9300],
                        [145.7950, -16.9050],
                        [145.7600, -16.9050],
                        [145.7600, -16.9300],
                    ]
                ],
            },
            "population_estimate": 15000,
            "vulnerable_population_estimate": 2250,
        },
        {
            "area_name": "Cairns Northern Suburbs",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.7300, -16.9050],
                        [145.7800, -16.9050],
                        [145.7800, -16.8500],
                        [145.7300, -16.8500],
                        [145.7300, -16.9050],
                    ]
                ],
            },
            "population_estimate": 28000,
            "vulnerable_population_estimate": 4200,
        },
        {
            "area_name": "Cairns Southern Suburbs",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.7100, -17.0300],
                        [145.7900, -17.0300],
                        [145.7900, -16.9300],
                        [145.7100, -16.9300],
                        [145.7100, -17.0300],
                    ]
                ],
            },
            "population_estimate": 35000,
            "vulnerable_population_estimate": 5250,
        },
        {
            "area_name": "Northern Beaches",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.6500, -16.8000],
                        [145.7200, -16.8000],
                        [145.7200, -16.7000],
                        [145.6500, -16.7000],
                        [145.6500, -16.8000],
                    ]
                ],
            },
            "population_estimate": 12000,
            "vulnerable_population_estimate": 1800,
        },
        {
            "area_name": "Port Douglas - Mossman",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.3500, -16.5500],
                        [145.4800, -16.5500],
                        [145.4800, -16.4200],
                        [145.3500, -16.4200],
                        [145.3500, -16.5500],
                    ]
                ],
            },
            "population_estimate": 14500,
            "vulnerable_population_estimate": 2175,
        },
        {
            "area_name": "Atherton Tablelands",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.3500, -17.4000],
                        [145.6500, -17.4000],
                        [145.6500, -17.1000],
                        [145.3500, -17.1000],
                        [145.3500, -17.4000],
                    ]
                ],
            },
            "population_estimate": 22000,
            "vulnerable_population_estimate": 3300,
        },
        {
            "area_name": "Innisfail - Mission Beach",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.9000, -17.9000],
                        [146.1500, -17.9000],
                        [146.1500, -17.4500],
                        [145.9000, -17.4500],
                        [145.9000, -17.9000],
                    ]
                ],
            },
            "population_estimate": 18000,
            "vulnerable_population_estimate": 2700,
        },
        {
            "area_name": "Mareeba",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.3800, -17.0300],
                        [145.4700, -17.0300],
                        [145.4700, -16.9600],
                        [145.3800, -16.9600],
                        [145.3800, -17.0300],
                    ]
                ],
            },
            "population_estimate": 11000,
            "vulnerable_population_estimate": 1650,
        },
        {
            "area_name": "Gordonvale - Babinda",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.7500, -17.3500],
                        [145.9500, -17.3500],
                        [145.9500, -17.0500],
                        [145.7500, -17.0500],
                        [145.7500, -17.3500],
                    ]
                ],
            },
            "population_estimate": 8500,
            "vulnerable_population_estimate": 1275,
        },
        {
            "area_name": "Tully - Cardwell",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.8800, -18.3000],
                        [146.1000, -18.3000],
                        [146.1000, -17.8800],
                        [145.8800, -17.8800],
                        [145.8800, -18.3000],
                    ]
                ],
            },
            "population_estimate": 9500,
            "vulnerable_population_estimate": 1425,
        },
        {
            "area_name": "Daintree - Cape Tribulation",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.3500, -16.3000],
                        [145.5000, -16.3000],
                        [145.5000, -16.0500],
                        [145.3500, -16.0500],
                        [145.3500, -16.3000],
                    ]
                ],
            },
            "population_estimate": 1200,
            "vulnerable_population_estimate": 180,
        },
        {
            "area_name": "Cooktown",
            "boundary": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [145.2000, -15.5200],
                        [145.3000, -15.5200],
                        [145.3000, -15.4300],
                        [145.2000, -15.4300],
                        [145.2000, -15.5200],
                    ]
                ],
            },
            "population_estimate": 2600,
            "vulnerable_population_estimate": 390,
        },
    ]

    return {
        "metadata": {
            "version": "1.0.0",
            "region": "Far North Queensland",
            "last_updated": "2026-04-16T00:00:00Z",
        },
        "facilities": facilities,
        "population_density": population_density,
    }


def main() -> None:
    # --- Road Network ---
    rn = generate_road_network()
    rn_path = ROOT / "data" / "road-networks" / "far-north-qld-sample.json"
    rn_path.parent.mkdir(parents=True, exist_ok=True)
    rn_path.write_text(json.dumps(rn, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Road network: {len(rn['nodes'])} nodes, "
        f"{len(rn['edges'])} edges, "
        f"{len(rn['assembly_areas'])} assembly areas → {rn_path}"
    )

    # --- Population ---
    pop = generate_population_data()
    pop_path = ROOT / "data" / "population" / "sample-population.json"
    pop_path.parent.mkdir(parents=True, exist_ok=True)
    pop_path.write_text(json.dumps(pop, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Population: {len(pop['facilities'])} facilities, {len(pop['population_density'])} density areas → {pop_path}"
    )


if __name__ == "__main__":
    main()
