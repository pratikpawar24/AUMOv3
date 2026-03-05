"""AUMOv3.1 ML Service Configuration."""
import os
from dataclasses import dataclass


@dataclass
class ModelConfig:
    input_dim: int = 10
    hidden_dim: int = 128
    hidden_dim_1: int = 128
    hidden_dim_2: int = 64
    num_layers: int = 2
    output_dim: int = 3
    forecast_steps: int = 6
    dropout: float = 0.3
    lookback: int = 12
    seq_len: int = 12
    epochs: int = 30
    batch_size: int = 64
    lr: float = 0.001
    learning_rate: float = 0.001


model_config = ModelConfig()

IS_HF_SPACE = os.getenv("SPACE_ID") is not None
API_PORT = int(os.getenv("PORT", "7860" if IS_HF_SPACE else "8001"))
MODEL_PATH = os.getenv("MODEL_PATH", "saved_models/traffic_lstm.pt")

# HuggingFace dataset for persisting model + data
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "Qrmanual/AUMO")
HF_TOKEN = os.getenv("HF_TOKEN", "")

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
    "https://*.vercel.app",
    "https://*.hf.space",
    "https://*.huggingface.co",
]
