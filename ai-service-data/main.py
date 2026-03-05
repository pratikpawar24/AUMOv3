"""
AUMOv3.2 — Data & Places Service
Handles POI database, Overpass place lookups, caching to HuggingFace Dataset.
No PyTorch dependency — lightweight and fast startup.
"""

import os, json, math, time, asyncio, logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import (
    API_PORT, CORS_ORIGINS, HF_DATASET_REPO, HF_TOKEN,
    MH_BBOX, PRELOAD_CITIES,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aumov3-data")

# ═══════════════════════════════════════════════════════════════
# POI Type Definitions
# ═══════════════════════════════════════════════════════════════

POI_TYPES = {
    "st_bus_stand": {"icon": "bus", "color": "#E53E3E", "label": "ST Bus Stand"},
    "bus_stop": {"icon": "bus", "color": "#FC8181", "label": "City Bus Stop"},
    "railway_station": {"icon": "train", "color": "#3182CE", "label": "Railway Station"},
    "metro_station": {"icon": "subway", "color": "#319795", "label": "Metro Station"},
    "junction": {"icon": "crosshairs", "color": "#DD6B20", "label": "Junction / Chowk"},
    "shop": {"icon": "shopping-cart", "color": "#38A169", "label": "Shopping Area"},
    "shopping": {"icon": "shopping-cart", "color": "#38A169", "label": "Shopping / Mall"},
    "hospital": {"icon": "hospital", "color": "#E53E3E", "label": "Hospital"},
    "pharmacy": {"icon": "pills", "color": "#F56565", "label": "Pharmacy / Chemist"},
    "education": {"icon": "graduation-cap", "color": "#805AD5", "label": "Education"},
    "landmark": {"icon": "monument", "color": "#D69E2E", "label": "Landmark"},
    "metro": {"icon": "subway", "color": "#319795", "label": "Metro Station"},
    "fuel": {"icon": "gas-pump", "color": "#4A5568", "label": "Fuel / EV Charging"},
    "fuel_station": {"icon": "gas-pump", "color": "#4A5568", "label": "Fuel / EV Charging"},
    "government": {"icon": "building", "color": "#2B6CB0", "label": "Government Office"},
    "colony": {"icon": "home", "color": "#9F7AEA", "label": "Colony / Residential"},
    "road": {"icon": "road", "color": "#718096", "label": "Road / Highway"},
    "chowk": {"icon": "crosshairs", "color": "#ED8936", "label": "Chowk / Square"},
    "police_station": {"icon": "shield", "color": "#2D3748", "label": "Police Station"},
    "fire_station": {"icon": "fire-extinguisher", "color": "#C53030", "label": "Fire Station"},
    "airport": {"icon": "plane", "color": "#2C5282", "label": "Airport"},
    "cafe": {"icon": "coffee", "color": "#B7791F", "label": "Cafe / Restaurant"},
    "town": {"icon": "map-pin", "color": "#4C51BF", "label": "Town / Village"},
    "place": {"icon": "map-pin", "color": "#667EEA", "label": "Place / Area"},
    "worship": {"icon": "landmark", "color": "#F6AD55", "label": "Temple / Worship"},
    "bank": {"icon": "landmark", "color": "#48BB78", "label": "Bank / ATM"},
    "post_office": {"icon": "mail", "color": "#FC8181", "label": "Post Office"},
    "hotel": {"icon": "bed", "color": "#9F7AEA", "label": "Hotel / Lodge"},
    "entertainment": {"icon": "film", "color": "#ED64A6", "label": "Entertainment"},
    "park": {"icon": "tree", "color": "#38A169", "label": "Park / Garden"},
    "building": {"icon": "building", "color": "#A0AEC0", "label": "Building"},
    "commercial": {"icon": "briefcase", "color": "#DD6B20", "label": "Commercial / Industrial"},
    "water": {"icon": "water", "color": "#3182CE", "label": "Water Body"},
    "amenity": {"icon": "info-circle", "color": "#718096", "label": "Amenity"},
}

# ═══════════════════════════════════════════════════════════════
# Hardcoded Maharashtra POI Database (200+ POIs)
# ═══════════════════════════════════════════════════════════════

PUNE_POIS = [
    {"name": "Pune Station (Swargate) ST Stand", "lat": 18.5018, "lng": 73.8636, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Shivajinagar ST Stand", "lat": 18.5310, "lng": 73.8458, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Wakad Bus Stop", "lat": 18.5990, "lng": 73.7604, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Hadapsar ST Stand", "lat": 18.5089, "lng": 73.9260, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Katraj Bus Stop", "lat": 18.4577, "lng": 73.8660, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Nigdi ST Stand", "lat": 18.6518, "lng": 73.7711, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Kothrud Depot", "lat": 18.5074, "lng": 73.8077, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Deccan Bus Stop", "lat": 18.5168, "lng": 73.8409, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Pune Junction Railway Station", "lat": 18.5285, "lng": 73.8743, "type": "railway_station", "city": "Pune"},
    {"name": "Shivajinagar Railway Station", "lat": 18.5341, "lng": 73.8498, "type": "railway_station", "city": "Pune"},
    {"name": "Khadki Railway Station", "lat": 18.5658, "lng": 73.8417, "type": "railway_station", "city": "Pune"},
    {"name": "Chinchwad Railway Station", "lat": 18.6270, "lng": 73.7936, "type": "railway_station", "city": "Pune"},
    {"name": "Pimpri Railway Station", "lat": 18.6225, "lng": 73.8039, "type": "railway_station", "city": "Pune"},
    {"name": "Hadapsar Railway Station", "lat": 18.4997, "lng": 73.9433, "type": "railway_station", "city": "Pune"},
    {"name": "Swargate Chowk", "lat": 18.5018, "lng": 73.8636, "type": "junction", "city": "Pune"},
    {"name": "Nal Stop Junction", "lat": 18.5153, "lng": 73.8316, "type": "junction", "city": "Pune"},
    {"name": "Chandni Chowk", "lat": 18.5120, "lng": 73.8125, "type": "junction", "city": "Pune"},
    {"name": "Warje Junction", "lat": 18.4875, "lng": 73.7991, "type": "junction", "city": "Pune"},
    {"name": "Hinjewadi Chowk", "lat": 18.5912, "lng": 73.7389, "type": "junction", "city": "Pune"},
    {"name": "Kharadi Bypass Junction", "lat": 18.5512, "lng": 73.9406, "type": "junction", "city": "Pune"},
    {"name": "Magarpatta Road Junction", "lat": 18.5132, "lng": 73.9298, "type": "junction", "city": "Pune"},
    {"name": "University Circle", "lat": 18.5538, "lng": 73.8252, "type": "junction", "city": "Pune"},
    {"name": "Laxmi Road Market", "lat": 18.5128, "lng": 73.8553, "type": "shop", "city": "Pune"},
    {"name": "MG Road Pune", "lat": 18.5158, "lng": 73.8790, "type": "shop", "city": "Pune"},
    {"name": "FC Road (Fergusson College Road)", "lat": 18.5252, "lng": 73.8397, "type": "shop", "city": "Pune"},
    {"name": "Phoenix Marketcity Pune", "lat": 18.5601, "lng": 73.9154, "type": "shop", "city": "Pune"},
    {"name": "Seasons Mall Magarpatta", "lat": 18.5145, "lng": 73.9283, "type": "shop", "city": "Pune"},
    {"name": "Westend Mall Aundh", "lat": 18.5627, "lng": 73.8075, "type": "shop", "city": "Pune"},
    {"name": "Appa Balwant Chowk", "lat": 18.5145, "lng": 73.8565, "type": "shop", "city": "Pune"},
    {"name": "Tulsi Baug", "lat": 18.5125, "lng": 73.8558, "type": "shop", "city": "Pune"},
    {"name": "Mandai Market", "lat": 18.5101, "lng": 73.8572, "type": "shop", "city": "Pune"},
    {"name": "Shaniwar Wada", "lat": 18.5195, "lng": 73.8554, "type": "landmark", "city": "Pune"},
    {"name": "Aga Khan Palace", "lat": 18.5531, "lng": 73.9015, "type": "landmark", "city": "Pune"},
    {"name": "Sinhagad Fort", "lat": 18.3661, "lng": 73.7558, "type": "landmark", "city": "Pune"},
    {"name": "Dagdusheth Ganpati", "lat": 18.5168, "lng": 73.8562, "type": "landmark", "city": "Pune"},
    {"name": "Sassoon General Hospital", "lat": 18.5230, "lng": 73.8729, "type": "hospital", "city": "Pune"},
    {"name": "Ruby Hall Clinic", "lat": 18.5336, "lng": 73.8816, "type": "hospital", "city": "Pune"},
    {"name": "Jehangir Hospital", "lat": 18.5332, "lng": 73.8754, "type": "hospital", "city": "Pune"},
    {"name": "Sahyadri Hospital", "lat": 18.5162, "lng": 73.8408, "type": "hospital", "city": "Pune"},
    {"name": "Savitribai Phule Pune University", "lat": 18.5538, "lng": 73.8252, "type": "education", "city": "Pune"},
    {"name": "Fergusson College", "lat": 18.5242, "lng": 73.8395, "type": "education", "city": "Pune"},
    {"name": "COEP Technological University", "lat": 18.5295, "lng": 73.8516, "type": "education", "city": "Pune"},
    {"name": "PCMC Metro Station", "lat": 18.6476, "lng": 73.8011, "type": "metro", "city": "Pune"},
    {"name": "Civil Court Metro Station", "lat": 18.5265, "lng": 73.8756, "type": "metro", "city": "Pune"},
    {"name": "Garware College Metro Station", "lat": 18.5168, "lng": 73.8409, "type": "metro", "city": "Pune"},
    {"name": "Vanaz Metro Station", "lat": 18.5082, "lng": 73.8022, "type": "metro", "city": "Pune"},
    # Colonies / Residential Areas
    {"name": "Kothrud Colony", "lat": 18.5074, "lng": 73.8077, "type": "colony", "city": "Pune"},
    {"name": "Baner Colony", "lat": 18.5590, "lng": 73.7868, "type": "colony", "city": "Pune"},
    {"name": "Aundh Colony", "lat": 18.5627, "lng": 73.8075, "type": "colony", "city": "Pune"},
    {"name": "Viman Nagar", "lat": 18.5679, "lng": 73.9143, "type": "colony", "city": "Pune"},
    {"name": "Kalyani Nagar", "lat": 18.5462, "lng": 73.9027, "type": "colony", "city": "Pune"},
    {"name": "Koregaon Park", "lat": 18.5362, "lng": 73.8936, "type": "colony", "city": "Pune"},
    {"name": "Bibwewadi", "lat": 18.4789, "lng": 73.8630, "type": "colony", "city": "Pune"},
    {"name": "Kondhwa Colony", "lat": 18.4632, "lng": 73.8900, "type": "colony", "city": "Pune"},
    {"name": "Wagholi Colony", "lat": 18.5800, "lng": 73.9740, "type": "colony", "city": "Pune"},
    # Roads
    {"name": "Pune-Mumbai Expressway", "lat": 18.7200, "lng": 73.4050, "type": "road", "city": "Pune"},
    {"name": "Pune-Solapur Highway (NH65)", "lat": 18.4900, "lng": 73.9400, "type": "road", "city": "Pune"},
    {"name": "Pune-Bangalore Highway (NH48)", "lat": 18.4700, "lng": 73.8460, "type": "road", "city": "Pune"},
    {"name": "Senapati Bapat Road", "lat": 18.5280, "lng": 73.8310, "type": "road", "city": "Pune"},
    {"name": "JM Road (Jungli Maharaj Road)", "lat": 18.5225, "lng": 73.8410, "type": "road", "city": "Pune"},
]

MUMBAI_POIS = [
    {"name": "Mumbai Central ST Stand", "lat": 18.9690, "lng": 72.8190, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Borivali ST Stand", "lat": 19.2283, "lng": 72.8572, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Dadar ST Stand", "lat": 19.0176, "lng": 72.8435, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Kurla ST Stand", "lat": 19.0726, "lng": 72.8794, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Panvel ST Stand", "lat": 18.9925, "lng": 73.1106, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "CST (Chhatrapati Shivaji Terminus)", "lat": 18.9398, "lng": 72.8355, "type": "railway_station", "city": "Mumbai"},
    {"name": "Mumbai Central Station", "lat": 18.9690, "lng": 72.8190, "type": "railway_station", "city": "Mumbai"},
    {"name": "Dadar Station", "lat": 19.0176, "lng": 72.8435, "type": "railway_station", "city": "Mumbai"},
    {"name": "Bandra Terminus", "lat": 19.0544, "lng": 72.8403, "type": "railway_station", "city": "Mumbai"},
    {"name": "Andheri Station", "lat": 19.1197, "lng": 72.8464, "type": "railway_station", "city": "Mumbai"},
    {"name": "Churchgate Station", "lat": 18.9350, "lng": 72.8276, "type": "railway_station", "city": "Mumbai"},
    {"name": "Borivali Station", "lat": 19.2283, "lng": 72.8572, "type": "railway_station", "city": "Mumbai"},
    {"name": "Thane Station", "lat": 19.1860, "lng": 72.9763, "type": "railway_station", "city": "Mumbai"},
    {"name": "Dadar Junction (TT Circle)", "lat": 19.0176, "lng": 72.8435, "type": "junction", "city": "Mumbai"},
    {"name": "Sion Circle", "lat": 19.0413, "lng": 72.8622, "type": "junction", "city": "Mumbai"},
    {"name": "Haji Ali Junction", "lat": 18.9827, "lng": 72.8126, "type": "junction", "city": "Mumbai"},
    {"name": "Andheri Subway Junction", "lat": 19.1197, "lng": 72.8464, "type": "junction", "city": "Mumbai"},
    {"name": "Teen Hath Naka Thane", "lat": 19.1967, "lng": 72.9635, "type": "junction", "city": "Mumbai"},
    {"name": "Crawford Market", "lat": 18.9475, "lng": 72.8332, "type": "shop", "city": "Mumbai"},
    {"name": "Linking Road Bandra", "lat": 19.0595, "lng": 72.8356, "type": "shop", "city": "Mumbai"},
    {"name": "Colaba Causeway", "lat": 18.9192, "lng": 72.8321, "type": "shop", "city": "Mumbai"},
    {"name": "High Street Phoenix", "lat": 18.9947, "lng": 72.8283, "type": "shop", "city": "Mumbai"},
    {"name": "R City Mall Ghatkopar", "lat": 19.0863, "lng": 72.9158, "type": "shop", "city": "Mumbai"},
    {"name": "Gateway of India", "lat": 18.9220, "lng": 72.8347, "type": "landmark", "city": "Mumbai"},
    {"name": "Marine Drive", "lat": 18.9432, "lng": 72.8235, "type": "landmark", "city": "Mumbai"},
    {"name": "Siddhivinayak Temple", "lat": 19.0170, "lng": 72.8310, "type": "landmark", "city": "Mumbai"},
    {"name": "Bandra-Worli Sea Link", "lat": 19.0300, "lng": 72.8165, "type": "landmark", "city": "Mumbai"},
    {"name": "Juhu Beach", "lat": 19.0988, "lng": 72.8267, "type": "landmark", "city": "Mumbai"},
    {"name": "Versova Metro", "lat": 19.1312, "lng": 72.8201, "type": "metro", "city": "Mumbai"},
    {"name": "Andheri Metro", "lat": 19.1197, "lng": 72.8464, "type": "metro", "city": "Mumbai"},
    {"name": "Ghatkopar Metro", "lat": 19.0868, "lng": 72.9086, "type": "metro", "city": "Mumbai"},
    # Colonies
    {"name": "Bandra West", "lat": 19.0596, "lng": 72.8295, "type": "colony", "city": "Mumbai"},
    {"name": "Powai Colony", "lat": 19.1176, "lng": 72.9060, "type": "colony", "city": "Mumbai"},
    {"name": "Malad West", "lat": 19.1867, "lng": 72.8369, "type": "colony", "city": "Mumbai"},
    {"name": "Goregaon East", "lat": 19.1623, "lng": 72.8630, "type": "colony", "city": "Mumbai"},
    {"name": "Andheri East", "lat": 19.1197, "lng": 72.8700, "type": "colony", "city": "Mumbai"},
    # Roads
    {"name": "Western Express Highway", "lat": 19.1553, "lng": 72.8495, "type": "road", "city": "Mumbai"},
    {"name": "Eastern Express Highway", "lat": 19.0800, "lng": 72.9100, "type": "road", "city": "Mumbai"},
    {"name": "Mumbai-Pune Expressway", "lat": 19.0000, "lng": 73.1000, "type": "road", "city": "Mumbai"},
]

NAGPUR_POIS = [
    {"name": "Nagpur ST Stand (Ganeshpeth)", "lat": 21.1431, "lng": 79.0918, "type": "st_bus_stand", "city": "Nagpur"},
    {"name": "Nagpur Railway Station", "lat": 21.1504, "lng": 79.0870, "type": "railway_station", "city": "Nagpur"},
    {"name": "Sitabuldi Junction", "lat": 21.1466, "lng": 79.0849, "type": "junction", "city": "Nagpur"},
    {"name": "Variety Square", "lat": 21.1479, "lng": 79.0737, "type": "junction", "city": "Nagpur"},
    {"name": "LAD Chowk", "lat": 21.1401, "lng": 79.0715, "type": "junction", "city": "Nagpur"},
    {"name": "Dharampeth Market", "lat": 21.1490, "lng": 79.0680, "type": "shop", "city": "Nagpur"},
    {"name": "Sadar Bazaar Nagpur", "lat": 21.1466, "lng": 79.0849, "type": "shop", "city": "Nagpur"},
    {"name": "Futala Lake", "lat": 21.1553, "lng": 79.0479, "type": "landmark", "city": "Nagpur"},
    {"name": "Deekshabhoomi", "lat": 21.1370, "lng": 79.0715, "type": "landmark", "city": "Nagpur"},
    {"name": "Zero Mile Nagpur", "lat": 21.1480, "lng": 79.0816, "type": "landmark", "city": "Nagpur"},
    {"name": "Nagpur Metro Sitabuldi", "lat": 21.1466, "lng": 79.0849, "type": "metro", "city": "Nagpur"},
    {"name": "AIIMS Nagpur", "lat": 21.1204, "lng": 79.0430, "type": "hospital", "city": "Nagpur"},
    {"name": "VNIT Nagpur", "lat": 21.1264, "lng": 79.0513, "type": "education", "city": "Nagpur"},
]

NASHIK_POIS = [
    {"name": "Nashik CBS", "lat": 19.9975, "lng": 73.7898, "type": "st_bus_stand", "city": "Nashik"},
    {"name": "Nashik Road Railway Station", "lat": 19.9698, "lng": 73.7994, "type": "railway_station", "city": "Nashik"},
    {"name": "Dwarka Circle", "lat": 19.9972, "lng": 73.7770, "type": "junction", "city": "Nashik"},
    {"name": "Panchavati", "lat": 20.0067, "lng": 73.7880, "type": "landmark", "city": "Nashik"},
    {"name": "Trimbakeshwar Temple", "lat": 19.9322, "lng": 73.5310, "type": "landmark", "city": "Nashik"},
    {"name": "Sula Vineyards", "lat": 20.0050, "lng": 73.7600, "type": "landmark", "city": "Nashik"},
    {"name": "City Center Mall Nashik", "lat": 20.0050, "lng": 73.7920, "type": "shop", "city": "Nashik"},
]

OTHER_POIS = [
    {"name": "Aurangabad CBS", "lat": 19.8762, "lng": 75.3433, "type": "st_bus_stand", "city": "Aurangabad"},
    {"name": "Aurangabad Railway Station", "lat": 19.8724, "lng": 75.3213, "type": "railway_station", "city": "Aurangabad"},
    {"name": "Kranti Chowk", "lat": 19.8762, "lng": 75.3433, "type": "junction", "city": "Aurangabad"},
    {"name": "Ajanta Caves", "lat": 20.5519, "lng": 75.7033, "type": "landmark", "city": "Aurangabad"},
    {"name": "Ellora Caves", "lat": 20.0268, "lng": 75.1790, "type": "landmark", "city": "Aurangabad"},
    {"name": "Bibi Ka Maqbara", "lat": 19.9018, "lng": 75.3210, "type": "landmark", "city": "Aurangabad"},
    {"name": "Kolhapur CBS", "lat": 16.7050, "lng": 74.2433, "type": "st_bus_stand", "city": "Kolhapur"},
    {"name": "Kolhapur Railway Station", "lat": 16.6940, "lng": 74.2298, "type": "railway_station", "city": "Kolhapur"},
    {"name": "Mahalaxmi Temple Kolhapur", "lat": 16.7058, "lng": 74.2310, "type": "landmark", "city": "Kolhapur"},
    {"name": "Rankala Lake", "lat": 16.6918, "lng": 74.2160, "type": "landmark", "city": "Kolhapur"},
    {"name": "Solapur CBS", "lat": 17.6599, "lng": 75.9064, "type": "st_bus_stand", "city": "Solapur"},
    {"name": "Solapur Railway Station", "lat": 17.6559, "lng": 75.9048, "type": "railway_station", "city": "Solapur"},
    {"name": "Sangli ST Stand", "lat": 16.8524, "lng": 74.5815, "type": "st_bus_stand", "city": "Sangli"},
    {"name": "Satara CBS", "lat": 17.6805, "lng": 74.0183, "type": "st_bus_stand", "city": "Satara"},
    {"name": "Ratnagiri ST Stand", "lat": 16.9902, "lng": 73.3120, "type": "st_bus_stand", "city": "Ratnagiri"},
    {"name": "Nanded CBS", "lat": 19.1596, "lng": 77.3154, "type": "st_bus_stand", "city": "Nanded"},
    {"name": "Amravati ST Stand", "lat": 20.9320, "lng": 77.7523, "type": "st_bus_stand", "city": "Amravati"},
    {"name": "Latur CBS", "lat": 18.3980, "lng": 76.5606, "type": "st_bus_stand", "city": "Latur"},
    {"name": "Akola ST Stand", "lat": 20.7091, "lng": 77.0029, "type": "st_bus_stand", "city": "Akola"},
    {"name": "Jalgaon CBS", "lat": 21.0077, "lng": 75.5626, "type": "st_bus_stand", "city": "Jalgaon"},
    {"name": "Dhule CBS", "lat": 20.9042, "lng": 74.7749, "type": "st_bus_stand", "city": "Dhule"},
    {"name": "Ahmednagar CBS", "lat": 19.0948, "lng": 74.7480, "type": "st_bus_stand", "city": "Ahmednagar"},
    {"name": "Shirdi Sai Baba Temple", "lat": 19.7664, "lng": 74.4766, "type": "landmark", "city": "Ahmednagar"},
    {"name": "Chandrapur CBS", "lat": 19.9615, "lng": 79.2961, "type": "st_bus_stand", "city": "Chandrapur"},
    {"name": "Tadoba Tiger Reserve", "lat": 20.2410, "lng": 79.3650, "type": "landmark", "city": "Chandrapur"},
    {"name": "Lonavala Railway Station", "lat": 18.7503, "lng": 73.4078, "type": "railway_station", "city": "Lonavala"},
    {"name": "Bhushi Dam", "lat": 18.7422, "lng": 73.3990, "type": "landmark", "city": "Lonavala"},
    {"name": "Mahabaleshwar ST Stand", "lat": 17.9237, "lng": 73.6586, "type": "st_bus_stand", "city": "Mahabaleshwar"},
    {"name": "Alibaug Beach", "lat": 18.6398, "lng": 72.8715, "type": "landmark", "city": "Alibaug"},
    {"name": "Sevagram Ashram", "lat": 20.7282, "lng": 78.6652, "type": "landmark", "city": "Wardha"},
    {"name": "Sindhudurg Fort", "lat": 16.0412, "lng": 73.4629, "type": "landmark", "city": "Sindhudurg"},
    {"name": "Kaas Plateau", "lat": 17.7221, "lng": 73.8167, "type": "landmark", "city": "Satara"},
    {"name": "Sachkhand Gurudwara Hazur Sahib", "lat": 19.1568, "lng": 77.3204, "type": "landmark", "city": "Nanded"},
    # ── Police Stations ──
    {"name": "Deccan Police Station Pune", "lat": 18.5168, "lng": 73.8350, "type": "police_station", "city": "Pune"},
    {"name": "Shivajinagar Police Station Pune", "lat": 18.5310, "lng": 73.8460, "type": "police_station", "city": "Pune"},
    {"name": "Swargate Police Station Pune", "lat": 18.5018, "lng": 73.8600, "type": "police_station", "city": "Pune"},
    {"name": "Kothrud Police Station", "lat": 18.5074, "lng": 73.8100, "type": "police_station", "city": "Pune"},
    {"name": "Hinjewadi Police Station", "lat": 18.5900, "lng": 73.7400, "type": "police_station", "city": "Pune"},
    {"name": "Hadapsar Police Station", "lat": 18.5089, "lng": 73.9260, "type": "police_station", "city": "Pune"},
    {"name": "Pimpri Police Station", "lat": 18.6225, "lng": 73.8040, "type": "police_station", "city": "Pune"},
    {"name": "Bandra Police Station Mumbai", "lat": 19.0544, "lng": 72.8403, "type": "police_station", "city": "Mumbai"},
    {"name": "Colaba Police Station Mumbai", "lat": 18.9220, "lng": 72.8321, "type": "police_station", "city": "Mumbai"},
    {"name": "Andheri Police Station Mumbai", "lat": 19.1197, "lng": 72.8464, "type": "police_station", "city": "Mumbai"},
    {"name": "Dadar Police Station Mumbai", "lat": 19.0180, "lng": 72.8435, "type": "police_station", "city": "Mumbai"},
    {"name": "Thane Police Station", "lat": 19.1860, "lng": 72.9763, "type": "police_station", "city": "Thane"},
    {"name": "Sitabuldi Police Station Nagpur", "lat": 21.1466, "lng": 79.0849, "type": "police_station", "city": "Nagpur"},
    {"name": "Nashik City Police Station", "lat": 19.9975, "lng": 73.7898, "type": "police_station", "city": "Nashik"},
    # ── More Railway Stations ──
    {"name": "Karjat Railway Station", "lat": 18.9103, "lng": 73.3228, "type": "railway_station", "city": "Karjat"},
    {"name": "Kasara Railway Station", "lat": 19.6355, "lng": 73.4716, "type": "railway_station", "city": "Kasara"},
    {"name": "Kalyan Junction", "lat": 19.2437, "lng": 73.1355, "type": "railway_station", "city": "Kalyan"},
    {"name": "Dombivli Railway Station", "lat": 19.2167, "lng": 73.0868, "type": "railway_station", "city": "Dombivli"},
    {"name": "Badlapur Railway Station", "lat": 19.1658, "lng": 73.2468, "type": "railway_station", "city": "Badlapur"},
    {"name": "Panvel Railway Station", "lat": 18.9925, "lng": 73.1106, "type": "railway_station", "city": "Panvel"},
    {"name": "Navi Mumbai Belapur Station", "lat": 19.0235, "lng": 73.0400, "type": "railway_station", "city": "Navi Mumbai"},
    {"name": "Vashi Railway Station", "lat": 19.0676, "lng": 72.9988, "type": "railway_station", "city": "Navi Mumbai"},
    {"name": "Sangli Railway Station", "lat": 16.8524, "lng": 74.5815, "type": "railway_station", "city": "Sangli"},
    {"name": "Satara Railway Station", "lat": 17.6805, "lng": 74.0050, "type": "railway_station", "city": "Satara"},
    {"name": "Latur Railway Station", "lat": 18.3980, "lng": 76.5606, "type": "railway_station", "city": "Latur"},
    {"name": "Amravati Railway Station", "lat": 20.9320, "lng": 77.7523, "type": "railway_station", "city": "Amravati"},
    {"name": "Akola Railway Station", "lat": 20.7100, "lng": 77.0029, "type": "railway_station", "city": "Akola"},
    {"name": "Jalgaon Railway Station", "lat": 21.0077, "lng": 75.5560, "type": "railway_station", "city": "Jalgaon"},
    {"name": "Dhule Railway Station", "lat": 20.9042, "lng": 74.7749, "type": "railway_station", "city": "Dhule"},
    {"name": "Nanded Railway Station", "lat": 19.1596, "lng": 77.3100, "type": "railway_station", "city": "Nanded"},
    {"name": "Ratnagiri Railway Station", "lat": 16.9902, "lng": 73.2820, "type": "railway_station", "city": "Ratnagiri"},
    {"name": "Manmad Junction", "lat": 20.2523, "lng": 74.4375, "type": "railway_station", "city": "Manmad"},
    {"name": "Bhusawal Junction", "lat": 21.0440, "lng": 75.7800, "type": "railway_station", "city": "Bhusawal"},
    {"name": "Igatpuri Railway Station", "lat": 19.6966, "lng": 73.5595, "type": "railway_station", "city": "Igatpuri"},
    {"name": "Wardha Railway Station", "lat": 20.7456, "lng": 78.5991, "type": "railway_station", "city": "Wardha"},
    {"name": "Chandrapur Railway Station", "lat": 19.9615, "lng": 79.2961, "type": "railway_station", "city": "Chandrapur"},
    {"name": "Parbhani Railway Station", "lat": 19.2616, "lng": 76.7740, "type": "railway_station", "city": "Parbhani"},
    {"name": "Beed CBS", "lat": 18.9891, "lng": 75.7580, "type": "st_bus_stand", "city": "Beed"},
    {"name": "Osmanabad CBS", "lat": 18.1860, "lng": 76.0400, "type": "st_bus_stand", "city": "Osmanabad"},
    # ── More Bus Stops ──
    {"name": "Thane ST Stand", "lat": 19.1860, "lng": 72.9763, "type": "st_bus_stand", "city": "Thane"},
    {"name": "Kalyan ST Stand", "lat": 19.2437, "lng": 73.1355, "type": "st_bus_stand", "city": "Kalyan"},
    {"name": "Navi Mumbai ST Stand Vashi", "lat": 19.0676, "lng": 72.9988, "type": "st_bus_stand", "city": "Navi Mumbai"},
    {"name": "Pimpri PMPML Bus Depot", "lat": 18.6200, "lng": 73.8050, "type": "bus_stop", "city": "Pune"},
    {"name": "Swargate PMPML Depot", "lat": 18.5018, "lng": 73.8636, "type": "bus_stop", "city": "Pune"},
    {"name": "Katraj PMPML Depot", "lat": 18.4577, "lng": 73.8660, "type": "bus_stop", "city": "Pune"},
    {"name": "Nashik CBS MSRTC", "lat": 19.9975, "lng": 73.7898, "type": "bus_stop", "city": "Nashik"},
    {"name": "Kolhapur Rankala Bus Stop", "lat": 16.6918, "lng": 74.2180, "type": "bus_stop", "city": "Kolhapur"},
    {"name": "Parbhani CBS", "lat": 19.2616, "lng": 76.7740, "type": "st_bus_stand", "city": "Parbhani"},
    {"name": "Washim CBS", "lat": 20.1012, "lng": 77.1486, "type": "st_bus_stand", "city": "Washim"},
    {"name": "Yavatmal CBS", "lat": 20.3888, "lng": 78.1203, "type": "st_bus_stand", "city": "Yavatmal"},
    {"name": "Hingoli CBS", "lat": 19.7150, "lng": 77.1510, "type": "st_bus_stand", "city": "Hingoli"},
    {"name": "Gadchiroli CBS", "lat": 20.1750, "lng": 80.0012, "type": "st_bus_stand", "city": "Gadchiroli"},
    {"name": "Gondia CBS", "lat": 21.4548, "lng": 80.1942, "type": "st_bus_stand", "city": "Gondia"},
    {"name": "Bhandara CBS", "lat": 21.1657, "lng": 79.6508, "type": "st_bus_stand", "city": "Bhandara"},
    {"name": "Buldhana CBS", "lat": 20.5290, "lng": 76.1858, "type": "st_bus_stand", "city": "Buldhana"},
    # ── Airports ──
    {"name": "Pune Airport (Lohegaon)", "lat": 18.5822, "lng": 73.9197, "type": "airport", "city": "Pune"},
    {"name": "Mumbai Airport (CSIA Terminal 2)", "lat": 19.0896, "lng": 72.8656, "type": "airport", "city": "Mumbai"},
    {"name": "Mumbai Airport (Domestic Terminal 1)", "lat": 19.0985, "lng": 72.8742, "type": "airport", "city": "Mumbai"},
    {"name": "Nagpur Airport (Dr. Ambedkar)", "lat": 21.0922, "lng": 79.0472, "type": "airport", "city": "Nagpur"},
    {"name": "Aurangabad Airport", "lat": 19.8627, "lng": 75.3981, "type": "airport", "city": "Aurangabad"},
    {"name": "Kolhapur Airport", "lat": 16.6646, "lng": 74.2894, "type": "airport", "city": "Kolhapur"},
    {"name": "Shirdi Airport", "lat": 19.6887, "lng": 74.3789, "type": "airport", "city": "Shirdi"},
    {"name": "Navi Mumbai International Airport (NMIA)", "lat": 18.9980, "lng": 73.1136, "type": "airport", "city": "Navi Mumbai"},
    # ── Cafés & Restaurants ──
    {"name": "Vaishali Restaurant Pune", "lat": 18.5248, "lng": 73.8396, "type": "cafe", "city": "Pune"},
    {"name": "German Bakery Koregaon Park", "lat": 18.5362, "lng": 73.8936, "type": "cafe", "city": "Pune"},
    {"name": "Goodluck Cafe FC Road", "lat": 18.5252, "lng": 73.8397, "type": "cafe", "city": "Pune"},
    {"name": "Café Leopold Mumbai", "lat": 18.9228, "lng": 72.8318, "type": "cafe", "city": "Mumbai"},
    {"name": "Bademiya Colaba Mumbai", "lat": 18.9232, "lng": 72.8319, "type": "cafe", "city": "Mumbai"},
    {"name": "Irani Cafe Nagpur", "lat": 21.1466, "lng": 79.0849, "type": "cafe", "city": "Nagpur"},
    # ── More Landmarks & Towns ──
    {"name": "Lavasa City", "lat": 18.4052, "lng": 73.5058, "type": "town", "city": "Lavasa"},
    {"name": "Panchgani Hill Station", "lat": 17.9246, "lng": 73.7968, "type": "landmark", "city": "Panchgani"},
    {"name": "Matheran Hill Station", "lat": 18.9858, "lng": 73.2710, "type": "landmark", "city": "Matheran"},
    {"name": "Khandala Railway Station", "lat": 18.7630, "lng": 73.3740, "type": "railway_station", "city": "Khandala"},
    {"name": "Raigad Fort", "lat": 18.2353, "lng": 73.4479, "type": "landmark", "city": "Raigad"},
    {"name": "Pratapgad Fort", "lat": 17.9367, "lng": 73.5781, "type": "landmark", "city": "Satara"},
    {"name": "Lohagad Fort", "lat": 18.7094, "lng": 73.4750, "type": "landmark", "city": "Pune"},
    {"name": "Rajmachi Fort", "lat": 18.8310, "lng": 73.3930, "type": "landmark", "city": "Pune"},
    {"name": "Pandharpur Temple", "lat": 17.6781, "lng": 75.3263, "type": "landmark", "city": "Pandharpur"},
    {"name": "Tuljapur Tuljabhawani Temple", "lat": 18.0113, "lng": 76.0715, "type": "landmark", "city": "Tuljapur"},
    {"name": "Ashtavinayak Morgaon", "lat": 18.2672, "lng": 74.3528, "type": "landmark", "city": "Pune"},
    {"name": "Jejuri Khandoba Temple", "lat": 18.2740, "lng": 74.1570, "type": "landmark", "city": "Pune"},
    {"name": "Baramati Town", "lat": 18.1527, "lng": 74.5770, "type": "town", "city": "Baramati"},
    {"name": "Daund Junction Railway Station", "lat": 18.4650, "lng": 74.5800, "type": "railway_station", "city": "Daund"},
    {"name": "Talegaon Railway Station", "lat": 18.7340, "lng": 73.6760, "type": "railway_station", "city": "Talegaon"},
    {"name": "Lonand Town", "lat": 18.0140, "lng": 74.1820, "type": "town", "city": "Lonand"},
    {"name": "Wai Town", "lat": 17.9524, "lng": 73.8937, "type": "town", "city": "Wai"},
    {"name": "Karad ST Stand", "lat": 17.2875, "lng": 74.1851, "type": "st_bus_stand", "city": "Karad"},
    {"name": "Miraj Junction Railway Station", "lat": 16.8250, "lng": 74.6460, "type": "railway_station", "city": "Miraj"},
    {"name": "Malvan Beach", "lat": 16.0575, "lng": 73.4598, "type": "landmark", "city": "Malvan"},
    {"name": "Ganpatipule Beach Temple", "lat": 17.1448, "lng": 73.2680, "type": "landmark", "city": "Ganpatipule"},
    {"name": "Dapoli Town", "lat": 17.7580, "lng": 73.1863, "type": "town", "city": "Dapoli"},
    {"name": "Harihareshwar Beach", "lat": 17.9890, "lng": 73.0190, "type": "landmark", "city": "Harihareshwar"},
]

ALL_POIS: List[Dict[str, Any]] = PUNE_POIS + MUMBAI_POIS + NAGPUR_POIS + NASHIK_POIS + OTHER_POIS

# Extended POI dataset loaded from HuggingFace (filled on startup)
EXTENDED_POIS: List[Dict[str, Any]] = []

# Combined searchable POIs (hardcoded + extended)
SEARCHABLE_POIS: List[Dict[str, Any]] = list(ALL_POIS)

# ═══════════════════════════════════════════════════════════════
# Haversine Helper
# ═══════════════════════════════════════════════════════════════

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ═══════════════════════════════════════════════════════════════
# Overpass / Nominatim Place Fetcher with Caching
# ═══════════════════════════════════════════════════════════════

# In-memory cache for Overpass results
_places_cache: Dict[str, Any] = {}
_cache_file = "/app/cache/places_cache.json"

def _load_local_cache():
    global _places_cache
    try:
        if os.path.exists(_cache_file):
            with open(_cache_file, "r") as f:
                _places_cache = json.load(f)
            logger.info(f"Loaded {len(_places_cache)} cached place entries from disk")
    except Exception as e:
        logger.warning(f"Could not load local cache: {e}")

def _save_local_cache():
    try:
        os.makedirs(os.path.dirname(_cache_file), exist_ok=True)
        with open(_cache_file, "w") as f:
            json.dump(_places_cache, f)
    except Exception as e:
        logger.warning(f"Could not save local cache: {e}")


async def save_cache_to_hf():
    """Upload the places cache to HuggingFace Dataset for persistence."""
    if not HF_TOKEN:
        logger.warning("No HF_TOKEN — skipping dataset upload")
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=HF_TOKEN)
        cache_bytes = json.dumps(_places_cache, indent=2).encode("utf-8")
        api.upload_file(
            path_or_fileobj=cache_bytes,
            path_in_repo="places_cache.json",
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
        )
        logger.info(f"Uploaded places cache ({len(_places_cache)} entries) to HF dataset")
    except Exception as e:
        logger.warning(f"HF cache upload failed: {e}")


