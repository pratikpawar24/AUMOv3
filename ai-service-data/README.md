---
title: AUMOv3.2 Data
emoji: 📍
colorFrom: yellow
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: AUMOv3 Places Database & Location Search Service
---

# 📍 AUMOv3.2 — Places Database & Location Service

Fast location search for Maharashtra — shops, stations, roads, colonies, chowks.
Caches data from OpenStreetMap Overpass API for fast local lookups.

## Endpoints
- `GET /api/places/search?q=...` — Search places by name
- `GET /api/places/nearby?lat=...&lng=...` — Nearby places
- `GET /api/places/stops?lat=...&lng=...` — Bus/train/metro stops
- `GET /api/poi` — Maharashtra POI search
- `GET /api/poi/map` — POIs within map bounds
- `GET /api/poi/types` — POI type definitions
- `POST /api/data/refresh` — Refresh place cache from Overpass
- `GET /api/health` — Health check
