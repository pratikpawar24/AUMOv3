"""AUMOv3.2 Data Service Configuration."""
import os

IS_HF_SPACE = os.getenv("SPACE_ID") is not None
API_PORT = int(os.getenv("PORT", "7860" if IS_HF_SPACE else "8002"))

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

# Maharashtra bounding box
MH_BBOX = {
    "south": 15.60,
    "north": 21.50,
    "west": 72.60,
    "east": 80.90,
}

# Cities to preload places for
PRELOAD_CITIES = [
    {"name": "Pune", "lat": 18.5204, "lng": 73.8567, "radius": 15000},
    {"name": "Mumbai", "lat": 19.0760, "lng": 72.8777, "radius": 20000},
    {"name": "Nagpur", "lat": 21.1458, "lng": 79.0882, "radius": 12000},
    {"name": "Nashik", "lat": 19.9975, "lng": 73.7898, "radius": 10000},
    {"name": "Aurangabad", "lat": 19.8762, "lng": 75.3433, "radius": 10000},
    {"name": "Thane", "lat": 19.2183, "lng": 72.9781, "radius": 10000},
    {"name": "Kolhapur", "lat": 16.7050, "lng": 74.2433, "radius": 8000},
    {"name": "Solapur", "lat": 17.6599, "lng": 75.9064, "radius": 8000},
]