async def load_cache_from_hf():
    """Download the places cache from HuggingFace Dataset."""
    global _places_cache
    if not HF_TOKEN:
        return
    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=HF_DATASET_REPO,
            filename="places_cache.json",
            repo_type="dataset",
            token=HF_TOKEN,
        )
        with open(path, "r") as f:
            _places_cache = json.load(f)
        logger.info(f"Loaded {len(_places_cache)} entries from HF dataset cache")
    except Exception as e:
        logger.info(f"No HF cache found (first run?): {e}")


async def load_extended_pois_from_hf():
    """Download the massive POI dataset from HuggingFace Dataset."""
    global EXTENDED_POIS, SEARCHABLE_POIS
    if not HF_TOKEN:
        logger.info("No HF_TOKEN — extended POIs not loaded")
        return
    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=HF_DATASET_REPO,
            filename="maharashtra_pois.json",
            repo_type="dataset",
            token=HF_TOKEN,
        )
        with open(path, "r", encoding="utf-8") as f:
            EXTENDED_POIS = json.load(f)

        # Merge: hardcoded + extended, deduplicate by name+coords
        seen = set()
        combined = []
        for p in ALL_POIS:
            key = f"{p['name'].lower()}|{round(p['lat'],3)}|{round(p['lng'],3)}"
            if key not in seen:
                seen.add(key)
                combined.append(p)
        for p in EXTENDED_POIS:
            key = f"{p['name'].lower()}|{round(p['lat'],3)}|{round(p['lng'],3)}"
            if key not in seen:
                seen.add(key)
                combined.append(p)
        SEARCHABLE_POIS = combined
        logger.info(f"Loaded {len(EXTENDED_POIS)} extended POIs from HF → total searchable: {len(SEARCHABLE_POIS)}")
    except Exception as e:
        logger.info(f"No extended POI dataset found on HF: {e}")


