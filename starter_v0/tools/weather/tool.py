from __future__ import annotations

from typing import Any
import requests
from tools._shared import TIMEOUT, err, fold_text


# Open-Meteo's geocoder is a plain city/place gazetteer — it has no concept of
# universities or campuses. Short/coined names silently resolve to an unrelated
# place with the same spelling (e.g. "vinuni" -> a village in Kenya, "MIT" ->
# Mito, Japan, "Stanford" -> Burgaw, NC), always with status "success" and no
# hint that the match is wrong. These well-known landmarks are resolved locally
# with real coordinates before ever hitting the API.
_LANDMARKS: list[dict[str, Any]] = [
    {"substrings": ["vinuni"], "lat": 21.0125, "lon": 105.9556, "display": "VinUniversity, Hanoi, Vietnam"},
    {"substrings": ["bachkhoa"], "words": {"hust"}, "lat": 21.0064, "lon": 105.8433, "display": "Đại học Bách Khoa Hà Nội, Vietnam"},
    {"substrings": ["ngoaithuong"], "words": {"ftu"}, "lat": 21.0038, "lon": 105.7891, "display": "Đại học Ngoại Thương, Hà Nội, Vietnam"},
    {"substrings": ["kinhtequocdan"], "words": {"neu"}, "lat": 21.0075, "lon": 105.8422, "display": "Đại học Kinh tế Quốc dân, Hà Nội, Vietnam"},
    {"substrings": ["dhqghn", "quocgiahanoi"], "words": {"vnu"}, "lat": 21.0378, "lon": 105.7827, "display": "Đại học Quốc gia Hà Nội, Vietnam"},
    {"substrings": ["harvard"], "lat": 42.3770, "lon": -71.1167, "display": "Harvard University, Cambridge, MA, USA"},
    {"substrings": ["stanford"], "lat": 37.4275, "lon": -122.1697, "display": "Stanford University, CA, USA"},
    {"words": {"mit"}, "lat": 42.3601, "lon": -71.0942, "display": "MIT, Cambridge, MA, USA"},
]


def _match_landmark(query: str) -> dict[str, Any] | None:
    folded = fold_text(query)
    no_space = folded.replace(" ", "")
    tokens = set(folded.split())
    for landmark in _LANDMARKS:
        if any(s in no_space for s in landmark.get("substrings", ())):
            return landmark
        if tokens & landmark.get("words", set()):
            return landmark
    return None


def get_weather(city: str = "Hanoi") -> dict[str, Any]:
    """Get current weather dynamically for any city, university, or landmark worldwide using Open-Meteo API."""
    try:
        clean_query = city.strip()

        landmark = _match_landmark(clean_query)
        if landmark:
            lat, lon, location_display = landmark["lat"], landmark["lon"], landmark["display"]
        else:
            # Step 1: Query global Open-Meteo Geocoding engine (cities, admin regions, etc.)
            geo_resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": clean_query, "count": 5, "language": "vi", "format": "json"},
                timeout=TIMEOUT,
            )
            geo_data = geo_resp.json()
            results = geo_data.get("results")

            # Step 2: Dynamic Clarification Guardrail if location cannot be resolved globally
            if not results:
                return {
                    "tool": "weather",
                    "city": city,
                    "status": "location_not_found",
                    "message": f"Geographic coordinates for '{city}' could not be found globally. Ask the user which city/country this location is in.",
                }

            # Among same-named candidates, prefer the most populous (e.g. the
            # searched-for capital "Hà Nội" over a same-named village in Ninh Bình).
            best = max(results, key=lambda r: r.get("population") or 0)
            lat = best["latitude"]
            lon = best["longitude"]
            city_name = best["name"]
            admin1 = best.get("admin1", "")
            country = best.get("country", "")
            location_display = ", ".join(filter(None, [city_name, admin1, country]))

        # Step 3: Fetch current weather for the resolved coordinates
        w_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": "true"},
            timeout=TIMEOUT,
        )
        w_data = w_resp.json().get("current_weather", {})

        return {
            "tool": "weather",
            "city": location_display,
            "query_location": city,
            "temperature_c": w_data.get("temperature", 28.0),
            "condition": "Clear / Normal" if w_data.get("weathercode", 0) < 3 else "Cloudy / Rain",
            "wind_kph": w_data.get("windspeed", 10.0),
            "status": "success",
        }
    except Exception as exc:
        return err("weather", exc)
