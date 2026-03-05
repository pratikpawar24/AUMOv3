---
title: AUMOv3
emoji: 🚗
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: AI-Powered Urban Mobility Optimizer for Maharashtra
---

# 🚗 AUMOv3 — AI Service

AI-powered routing, traffic prediction, CO₂ estimation, and carpool matching engine for Maharashtra, India.

## Features
- **AUMORoute™** — Custom routing with Contraction Hierarchies + Time-Dependent A*
- **COPERT IV** — Real-time CO₂ emission estimation
- **BiLSTM + Attention** — Traffic prediction model
- **DBSCAN + Scoring** — Smart carpool matching
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