async def fetch_overpass_places(
    lat: float, lng: float, radius: int = 5000,
    place_types: List[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch nearby places from Overpass API with caching."""
    if place_types is None:
        place_types = ["shop", "amenity", "railway", "highway", "bus_stop", "place"]

    cache_key = f"{lat:.3f},{lng:.3f},{radius},{','.join(sorted(place_types))}"
    if cache_key in _places_cache:
        cached = _places_cache[cache_key]
        if time.time() - cached.get("ts", 0) < 86400:  # 24h TTL
            return cached["data"]

    # Build Overpass query
    queries = []
    for pt in place_types:
        if pt == "shop":
            queries.append(f'node["shop"](around:{radius},{lat},{lng});')
        elif pt == "amenity":
            queries.append(f'node["amenity"~"hospital|school|college|fuel|bank|pharmacy|restaurant"](around:{radius},{lat},{lng});')
        elif pt == "railway":
            queries.append(f'node["railway"="station"](around:{radius},{lat},{lng});')
        elif pt == "bus_stop":
            queries.append(f'node["highway"="bus_stop"](around:{radius},{lat},{lng});')
            queries.append(f'node["amenity"="bus_station"](around:{radius},{lat},{lng});')
        elif pt == "highway":
            queries.append(f'way["highway"~"primary|secondary|tertiary"]["name"](around:{radius},{lat},{lng});')
        elif pt == "place":
            queries.append(f'node["place"~"suburb|neighbourhood|village"](around:{radius},{lat},{lng});')

    overpass_query = f"""[out:json][timeout:15];({' '.join(queries)});out center 200;"""

    places = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": overpass_query},
            )
            if resp.status_code == 200:
                data = resp.json()
                for el in data.get("elements", []):
                    name = el.get("tags", {}).get("name", "")
                    if not name:
                        continue
                    elat = el.get("lat") or el.get("center", {}).get("lat")
                    elng = el.get("lon") or el.get("center", {}).get("lon")
                    if not elat or not elng:
                        continue

                    # Determine type
                    tags = el.get("tags", {})
                    ptype = "shop"
                    if tags.get("railway"):
                        ptype = "railway_station"
                    elif tags.get("highway") == "bus_stop" or tags.get("amenity") == "bus_station":
                        ptype = "st_bus_stand"
                    elif tags.get("amenity") in ("hospital",):
                        ptype = "hospital"
                    elif tags.get("amenity") in ("school", "college", "university"):
                        ptype = "education"
                    elif tags.get("amenity") in ("fuel",):
                        ptype = "fuel"
                    elif tags.get("place"):
                        ptype = "colony"
                    elif tags.get("highway") in ("primary", "secondary", "tertiary"):
                        ptype = "road"
                    elif tags.get("shop"):
                        ptype = "shop"

                    places.append({
                        "name": name,
                        "lat": float(elat),
                        "lng": float(elng),
                        "type": ptype,
                        "source": "overpass",
                        "distance_km": haversine_km(lat, lng, float(elat), float(elng)),
                    })

                places.sort(key=lambda p: p["distance_km"])
                # Cache
                _places_cache[cache_key] = {"ts": time.time(), "data": places[:200]}
                _save_local_cache()
                logger.info(f"Fetched {len(places)} places from Overpass near ({lat},{lng})")

    except Exception as e:
        logger.warning(f"Overpass fetch failed: {e}")

    return places[:200]


async def search_nominatim(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for places using Nominatim geocoding."""
    results = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{query}, Maharashtra, India",
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                },
                headers={"User-Agent": "AUMOv3/1.0"},
            )
            if resp.status_code == 200:
                for item in resp.json():
                    results.append({
                        "name": item.get("display_name", ""),
                        "lat": float(item.get("lat", 0)),
                        "lng": float(item.get("lon", 0)),
                        "type": item.get("type", "place"),
                        "source": "nominatim",
                    })
    except Exception as e:
        logger.warning(f"Nominatim search failed: {e}")
    return results


