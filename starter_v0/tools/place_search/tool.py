from __future__ import annotations

import math
from typing import Any

import requests

from tools._shared import TIMEOUT, err, fold_text

# OpenStreetMap usage policy requires a descriptive User-Agent identifying the app.
_HEADERS = {"User-Agent": "C401-ToolCallingLab-Demo/1.0"}
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Vietnamese-friendly category keywords -> OSM (key, value) tag filters.
_CATEGORY_TAGS: list[tuple[list[str], list[tuple[str, str]]]] = [
    (["bar", "pub", "quanbar"], [("amenity", "bar"), ("amenity", "pub")]),
    (["cafe", "caphe", "coffee"], [("amenity", "cafe")]),
    (
        ["vuichoi", "giaitri", "entertainment", "karaoke", "phim", "cinema", "raprap"],
        [("amenity", "cinema"), ("amenity", "nightclub"), ("leisure", "bowling_alley"), ("leisure", "amusement_arcade")],
    ),
    (["congvien", "park"], [("leisure", "park")]),
    (["anuong", "nhahang", "quanan", "doan", "food", "restaurant"], [("amenity", "restaurant"), ("amenity", "fast_food")]),
]
_DEFAULT_TAGS = [("amenity", "restaurant"), ("amenity", "cafe")]


def _resolve_tags(category: str) -> list[tuple[str, str]]:
    folded = fold_text(category).replace(" ", "")
    for keywords, tags in _CATEGORY_TAGS:
        if any(keyword in folded for keyword in keywords):
            return tags
    return _DEFAULT_TAGS


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _address(tags: dict[str, str]) -> str:
    parts = [tags.get("addr:housenumber", ""), tags.get("addr:street", ""), tags.get("addr:suburb", "")]
    return ", ".join(p for p in parts if p)


def find_places(location: str = "", category: str = "an uong", radius_km: float = 1.5, top_k: int = 5) -> dict[str, Any]:
    """Find restaurants/cafes/entertainment venues near a city, university, or landmark."""
    try:
        clean_location = location.strip()
        if not clean_location:
            return {
                "tool": "place_search",
                "status": "missing_location",
                "message": "Cần tên địa điểm/khu vực để tìm quanh đó. Hỏi lại người dùng.",
            }

        # Step 1: Resolve the location (city, university, landmark) to coordinates.
        geo_resp = requests.get(
            _NOMINATIM_URL,
            params={"q": clean_location, "format": "json", "limit": 1, "accept-language": "vi"},
            headers=_HEADERS,
            timeout=TIMEOUT,
        )
        geo_results = geo_resp.json()
        if not geo_results:
            return {
                "tool": "place_search",
                "location": location,
                "status": "location_not_found",
                "message": f"Không tìm thấy vị trí '{location}'. Hỏi người dùng khu vực/thành phố cụ thể hơn.",
            }

        origin_lat = float(geo_results[0]["lat"])
        origin_lon = float(geo_results[0]["lon"])
        origin_display = geo_results[0].get("display_name", clean_location)

        # Step 2: Query nearby points of interest via Overpass (OpenStreetMap data).
        radius_m = max(200, min(int((radius_km or 1.5) * 1000), 5000))
        tags = _resolve_tags(category)
        clauses = "".join(
            f'node["{key}"="{value}"](around:{radius_m},{origin_lat},{origin_lon});\n'
            f'way["{key}"="{value}"](around:{radius_m},{origin_lat},{origin_lon});\n'
            for key, value in tags
        )
        overpass_query = f"[out:json][timeout:25];\n(\n{clauses});\nout center 30;"

        poi_resp = requests.post(_OVERPASS_URL, data={"data": overpass_query}, headers=_HEADERS, timeout=TIMEOUT)
        elements = poi_resp.json().get("elements", [])

        places: list[dict[str, Any]] = []
        for el in elements:
            el_tags = el.get("tags", {})
            name = el_tags.get("name")
            if not name:
                continue
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None or lon is None:
                continue
            places.append({
                "place_id": f"osm:{el['type']}/{el['id']}",
                "name": name,
                "category": el_tags.get("amenity") or el_tags.get("leisure") or "",
                "cuisine": el_tags.get("cuisine", ""),
                "address": _address(el_tags),
                "distance_km": round(_haversine_km(origin_lat, origin_lon, lat, lon), 2),
                "lat": lat,
                "lon": lon,
            })

        places.sort(key=lambda p: p["distance_km"])
        top_places = places[: max(1, int(top_k or 5))]

        if not top_places:
            return {
                "tool": "place_search",
                "location": origin_display,
                "category": category,
                "radius_km": radius_m / 1000,
                "results": [],
                "status": "no_results",
                "message": "Không tìm thấy địa điểm phù hợp trong bán kính này. Thử tăng radius_km hoặc đổi category.",
            }

        return {
            "tool": "place_search",
            "location": origin_display,
            "category": category,
            "radius_km": radius_m / 1000,
            "results": top_places,
            "status": "success",
        }
    except Exception as exc:
        return err("place_search", exc)
