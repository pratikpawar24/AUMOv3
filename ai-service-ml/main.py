"""
AUMOv3.1 — ML Traffic Prediction Microservice

Lightweight service that only handles:
  - Traffic prediction (BiLSTM + Attention)
  - Model training
  - Model persistence to HuggingFace Dataset
"""

import os
import math
import random
from datetime import datetime
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import model_config, API_PORT, CORS_ORIGINS, MODEL_PATH, HF_DATASET_REPO, HF_TOKEN

# ═══════════════════════════════════════════════════════════════
# Model Definition (self-contained, no external deps)
# ═══════════════════════════════════════════════════════════════


class TemporalAttention(nn.Module):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn_W = nn.Linear(hidden_dim, hidden_dim, bias=True)
        self.attn_v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, lstm_output: torch.Tensor):
        energy = torch.tanh(self.attn_W(lstm_output))
        scores = self.attn_v(energy).squeeze(-1)
        attn_weights = F.softmax(scores, dim=1)
        context = torch.bmm(attn_weights.unsqueeze(1), lstm_output).squeeze(1)
        return context, attn_weights


class TrafficLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        dim = model_config.hidden_dim
        self.input_proj = nn.Linear(model_config.input_dim, dim)
        self.input_norm = nn.LayerNorm(dim)
        self.lstm1 = nn.LSTM(dim, dim, 1, batch_first=True, bidirectional=True)
        self.lstm2 = nn.LSTM(dim * 2, dim // 2, 1, batch_first=True, bidirectional=True)
        self.attention = TemporalAttention(dim)
        self.dropout = nn.Dropout(model_config.dropout)
        self.fc1 = nn.Linear(dim, dim // 2)
        self.fc2 = nn.Linear(dim // 2, model_config.output_dim)
        self.norm1 = nn.LayerNorm(dim * 2)
        self.norm2 = nn.LayerNorm(dim)

    def forward(self, x: torch.Tensor):
        h = F.gelu(self.input_norm(self.input_proj(x)))
        h, _ = self.lstm1(h)
        h = self.dropout(self.norm1(h))
        h, _ = self.lstm2(h)
        h = self.dropout(self.norm2(h))
        context, _ = self.attention(h)
        out = self.dropout(F.relu(self.fc1(context)))
        pred = self.fc2(out)
        return torch.cat([
            F.softplus(pred[:, 0:1]),
            F.relu(pred[:, 1:2]),
            torch.sigmoid(pred[:, 2:3]),
        ], dim=1)


# ═══════════════════════════════════════════════════════════════
# Data generation (self-contained)
# ═══════════════════════════════════════════════════════════════


def time_features(dt: datetime) -> Dict[str, float]:
    hour = dt.hour + dt.minute / 60.0
    dow = dt.weekday()
    return {
        "hour_sin": math.sin(2 * math.pi * hour / 24),
        "hour_cos": math.cos(2 * math.pi * hour / 24),
        "day_sin": math.sin(2 * math.pi * dow / 7),
        "day_cos": math.cos(2 * math.pi * dow / 7),
        "is_weekend": 1.0 if dow >= 5 else 0.0,
        "is_holiday": 0.0,
    }


def road_type_encoding(road_type: str) -> float:
    return {"motorway": 1.0, "trunk": 0.85, "primary": 0.7, "secondary": 0.55,
            "tertiary": 0.4, "residential": 0.2, "service": 0.1}.get(road_type, 0.3)


def generate_traffic(hour: float, dow: int, road_type: str, base_speed: float = 50.0):
    is_wknd = dow >= 5
    if 7.5 <= hour < 9.5:
        vf = 0.85 + 0.1 * math.sin(math.pi * (hour - 7.5) / 2)
    elif 17.5 <= hour < 20:
        vf = 0.9 + 0.08 * math.sin(math.pi * (hour - 17.5) / 2.5)
    elif 13 <= hour < 14.5:
        vf = 0.55
    elif 9.5 <= hour < 17.5:
        vf = 0.6
    elif 5 <= hour < 7.5:
        vf = 0.2 + 0.3 * ((hour - 5) / 2.5)
    else:
        vf = 0.1
    if is_wknd:
        vf *= 0.75
    rm = {"motorway": 1.2, "trunk": 1.1, "primary": 1.0, "secondary": 0.8,
          "tertiary": 0.6, "residential": 0.4}.get(road_type, 0.7)
    vf = min(vf * rm, 1.0)
    speed = base_speed * max(1.0 - 0.6 * vf ** 2, 0.2)
    cong = min(1.0, vf ** 1.3)
    cap = {"motorway": 2200, "primary": 1800, "secondary": 1200, "residential": 400}.get(road_type, 1000)
    vol = cap * vf
    return speed + random.gauss(0, speed * 0.05), max(0, vol + random.gauss(0, vol * 0.08)), max(0, min(1, cong + random.gauss(0, 0.03)))


def generate_dataset(num_samples: int = 2000):
    from datetime import timedelta
    road_types = ["motorway", "primary", "secondary", "tertiary", "residential"]
    speeds = {"motorway": 100, "primary": 60, "secondary": 45, "tertiary": 35, "residential": 25}
    X_all, y_all = [], []
    for _ in range(num_samples):
        rt = random.choice(road_types)
        base = speeds[rt]
        start = datetime(2025, 1, 1) + timedelta(minutes=random.randint(0, 525600))
        seq = []
        for s in range(model_config.seq_len):
            dt = start + timedelta(minutes=s * 5)
            sp, vol, cong = generate_traffic(dt.hour + dt.minute / 60, dt.weekday(), rt, base)
            tf = time_features(dt)
            seq.append([sp / 120, vol / 2200, cong, tf["hour_sin"], tf["hour_cos"],
                        tf["day_sin"], tf["day_cos"], tf["is_weekend"], tf["is_holiday"], road_type_encoding(rt)])
        next_dt = start + timedelta(minutes=model_config.seq_len * 5)
        ns, nv, nc = generate_traffic(next_dt.hour + next_dt.minute / 60, next_dt.weekday(), rt, base)
        X_all.append(seq)
        y_all.append([ns / 120, nv / 2200, nc])
    return torch.tensor(X_all, dtype=torch.float32), torch.tensor(y_all, dtype=torch.float32)


# ═══════════════════════════════════════════════════════════════
# HuggingFace Dataset persistence
# ═══════════════════════════════════════════════════════════════


def save_model_to_hf(model: TrafficLSTM):
    """Save trained model to HuggingFace Dataset repo for persistence."""
    try:
        os.makedirs("saved_models", exist_ok=True)
        path = "saved_models/traffic_lstm.pt"
        torch.save(model.state_dict(), path)
        print(f"[ML] Model saved locally to {path}")

        if HF_TOKEN:
            from huggingface_hub import HfApi
            api = HfApi(token=HF_TOKEN)
            api.upload_file(
                path_or_fileobj=path,
                path_in_repo="models/traffic_lstm.pt",
                repo_id=HF_DATASET_REPO,
                repo_type="dataset",
            )
            print(f"[ML] Model uploaded to HF dataset: {HF_DATASET_REPO}")
    except Exception as e:
        print(f"[ML] HF upload error: {e}")


def load_model_from_hf() -> TrafficLSTM:
    """Load model from HF Dataset or local, or use random init."""
    model = TrafficLSTM()
    local_path = MODEL_PATH

    # Try downloading from HF Dataset first
    if HF_TOKEN:
        try:
            from huggingface_hub import hf_hub_download
            local_path = hf_hub_download(
                repo_id=HF_DATASET_REPO,
                filename="models/traffic_lstm.pt",
                repo_type="dataset",
                token=HF_TOKEN,
                local_dir="saved_models",
            )
            print(f"[ML] Model downloaded from HF dataset")
        except Exception as e:
            print(f"[ML] HF download failed: {e}")

    # Load weights
    try:
        state_dict = torch.load(local_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state_dict)
        model.eval()
        print(f"[ML] Model loaded from {local_path}")
    except Exception as e:
        print(f"[ML] Using random init: {e}")

    return model


# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

app = FastAPI(title="AUMOv3.1 ML Service", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if isinstance(CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state = {"model": None, "training": False}


@app.on_event("startup")
async def startup():
    print("\n" + "=" * 50)
    print("  AUMOv3.1 ML Service Starting...")
    print("=" * 50)
    state["model"] = load_model_from_hf()
    print(f"[ML] Service ready on port {API_PORT}")
    print("=" * 50 + "\n")


@app.get("/")
async def root():
    return {"service": "AUMOv3.1 ML", "status": "running", "version": "3.1.0"}


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": state["model"] is not None,
        "training": state["training"],
        "service": "ml-prediction",
        "version": "3.1.0",
    }


class TrafficPredictRequest(BaseModel):
    segments: List[Dict]


@app.post("/api/traffic/predict")
async def predict_traffic_endpoint(req: TrafficPredictRequest):
    if state["model"] is None:
        raise HTTPException(503, "Model not loaded")

    model = state["model"]
    results = []

    for seg in req.segments:
        now = datetime.now()
        tf = time_features(now)
        speed = seg.get("current_speed", 40) / 120.0
        volume = seg.get("current_volume", 500) / 2200.0
        congestion = seg.get("current_congestion", 0.3)
        rt = road_type_encoding(seg.get("road_type", "primary"))

        feature_vec = [speed, volume, congestion,
                       tf["hour_sin"], tf["hour_cos"], tf["day_sin"], tf["day_cos"],
                       tf["is_weekend"], tf["is_holiday"], rt]

        seq = torch.tensor([feature_vec] * model_config.seq_len, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            pred = model(seq).squeeze(0).numpy()

        results.append({
            "segment_id": seg.get("id", "unknown"),
            "predicted_speed": round(float(pred[0]) * 120, 1),
            "predicted_volume": round(float(pred[1]) * 2200, 0),
            "congestion_level": round(float(pred[2]), 3),
        })

    return {"success": True, "predictions": results}


@app.post("/api/train")
async def train_model(background_tasks: BackgroundTasks):
    if state["training"]:
        raise HTTPException(409, "Training already in progress")

    def _train():
        state["training"] = True
        try:
            print("[ML] Training started...")
            model = TrafficLSTM()
            X, y = generate_dataset(num_samples=2000)

            from torch.utils.data import DataLoader, TensorDataset
            ds = TensorDataset(X, y)
            loader = DataLoader(ds, batch_size=model_config.batch_size, shuffle=True)

            optimizer = torch.optim.AdamW(model.parameters(), lr=model_config.lr)
            criterion = nn.MSELoss()

            model.train()
            for epoch in range(model_config.epochs):
                total_loss = 0
                for xb, yb in loader:
                    optimizer.zero_grad()
                    pred = model(xb)
                    loss = criterion(pred, yb)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    total_loss += loss.item()
                if (epoch + 1) % 5 == 0:
                    print(f"[ML] Epoch {epoch + 1}/{model_config.epochs} loss={total_loss / len(loader):.4f}")

            model.eval()
            state["model"] = model
            save_model_to_hf(model)
            print("[ML] Training complete, model saved")
        except Exception as e:
            print(f"[ML] Training error: {e}")
        finally:
            state["training"] = False

    background_tasks.add_task(_train)
    return {"success": True, "message": "Training started in background"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, log_level="info")