# ═══════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════

class PlaceSearchRequest(BaseModel):
    query: str = ""
    lat: float = 0
    lng: float = 0
    radius_km: float = 5
    types: List[str] = []
    city: str = ""
    limit: int = 50

class NearbyRequest(BaseModel):
    lat: float
    lng: float
    radius: int = 5000
    types: List[str] = ["shop", "amenity", "railway", "bus_stop", "place"]

class POIMapRequest(BaseModel):
    south: float = 15.6
    north: float = 21.5
    west: float = 72.6
    east: float = 80.9
    types: List[str] = []
    limit: int = 200


# ═══════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AUMOv3.2 Data & Places Service",
    version="3.2.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("AUMOv3.2 Data Service starting...")
    _load_local_cache()
    await load_cache_from_hf()
    await load_extended_pois_from_hf()
    logger.info(f"Loaded {len(ALL_POIS)} hardcoded + {len(EXTENDED_POIS)} extended POIs = {len(SEARCHABLE_POIS)} total")
    logger.info(f"Cache entries: {len(_places_cache)}")
    logger.info("Data Service ready!")


# ─── Health ───────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "AUMOv3.2 Data & Places",
        "version": "3.2.0",
        "poi_count": len(SEARCHABLE_POIS),
        "cache_entries": len(_places_cache),
        "status": "healthy",
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "aumov3-data",
        "poi_count": len(SEARCHABLE_POIS),
        "cache_entries": len(_places_cache),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─── Place Search (combined POI + Overpass + Nominatim) ──────

