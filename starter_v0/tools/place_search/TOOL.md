---
name: place_search
track: bonus
kind: live_api
provider: OpenStreetMap (Nominatim + Overpass)
requires_env: []
inputs: [location, category, radius_km, top_k]
outputs: [location, category, radius_km, results, status]
side_effect: false
---
# place_search

Resolves `location` (city, university, or landmark) via Nominatim geocoding,
then searches nearby restaurants/cafes/bars/entertainment venues via the
Overpass API within `radius_km`. Results are sorted by distance. Free,
no API key required.
