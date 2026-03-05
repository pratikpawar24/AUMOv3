---
title: AUMOv3
emoji: 🚗
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: AI Gateway - Urban Mobility Optimizer for Maharashtra
---

# 🚗 AUMOv3 — AI Gateway Service

Lightweight AI gateway for routing, emissions, and matching. Proxies ML predictions to Space 2 and POI/place data to Space 3.

## Features
- **AUMORoute™** — Custom routing with Contraction Hierarchies + Time-Dependent A*
- **COPERT IV** — Real-time CO₂ emission estimation
- **DBSCAN + Scoring** — Smart carpool matching
- **Proxy** — Forwards ML and data requests to dedicated microservices
- **200+ Maharashtra POIs** — Bus stands, junctions, landmarks

## API Endpoints
- `GET /api/health` — Health check
- `POST /api/route` — Calculate optimal route
- `POST /api/multi-route` — Compare routing strategies
- `POST /api/emissions` — CO₂ estimation
- `POST /api/match` — Carpool matching
- `GET /api/poi?q=&city=` — Search POIs
- `POST /api/traffic/predict` — Traffic prediction
- `GET /api/traffic/heatmap` — Traffic heatmap data