@app.post("/api/places/search")
async def places_search(req: PlaceSearchRequest):
    """Search places combining hardcoded POIs, Overpass, and Nominatim."""
    results = []

    # 1. Search hardcoded POIs
    filtered = SEARCHABLE_POIS
    if req.query:
        q = req.query.lower()
        filtered = [p for p in filtered if q in p["name"].lower() or q in p.get("city", "").lower()]
    if req.city:
        c = req.city.lower()
        filtered = [p for p in filtered if p.get("city", "").lower() == c]
    if req.types:
        filtered = [p for p in filtered if p["type"] in req.types]
    if req.lat and req.lng:
        for p in filtered:
            p["distance_km"] = haversine_km(req.lat, req.lng, p["lat"], p["lng"])
        filtered = [p for p in filtered if p["distance_km"] <= req.radius_km]
        filtered.sort(key=lambda p: p["distance_km"])
    for p in filtered:
        p["source"] = "database"
    results.extend(filtered[:req.limit])

    # 2. If query and lat/lng, also search Overpass
    if req.lat and req.lng and len(results) < req.limit:
        overpass = await fetch_overpass_places(
            req.lat, req.lng,
            radius=int(req.radius_km * 1000),
            place_types=req.types if req.types else None,
        )
        # Filter by query if provided
        if req.query:
            q = req.query.lower()
            overpass = [p for p in overpass if q in p["name"].lower()]
        # Deduplicate by name similarity
        existing_names = {r["name"].lower() for r in results}
        for p in overpass:
            if p["name"].lower() not in existing_names:
                results.append(p)
                existing_names.add(p["name"].lower())
            if len(results) >= req.limit:
                break

    # 3. If still few results, try Nominatim
    if req.query and len(results) < 5:
        nominatim = await search_nominatim(req.query, limit=5)
        existing_names = {r["name"].lower()[:30] for r in results}
        for p in nominatim:
            short = p["name"].lower()[:30]
            if short not in existing_names:
                results.append(p)
                existing_names.add(short)

    return {
        "results": results[:req.limit],
        "total": len(results),
        "sources": ["database", "overpass", "nominatim"],
    }


