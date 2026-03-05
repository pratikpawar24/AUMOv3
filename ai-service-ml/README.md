---
title: AUMOv3.1 ML
emoji: 🧠
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: AUMOv3 Traffic ML Prediction Service
---

# 🧠 AUMOv3.1 — ML Traffic Prediction Service

BiLSTM + Temporal Attention model for real-time traffic prediction.
Part of the AUMOv3 split microservice architecture.

## Endpoints
- `POST /api/traffic/predict` — Predict traffic for road segments
- `POST /api/train` — Trigger model training
- `GET /api/health` — Health check
