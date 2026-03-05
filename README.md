# 🚗 AUMO v3 — AI-Powered Urban Mobility Optimizer

> Advanced full-stack web application combining custom routing algorithms, real-time traffic prediction, eco-friendly routing, smart carpooling, and CO₂ estimation — focused on Maharashtra, India.

## 🏗️ Architecture

- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Leaflet.js, Socket.IO, Recharts, Zustand
- **Backend**: Express.js, TypeScript, MongoDB/Mongoose, Socket.IO, JWT Auth
- **AI Service**: FastAPI, PyTorch (BiLSTM + Attention), scikit-learn (DBSCAN), Custom Routing Engine
- **Infrastructure**: Docker Compose, MongoDB 7+

## 🆕 What's New in v3

### Custom Routing Algorithm — AUMORoute™
- **Contraction Hierarchies (CH)** for ultra-fast shortest path queries
- **Time-Dependent A\*** with real-time traffic adaptation
- **Multi-Objective Optimization**: time × emissions × distance × traffic density
- **Dynamic Rerouting**: Instant reroute when traffic conditions change
- **BPR (Bureau of Public Roads) function** for travel time estimation

### Maharashtra POI Integration
- 500+ named places, shops, junctions, ST bus stands across Maharashtra
- Searchable landmarks on the map
- POI-based routing (route through named locations)
- Major cities: Mumbai, Pune, Nagpur, Nashik, Aurangabad, Thane, Kolhapur, Solapur, Satara, Amravati, Latur

### Advanced CO₂ Estimator
- COPERT IV emission model with fuel-type support
- Real-time carpool savings calculator
- "What-if" scenario: solo vs shared ride comparison
- Equivalent tree-days metric
- Fleet-wide emission analytics

### Real-Time Traffic Intelligence
- BiLSTM + Temporal Attention for traffic prediction
- Instant traffic modification & dynamic rerouting
- Congestion-aware path selection
- Traffic heatmap overlay on map

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- MongoDB 7+ (or Docker)

### Local Development

**Backend:**
```bash
cd backend
cp .env.example .env
npm install
npm run dev
```

**Frontend:**
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

**AI Service:**
```bash
cd ai-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Docker Compose
```bash
docker-compose up --build
```

## 📡 Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | Next.js web application |
| Backend | 5000 | Express.js API server |
| AI Service | 8000 | FastAPI ML/routing service |
| MongoDB | 27017 | Database |

## 🧠 Mathematical Models

### M1: AUMORoute™ — Custom Routing Algorithm
```
Contraction Hierarchies preprocessing:
  1. Node ordering by importance: degree × edge_diff × contracted_neighbors
  2. Shortcut creation: for each contracted node u, add shortcut (v, w) if 
     dist(v, u) + dist(u, w) = shortest path(v, w)
  3. Bidirectional Dijkstra on augmented graph

Time-Dependent A* with traffic awareness:
  f(n, t) = g(n, t) + h(n)
  g(n, t) = Σ w(eᵢ, tᵢ) [cumulative cost]
  w(e, t) = length(e) / v_predicted(e, t) [if LSTM prediction available]
         OR t₀ × [1 + 0.15 × (V/C)⁴]  [BPR fallback]

Multi-objective cost:
  Cost(path) = α·T + β·E + γ·D + δ·Traffic_Density
  where α + β + γ + δ = 1
```

### M2: COPERT IV Emission Model
```
fuel_consumption(v) = 0.0667 + 0.0556/v + 0.000472·v²  [L/km]
EF(v) = CO₂_per_liter × fuel_consumption(v)  [g CO₂/km]
CO₂_ride = Σ segments [length_km × EF(v_avg)]
Carpool savings = Σᵢ (dᵢ × EFᵢ) − d_shared × EF_shared
```

### M3: BiLSTM Traffic Predictor
```
Stacked Bidirectional LSTM with Temporal Attention:
  Layer 1: BiLSTM(input=10, hidden=128)
  Layer 2: BiLSTM(input=256, hidden=64)
  Attention: softmax(Wₐ · tanh(Wₕ · H))
  Output: Linear(128 → 3) × forecast_steps
```

### M4: Smart Carpooling (DBSCAN + Scoring)
```
S(d,r) = 0.35·RouteOverlap + 0.25·TimeCompat + 0.15·PrefMatch + 0.25·Proximity
```

### M5: Green Mobility Score
```
GreenScore = min(100, RideShare + CO₂Saved + DistSaved + Consistency)
```

## 📄 License
MIT