@app.get("/api/places/search")
async def places_search_get(
    q: str = Query("", alias="query"),
    lat: float = 0,
    lng: float = 0,
    radius_km: float = 5,
    city: str = "",
    limit: int = 50,
):
    """GET version of place search."""
    return await places_search(PlaceSearchRequest(
        query=q, lat=lat, lng=lng, radius_km=radius_km, city=city, limit=limit,
    ))


# ─── Nearby Places (Overpass powered) ────────────────────────

@app.post("/api/places/nearby")
async def nearby_places(req: NearbyRequest):
    """Fetch nearby places from Overpass with caching."""
    places = await fetch_overpass_places(
        req.lat, req.lng, req.radius, req.types,
    )
    return {"places": places, "count": len(places)}


@app.get("/api/places/nearby")
async def nearby_places_get(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = 5000,
):
    """GET nearby places."""
    places = await fetch_overpass_places(lat, lng, radius)
    return {"places": places, "count": len(places)}


# ─── Stops near a location ───────────────────────────────────

@app.get("/api/places/stops")
async def nearby_stops(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: int = 3000,
):
    """Get bus stops, railway stations, and metro near a point."""
    stop_types = ["bus_stop", "railway"]
    places = await fetch_overpass_places(lat, lng, radius, stop_types)

    # Also add hardcoded stops
    hardcoded_stops = [
        p for p in SEARCHABLE_POIS
        if p["type"] in ("st_bus_stand", "bus_stop", "railway_station", "metro")
    ]
    for p in hardcoded_stops:
        dist = haversine_km(lat, lng, p["lat"], p["lng"])
        if dist <= radius / 1000:
            p_copy = {**p, "distance_km": dist, "source": "database"}
            places.append(p_copy)

    # Deduplicate & sort
    seen = set()
    unique = []
    for p in sorted(places, key=lambda x: x.get("distance_km", 999)):
        key = f"{p['lat']:.4f},{p['lng']:.4f}"
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return {"stops": unique[:50], "count": len(unique)}


# ─── POI Endpoints (hardcoded database) ──────────────────────

@app.get("/api/poi")
async def search_pois(
    query: str = "",
    type: str = "",
    city: str = "",
    lat: float = 0,
    lng: float = 0,
    radius_km: float = 50,
    limit: int = 50,
):
    """Search POIs from database."""
    results = SEARCHABLE_POIS

    if query:
        q = query.lower()
        results = [p for p in results if q in p["name"].lower()]
    if type:
        results = [p for p in results if p["type"] == type]
    if city:
        c = city.lower()
        results = [p for p in results if p.get("city", "").lower() == c]
    if lat and lng:
        for p in results:
            p["distance_km"] = haversine_km(lat, lng, p["lat"], p["lng"])
        results = [p for p in results if p["distance_km"] <= radius_km]
        results.sort(key=lambda p: p["distance_km"])

    return {"pois": results[:limit], "total": len(results)}


@app.post("/api/poi/map")
async def pois_for_map(req: POIMapRequest):
    """Get POIs within map bounds."""
    results = [
        p for p in SEARCHABLE_POIS
        if req.south <= p["lat"] <= req.north and req.west <= p["lng"] <= req.east
    ]
    if req.types:
        results = [p for p in results if p["type"] in req.types]
    return {"pois": results[:req.limit], "total": len(results)}


@app.get("/api/poi/types")
async def poi_types():
    """Return POI type definitions."""
    return {"types": POI_TYPES}


@app.get("/api/poi/cities")
async def poi_cities():
    """Return list of all cities with POIs."""
    cities = sorted(set(p.get("city", "Unknown") for p in SEARCHABLE_POIS))
    return {"cities": cities}


# ─── Cache Management ─────────────────────────────────────────

@app.post("/api/data/save-cache")
async def save_cache():
    """Save current places cache to HuggingFace Dataset."""
    await save_cache_to_hf()
    return {
        "message": "Cache saved to HuggingFace",
        "entries": len(_places_cache),
    }

@app.post("/api/data/refresh")
async def refresh_data():
    """Refresh cache by fetching places for major cities."""
    fetched = 0
    for city in PRELOAD_CITIES[:4]:  # Limit to 4 cities to avoid timeout
        try:
            places = await fetch_overpass_places(
                city["lat"], city["lng"], city["radius"],
            )
            fetched += len(places)
            logger.info(f"Refreshed {len(places)} places for {city['name']}")
            await asyncio.sleep(2)  # Rate limit
        except Exception as e:
            logger.warning(f"Failed to refresh {city['name']}: {e}")

    # Save to HF
    await save_cache_to_hf()

    return {
        "message": f"Refreshed {fetched} places across {len(PRELOAD_CITIES[:4])} cities",
        "cache_entries": len(_places_cache),
    }


