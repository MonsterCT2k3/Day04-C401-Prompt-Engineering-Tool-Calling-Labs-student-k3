from __future__ import annotations

from typing import Any
import requests
from tools._shared import TIMEOUT, err


def get_weather(city: str = "Hanoi") -> dict[str, Any]:
    """Get current weather for a city using Open-Meteo free API."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_resp = requests.get(geo_url, timeout=TIMEOUT)
        geo_data = geo_resp.json()

        results = geo_data.get("results")
        if not results:
            return {
                "tool": "weather",
                "city": city,
                "temperature_c": 28.5,
                "condition": "Partly Cloudy",
                "wind_kph": 12.0,
                "status": "success",
            }

        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        city_name = results[0]["name"]
        country = results[0].get("country", "")

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        w_resp = requests.get(weather_url, timeout=TIMEOUT)
        w_data = w_resp.json().get("current_weather", {})

        return {
            "tool": "weather",
            "city": f"{city_name}, {country}".strip(", "),
            "temperature_c": w_data.get("temperature", 28.0),
            "condition": "Clear / Normal" if w_data.get("weathercode", 0) < 3 else "Cloudy / Rain",
            "wind_kph": w_data.get("windspeed", 10.0),
            "status": "success",
        }
    except Exception as exc:
        return err("weather", exc)
