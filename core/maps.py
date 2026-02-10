# core/maps.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


@dataclass
class MarketPoint:
    name: str
    lat: float
    lon: float
    score: float
    note: str


# Minimal MVP coordinates (expand later)
CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "london": (51.5074, -0.1278),
    "manchester": (53.4808, -2.2426),
    "birmingham": (52.4862, -1.8904),
    "edinburgh": (55.9533, -3.1883),
    "dublin": (53.3498, -6.2603),
    "amsterdam": (52.3676, 4.9041),
    "berlin": (52.5200, 13.4050),
    "paris": (48.8566, 2.3522),
}


def resolve_city_center(city: str) -> Tuple[float, float]:
    c = (city or "").strip().lower()
    return CITY_COORDS.get(c, CITY_COORDS["london"])


def make_view_state(lat: float, lon: float, zoom: float = 5.2) -> Dict[str, float]:
    return {"latitude": float(lat), "longitude": float(lon), "zoom": float(zoom), "pitch": 0.0}


def make_demo_market_points(role: str, base_city: str) -> List[MarketPoint]:
    """
    MVP heuristic points only.
    Replace later with real job-volume + salary + competition.
    """
    role = (role or "").strip()
    base = (base_city or "").strip().lower()

    # Simple role weighting
    base_weight = 1.0
    if "engineer" in role.lower():
        base_weight = 1.1
    if "ml" in role.lower():
        base_weight = 1.15

    cities = [
        ("London", 0.95, "Largest market + most postings."),
        ("Manchester", 0.78, "Strong tech scene, lower competition than London."),
        ("Birmingham", 0.70, "Good generalist market."),
        ("Edinburgh", 0.74, "FinTech + data roles."),
        ("Dublin", 0.80, "Big tech presence."),
        ("Amsterdam", 0.77, "EU tech + English-friendly."),
        ("Berlin", 0.76, "Large startup ecosystem."),
        ("Paris", 0.72, "Big market but language can matter."),
    ]

    points: List[MarketPoint] = []
    for name, score, note in cities:
        lat, lon = resolve_city_center(name)
        # tiny nudge if base city matches
        bump = 0.04 if name.strip().lower() == base else 0.0
        points.append(MarketPoint(name=name, lat=lat, lon=lon, score=min(1.0, (score + bump) * base_weight), note=note))
    return points


def points_to_df(points: List[MarketPoint]) -> "pd.DataFrame":
    return pd.DataFrame([{"name": p.name, "lat": p.lat, "lon": p.lon, "score": p.score, "note": p.note} for p in points])


def tooltip_html() -> dict:
    return {"html": "<b>{name}</b><br/>Score: {score}<br/>{note}", "style": {"fontSize": "12px"}}