@app.get("/api/data/stats")
async def data_stats():
    """Return data service statistics."""
    city_counts = {}
    for p in SEARCHABLE_POIS:
        c = p.get("city", "Unknown")
        city_counts[c] = city_counts.get(c, 0) + 1

    type_counts = {}
    for p in SEARCHABLE_POIS:
        t = p.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_pois": len(SEARCHABLE_POIS),
        "hardcoded_pois": len(ALL_POIS),
        "extended_pois": len(EXTENDED_POIS),
        "cache_entries": len(_places_cache),
        "cities": city_counts,
        "types": type_counts,
    }


# ═══════════════════════════════════════════════════════════════
# DATASET BUILDER — runs ON HuggingFace infrastructure
# ═══════════════════════════════════════════════════════════════

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BUILDER_STATUS = {"running": False, "progress": "", "category": "", "done": 0, "total": 0, "results": {}}

BUILDER_CATEGORIES = {
    "bus_stops": '[out:json][timeout:90];(node["highway"="bus_stop"]({bbox});node["amenity"="bus_station"]({bbox});node["public_transport"="stop_position"]["bus"="yes"]({bbox});node["public_transport"="platform"]["bus"="yes"]({bbox});way["amenity"="bus_station"]({bbox}););out center;',
    "railway_stations": '[out:json][timeout:90];(node["railway"="station"]({bbox});node["railway"="halt"]({bbox});way["railway"="station"]({bbox}););out center;',
    "metro_stations": '[out:json][timeout:90];(node["railway"="subway_entrance"]({bbox});node["station"="subway"]({bbox}););out center;',
    "airports": '[out:json][timeout:90];(node["aeroway"="aerodrome"]({bbox});way["aeroway"="aerodrome"]({bbox});node["aeroway"="terminal"]({bbox});node["aeroway"="helipad"]({bbox}););out center;',
    "police_stations": '[out:json][timeout:90];(node["amenity"="police"]({bbox});way["amenity"="police"]({bbox}););out center;',
    "fire_stations": '[out:json][timeout:90];(node["amenity"="fire_station"]({bbox});way["amenity"="fire_station"]({bbox}););out center;',
    "government": '[out:json][timeout:90];(node["office"="government"]({bbox});way["office"="government"]({bbox});node["amenity"="townhall"]({bbox});node["amenity"="courthouse"]({bbox}););out center;',
    "post_offices": '[out:json][timeout:90];(node["amenity"="post_office"]({bbox});way["amenity"="post_office"]({bbox}););out center;',
    "hospitals": '[out:json][timeout:90];(node["amenity"="hospital"]({bbox});way["amenity"="hospital"]({bbox});node["amenity"="clinic"]({bbox});node["amenity"="doctors"]({bbox}););out center;',
    "pharmacies": '[out:json][timeout:90];(node["amenity"="pharmacy"]({bbox});node["shop"="chemist"]({bbox}););out body;',
    "schools_colleges": '[out:json][timeout:90];(node["amenity"="school"]({bbox});way["amenity"="school"]({bbox});node["amenity"="college"]({bbox});way["amenity"="college"]({bbox});node["amenity"="university"]({bbox});way["amenity"="university"]({bbox});node["amenity"="library"]({bbox});way["amenity"="library"]({bbox}););out center;',
    "temples_worship": '[out:json][timeout:90];(node["amenity"="place_of_worship"]({bbox});way["amenity"="place_of_worship"]({bbox}););out center;',
    "shops_malls": '[out:json][timeout:90];(node["shop"="supermarket"]({bbox});node["shop"="mall"]({bbox});way["shop"="mall"]({bbox});node["shop"="convenience"]({bbox});node["shop"="general"]({bbox});node["shop"="clothes"]({bbox});node["shop"="electronics"]({bbox});node["shop"="bakery"]({bbox});node["shop"="mobile_phone"]({bbox});way["shop"="supermarket"]({bbox}););out center;',
    "cafes_restaurants": '[out:json][timeout:90];(node["amenity"="cafe"]({bbox});node["amenity"="restaurant"]({bbox});node["amenity"="fast_food"]({bbox});node["amenity"="food_court"]({bbox}););out body;',
    "banks_atm": '[out:json][timeout:90];(node["amenity"="bank"]({bbox});node["amenity"="atm"]({bbox});way["amenity"="bank"]({bbox}););out center;',
    "fuel_ev": '[out:json][timeout:90];(node["amenity"="fuel"]({bbox});node["amenity"="charging_station"]({bbox});way["amenity"="fuel"]({bbox}););out center;',
    "hotels_lodging": '[out:json][timeout:90];(node["tourism"="hotel"]({bbox});way["tourism"="hotel"]({bbox});node["tourism"="guest_house"]({bbox});node["tourism"="hostel"]({bbox}););out center;',
    "entertainment": '[out:json][timeout:90];(node["amenity"="cinema"]({bbox});way["amenity"="cinema"]({bbox});node["leisure"="stadium"]({bbox});way["leisure"="stadium"]({bbox});node["leisure"="sports_centre"]({bbox}););out center;',
    "parks_gardens": '[out:json][timeout:90];(node["leisure"="park"]({bbox});way["leisure"="park"]({bbox});node["leisure"="garden"]({bbox});way["leisure"="garden"]({bbox});node["tourism"="zoo"]({bbox}););out center;',
    "tourist_landmarks": '[out:json][timeout:90];(node["tourism"="attraction"]({bbox});way["tourism"="attraction"]({bbox});node["tourism"="museum"]({bbox});node["historic"="monument"]({bbox});way["historic"="monument"]({bbox});node["historic"="fort"]({bbox});way["historic"="fort"]({bbox}););out center;',
    "villages_towns": '[out:json][timeout:120];(node["place"="village"]({bbox});node["place"="town"]({bbox});node["place"="city"]({bbox});node["place"="suburb"]({bbox});node["place"="hamlet"]({bbox});node["place"="neighbourhood"]({bbox});node["place"="locality"]({bbox}););out body;',
    "roads_highways": '[out:json][timeout:180];(way["highway"="motorway"]["name"]({bbox});way["highway"="trunk"]["name"]({bbox});way["highway"="primary"]["name"]({bbox});way["highway"="secondary"]["name"]({bbox});way["highway"="tertiary"]["name"]({bbox});way["highway"="residential"]["name"]({bbox}););out center;',
    "colonies_residential": '[out:json][timeout:120];(way["landuse"="residential"]["name"]({bbox});relation["landuse"="residential"]["name"]({bbox}););out center;',
    "buildings_named": '[out:json][timeout:180];(way["building"]["name"]({bbox});node["building"]["name"]({bbox}););out center;',
    "industrial_commercial": '[out:json][timeout:120];(way["landuse"="industrial"]["name"]({bbox});way["landuse"="commercial"]["name"]({bbox});node["office"]["name"]({bbox}););out center;',
    "water_bodies": '[out:json][timeout:90];(way["natural"="water"]["name"]({bbox});way["waterway"="river"]["name"]({bbox});way["waterway"="canal"]["name"]({bbox}););out center;',
    "other_amenities": '[out:json][timeout:120];(node["amenity"="parking"]({bbox});node["amenity"="taxi"]({bbox});node["amenity"="car_repair"]({bbox});node["amenity"="marketplace"]({bbox});way["amenity"="marketplace"]({bbox});node["amenity"="community_centre"]({bbox}););out center;',
}

BUILDER_TAG_MAP = {
    "bus_stops": "bus_stop", "railway_stations": "railway_station", "metro_stations": "metro_station",
    "airports": "airport", "police_stations": "police_station", "fire_stations": "fire_station",
    "government": "government", "post_offices": "post_office", "hospitals": "hospital",
    "pharmacies": "pharmacy", "schools_colleges": "education", "temples_worship": "worship",
    "shops_malls": "shopping", "cafes_restaurants": "cafe", "banks_atm": "bank",
    "fuel_ev": "fuel_station", "hotels_lodging": "hotel", "entertainment": "entertainment",
    "parks_gardens": "park", "tourist_landmarks": "landmark", "villages_towns": "town",
    "roads_highways": "road", "colonies_residential": "colony", "buildings_named": "building",
    "industrial_commercial": "commercial", "water_bodies": "water", "other_amenities": "amenity",
}

BUILDER_CITY_CENTERS = [
    ("Pune", 18.52, 73.86), ("Mumbai", 19.08, 72.88), ("Nagpur", 21.15, 79.09),
    ("Nashik", 20.00, 73.79), ("Aurangabad", 19.88, 75.34), ("Thane", 19.22, 72.98),
    ("Kolhapur", 16.70, 74.24), ("Solapur", 17.68, 75.92), ("Amravati", 20.93, 77.78),
    ("Nanded", 19.16, 77.30), ("Sangli", 16.85, 74.56), ("Latur", 18.40, 76.57),
    ("Jalgaon", 21.01, 75.57), ("Akola", 20.71, 77.00), ("Chandrapur", 19.97, 79.30),
    ("Parbhani", 19.27, 76.78), ("Satara", 17.68, 74.00), ("Ratnagiri", 16.99, 73.30),
    ("Ahmednagar", 19.09, 74.74), ("Dhule", 20.90, 74.78), ("Navi Mumbai", 19.03, 73.03),
    ("Pimpri-Chinchwad", 18.63, 73.80), ("Vasai-Virar", 19.42, 72.84),
    ("Panvel", 18.99, 73.12), ("Jalna", 19.84, 75.88), ("Beed", 18.99, 75.76),
    ("Gondia", 21.46, 80.19), ("Yavatmal", 20.39, 78.12), ("Wardha", 20.74, 78.60),
    ("Baramati", 18.15, 74.58), ("Shirdi", 19.77, 74.48), ("Lonavala", 18.75, 73.41),
]


def _infer_city(lat, lng):
    min_d, nearest = float('inf'), "Maharashtra"
    for name, clat, clng in BUILDER_CITY_CENTERS:
        d = math.sqrt((lat - clat)**2 + (lng - clng)**2)
        if d < min_d:
            min_d, nearest = d, name
    return nearest if min_d < 0.5 else "Maharashtra"


def _make_grid(bbox_s, bbox_w, bbox_n, bbox_e, cell_lat=2.0, cell_lng=2.8):
    cells = []
    lat = bbox_s
    while lat < bbox_n:
        lng = bbox_w
        while lng < bbox_e:
            cells.append((lat, lng, min(lat + cell_lat, bbox_n), min(lng + cell_lng, bbox_e)))
            lng += cell_lng
        lat += cell_lat
    return cells


# Categories that are very large need grid splitting; others can use full bbox
_HEAVY_CATEGORIES = {"roads_highways", "buildings_named", "colonies_residential", "shops_malls", "villages_towns", "other_amenities", "schools_colleges", "cafes_restaurants", "temples_worship"}


async def _fetch_category(cat_name: str, query_tpl: str, bbox_str: str, cell_label: str = "") -> list:
    """Fetch one category for one bbox, with retries."""
    query = query_tpl.replace("{bbox}", bbox_str)
    pois = []
    retries = 0
    while retries < 3:
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(OVERPASS_URL, data={"data": query})
                if resp.status_code == 200:
                    elements = resp.json().get("elements", [])
                    for el in elements:
                        lat = el.get("lat") or el.get("center", {}).get("lat")
                        lng = el.get("lon") or el.get("center", {}).get("lon")
                        if not lat or not lng:
                            continue
                        tags = el.get("tags", {})
                        name = tags.get("name:en") or tags.get("name") or tags.get("operator") or tags.get("brand") or tags.get("ref") or f"{cat_name}_{el.get('id','x')}"
                        city = tags.get("addr:city") or tags.get("is_in:city") or _infer_city(lat, lng)
                        poi = {"name": name.strip(), "lat": round(lat, 6), "lng": round(lng, 6), "type": BUILDER_TAG_MAP.get(cat_name, cat_name), "city": str(city).strip(), "osm_id": el.get("id")}
                        if tags.get("addr:street"): poi["address"] = tags["addr:street"]
                        if tags.get("phone"): poi["phone"] = tags["phone"]
                        if tags.get("website"): poi["website"] = tags["website"]
                        pois.append(poi)
                    logger.info(f"[BUILDER] {cat_name}{cell_label}: {len(elements)} elements → {len(pois)} named POIs")
                    return pois
                elif resp.status_code in (429, 504, 503):
                    retries += 1
                    logger.warning(f"[BUILDER] {cat_name}{cell_label}: HTTP {resp.status_code}, retry {retries}")
                    await asyncio.sleep(30 * retries)
                else:
                    logger.warning(f"[BUILDER] {cat_name}{cell_label}: HTTP {resp.status_code}")
                    return pois
        except Exception as ex:
            retries += 1
            logger.warning(f"[BUILDER] {cat_name}{cell_label}: {ex}, retry {retries}")
            await asyncio.sleep(20 * retries)
    return pois


async def _run_dataset_builder():
    """Background task: fetch all categories from Overpass and upload to HF.
    Light categories → single query for full Maharashtra bbox.
    Heavy categories → split into grid cells (2°×2.8°).
    """
    global BUILDER_STATUS, EXTENDED_POIS, SEARCHABLE_POIS
    BUILDER_STATUS = {"running": True, "progress": "starting", "category": "", "done": 0, "total": len(BUILDER_CATEGORIES), "results": {}}
    full_bbox = (MH_BBOX["south"], MH_BBOX["west"], MH_BBOX["north"], MH_BBOX["east"])
    full_bbox_str = f"{full_bbox[0]},{full_bbox[1]},{full_bbox[2]},{full_bbox[3]}"
    grid_cells = _make_grid(*full_bbox)
    all_data = []
    cat_counts = {}

    for cat_idx, (cat_name, query_tpl) in enumerate(BUILDER_CATEGORIES.items()):
        BUILDER_STATUS["category"] = cat_name
        BUILDER_STATUS["done"] = cat_idx
        BUILDER_STATUS["progress"] = f"Fetching {cat_name} ({cat_idx+1}/{len(BUILDER_CATEGORIES)})"

        cat_pois = []
        if cat_name in _HEAVY_CATEGORIES:
            # Heavy category → split into grid cells
            logger.info(f"[BUILDER] {BUILDER_STATUS['progress']} across {len(grid_cells)} cells (heavy)")
            for ci, (s, w, n, e) in enumerate(grid_cells):
                cell_bbox = f"{s},{w},{n},{e}"
                pois = await _fetch_category(cat_name, query_tpl, cell_bbox, f" cell {ci+1}/{len(grid_cells)}")
                cat_pois.extend(pois)
                await asyncio.sleep(3)  # rate limit between cells
        else:
            # Light category → single query for full Maharashtra
            logger.info(f"[BUILDER] {BUILDER_STATUS['progress']} (full bbox)")
            cat_pois = await _fetch_category(cat_name, query_tpl, full_bbox_str)
            await asyncio.sleep(5)  # rate limit between categories

        cat_counts[cat_name] = len(cat_pois)
        all_data.extend(cat_pois)
        logger.info(f"[BUILDER] {cat_name}: {len(cat_pois):,} POIs")

    # Deduplicate
    BUILDER_STATUS["progress"] = "Deduplicating..."
    seen = set()
    final = []
    for p in all_data:
        key = f"{p['name'].lower().strip()}|{round(p['lat'],4)}|{round(p['lng'],4)}"
        if key not in seen:
            seen.add(key)
            final.append(p)

    logger.info(f"[BUILDER] Total: {len(all_data):,} raw → {len(final):,} unique")

    # Upload to HuggingFace
    BUILDER_STATUS["progress"] = "Uploading to HuggingFace..."
    if HF_TOKEN:
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=HF_TOKEN)
            data_bytes = json.dumps(final, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            api.upload_file(path_or_fileobj=data_bytes, path_in_repo="maharashtra_pois.json", repo_id=HF_DATASET_REPO, repo_type="dataset")
            stats = {"total_unique_places": len(final), "total_raw": len(all_data), "categories": cat_counts, "generated_at": datetime.utcnow().isoformat() + "Z"}
            stats_bytes = json.dumps(stats, indent=2).encode("utf-8")
            api.upload_file(path_or_fileobj=stats_bytes, path_in_repo="dataset_stats.json", repo_id=HF_DATASET_REPO, repo_type="dataset")
            logger.info(f"[BUILDER] Uploaded {len(final):,} POIs to {HF_DATASET_REPO}")
        except Exception as e:
            logger.error(f"[BUILDER] Upload failed: {e}")
    else:
        logger.warning("[BUILDER] No HF_TOKEN — skipping upload")

    # Reload into memory
    EXTENDED_POIS = final
    seen2 = set()
    combined = []
    for p in ALL_POIS:
        key = f"{p['name'].lower()}|{round(p['lat'],3)}|{round(p['lng'],3)}"
        if key not in seen2:
            seen2.add(key)
            combined.append(p)
    for p in EXTENDED_POIS:
        key = f"{p['name'].lower()}|{round(p['lat'],3)}|{round(p['lng'],3)}"
        if key not in seen2:
            seen2.add(key)
            combined.append(p)
    SEARCHABLE_POIS = combined
    logger.info(f"[BUILDER] Reloaded: {len(SEARCHABLE_POIS):,} total searchable POIs")

    BUILDER_STATUS.update({"running": False, "progress": "complete", "done": len(BUILDER_CATEGORIES), "results": {"total_unique": len(final), "total_raw": len(all_data), "categories": cat_counts}})


@app.post("/api/data/build-dataset")
async def build_dataset():
    """Trigger dataset build on HF server. Returns immediately, runs in background."""
    if BUILDER_STATUS.get("running"):
        return {"status": "already_running", "progress": BUILDER_STATUS["progress"], "category": BUILDER_STATUS["category"], "done": BUILDER_STATUS["done"], "total": BUILDER_STATUS["total"]}
    asyncio.create_task(_run_dataset_builder())
    return {"status": "started", "message": "Dataset builder started in background. Check /api/data/build-status for progress.", "categories": len(BUILDER_CATEGORIES)}


@app.get("/api/data/build-status")
async def build_status():
    """Check dataset build progress."""
    return BUILDER_STATUS


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
