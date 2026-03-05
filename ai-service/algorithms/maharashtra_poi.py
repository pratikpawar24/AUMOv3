"""
Maharashtra Points of Interest (POI) Database

Categories:
  - ST Bus Stands (MSRTC)
  - Railway Stations
  - Major Junctions / Chowks
  - Shopping Areas / Markets
  - Hospitals
  - Educational Institutions
  - Tourist / Landmarks
  - Metro Stations (Mumbai / Pune / Nagpur)
  - Petrol Pumps / EV Charging
  - Government Offices

Covers: Mumbai, Pune, Nagpur, Nashik, Aurangabad (Chhatrapati Sambhajinagar),
        Thane, Kolhapur, Solapur, Sangli, Satara, Ratnagiri, Nanded, Amravati,
        Latur, Akola, Jalgaon, Dhule, Ahmednagar, Parbhani, Beed, Sindhudurg,
        Wardha, Chandrapur, Gondia, Buldhana
"""

from typing import List, Dict, Any

# ═══════════════════════════════════════════════════════════════
# POI Type Definitions
# ═══════════════════════════════════════════════════════════════

POI_TYPES = {
    "st_bus_stand": {"icon": "bus", "color": "#E53E3E", "label": "ST Bus Stand"},
    "railway_station": {"icon": "train", "color": "#3182CE", "label": "Railway Station"},
    "junction": {"icon": "crosshairs", "color": "#DD6B20", "label": "Junction / Chowk"},
    "shop": {"icon": "shopping-cart", "color": "#38A169", "label": "Shopping Area"},
    "hospital": {"icon": "hospital", "color": "#E53E3E", "label": "Hospital"},
    "education": {"icon": "graduation-cap", "color": "#805AD5", "label": "Education"},
    "landmark": {"icon": "monument", "color": "#D69E2E", "label": "Landmark"},
    "metro": {"icon": "subway", "color": "#319795", "label": "Metro Station"},
    "fuel": {"icon": "gas-pump", "color": "#4A5568", "label": "Fuel / EV Charging"},
    "government": {"icon": "building", "color": "#2B6CB0", "label": "Government Office"},
}

# ═══════════════════════════════════════════════════════════════
# PUNE POIs
# ═══════════════════════════════════════════════════════════════

PUNE_POIS: List[Dict[str, Any]] = [
    # ST Bus Stands
    {"name": "Pune Station (Swargate) ST Stand", "lat": 18.5018, "lng": 73.8636, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Shivajinagar ST Stand", "lat": 18.5310, "lng": 73.8458, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Wakad Bus Stop", "lat": 18.5990, "lng": 73.7604, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Hadapsar ST Stand", "lat": 18.5089, "lng": 73.9260, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Katraj Bus Stop", "lat": 18.4577, "lng": 73.8660, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Nigdi ST Stand", "lat": 18.6518, "lng": 73.7711, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Kothrud Depot", "lat": 18.5074, "lng": 73.8077, "type": "st_bus_stand", "city": "Pune"},
    {"name": "Deccan Bus Stop", "lat": 18.5168, "lng": 73.8409, "type": "st_bus_stand", "city": "Pune"},

    # Railway Stations
    {"name": "Pune Junction Railway Station", "lat": 18.5285, "lng": 73.8743, "type": "railway_station", "city": "Pune"},
    {"name": "Shivajinagar Railway Station", "lat": 18.5341, "lng": 73.8498, "type": "railway_station", "city": "Pune"},
    {"name": "Khadki Railway Station", "lat": 18.5658, "lng": 73.8417, "type": "railway_station", "city": "Pune"},
    {"name": "Chinchwad Railway Station", "lat": 18.6270, "lng": 73.7936, "type": "railway_station", "city": "Pune"},
    {"name": "Pimpri Railway Station", "lat": 18.6225, "lng": 73.8039, "type": "railway_station", "city": "Pune"},
    {"name": "Hadapsar Railway Station", "lat": 18.4997, "lng": 73.9433, "type": "railway_station", "city": "Pune"},
    {"name": "Loni Railway Station", "lat": 18.5038, "lng": 73.9601, "type": "railway_station", "city": "Pune"},

    # Junctions
    {"name": "Swargate Chowk", "lat": 18.5018, "lng": 73.8636, "type": "junction", "city": "Pune"},
    {"name": "Nal Stop Junction", "lat": 18.5153, "lng": 73.8316, "type": "junction", "city": "Pune"},
    {"name": "Pune-Satara Road Junction", "lat": 18.4825, "lng": 73.8574, "type": "junction", "city": "Pune"},
    {"name": "Chandni Chowk", "lat": 18.5120, "lng": 73.8125, "type": "junction", "city": "Pune"},
    {"name": "Warje Junction", "lat": 18.4875, "lng": 73.7991, "type": "junction", "city": "Pune"},
    {"name": "Hinjewadi Chowk", "lat": 18.5912, "lng": 73.7389, "type": "junction", "city": "Pune"},
    {"name": "Kharadi Bypass Junction", "lat": 18.5512, "lng": 73.9406, "type": "junction", "city": "Pune"},
    {"name": "Magarpatta Road Junction", "lat": 18.5132, "lng": 73.9298, "type": "junction", "city": "Pune"},
    {"name": "University Circle", "lat": 18.5538, "lng": 73.8252, "type": "junction", "city": "Pune"},
    {"name": "Pune-Bangalore Highway Jn", "lat": 18.4710, "lng": 73.8462, "type": "junction", "city": "Pune"},

    # Shopping Areas
    {"name": "Laxmi Road Market", "lat": 18.5128, "lng": 73.8553, "type": "shop", "city": "Pune"},
    {"name": "MG Road Pune", "lat": 18.5158, "lng": 73.8790, "type": "shop", "city": "Pune"},
    {"name": "FC Road (Fergusson College Road)", "lat": 18.5252, "lng": 73.8397, "type": "shop", "city": "Pune"},
    {"name": "Phoenix Marketcity Pune", "lat": 18.5601, "lng": 73.9154, "type": "shop", "city": "Pune"},
    {"name": "Seasons Mall Magarpatta", "lat": 18.5145, "lng": 73.9283, "type": "shop", "city": "Pune"},
    {"name": "Westend Mall Aundh", "lat": 18.5627, "lng": 73.8075, "type": "shop", "city": "Pune"},
    {"name": "SGS Mall Pune Camp", "lat": 18.5116, "lng": 73.8837, "type": "shop", "city": "Pune"},
    {"name": "Appa Balwant Chowk", "lat": 18.5145, "lng": 73.8565, "type": "shop", "city": "Pune"},
    {"name": "Tulsi Baug", "lat": 18.5125, "lng": 73.8558, "type": "shop", "city": "Pune"},
    {"name": "Mandai Market", "lat": 18.5101, "lng": 73.8572, "type": "shop", "city": "Pune"},

    # Landmarks / Tourist
    {"name": "Shaniwar Wada", "lat": 18.5195, "lng": 73.8554, "type": "landmark", "city": "Pune"},
    {"name": "Aga Khan Palace", "lat": 18.5531, "lng": 73.9015, "type": "landmark", "city": "Pune"},
    {"name": "Sinhagad Fort", "lat": 18.3661, "lng": 73.7558, "type": "landmark", "city": "Pune"},
    {"name": "Dagdusheth Ganpati", "lat": 18.5168, "lng": 73.8562, "type": "landmark", "city": "Pune"},
    {"name": "Pataleshwar Cave Temple", "lat": 18.5290, "lng": 73.8510, "type": "landmark", "city": "Pune"},
    {"name": "Rajiv Gandhi Zoological Park", "lat": 18.4583, "lng": 73.8700, "type": "landmark", "city": "Pune"},

    # Hospitals
    {"name": "Sassoon General Hospital", "lat": 18.5230, "lng": 73.8729, "type": "hospital", "city": "Pune"},
    {"name": "Ruby Hall Clinic", "lat": 18.5336, "lng": 73.8816, "type": "hospital", "city": "Pune"},
    {"name": "Jehangir Hospital", "lat": 18.5332, "lng": 73.8754, "type": "hospital", "city": "Pune"},
    {"name": "Sahyadri Hospital", "lat": 18.5162, "lng": 73.8408, "type": "hospital", "city": "Pune"},
    {"name": "Deenanath Mangeshkar Hospital", "lat": 18.4986, "lng": 73.8132, "type": "hospital", "city": "Pune"},

    # Education
    {"name": "Savitribai Phule Pune University", "lat": 18.5538, "lng": 73.8252, "type": "education", "city": "Pune"},
    {"name": "Fergusson College", "lat": 18.5242, "lng": 73.8395, "type": "education", "city": "Pune"},
    {"name": "COEP Technological University", "lat": 18.5295, "lng": 73.8516, "type": "education", "city": "Pune"},
    {"name": "Symbiosis International University", "lat": 18.5733, "lng": 73.7723, "type": "education", "city": "Pune"},
    {"name": "MIT-WPU", "lat": 18.5142, "lng": 73.8070, "type": "education", "city": "Pune"},

    # Metro Stations (Pune Metro)
    {"name": "PCMC Metro Station", "lat": 18.6476, "lng": 73.8011, "type": "metro", "city": "Pune"},
    {"name": "Civil Court Metro Station", "lat": 18.5265, "lng": 73.8756, "type": "metro", "city": "Pune"},
    {"name": "Garware College Metro Station", "lat": 18.5168, "lng": 73.8409, "type": "metro", "city": "Pune"},
    {"name": "Vanaz Metro Station", "lat": 18.5082, "lng": 73.8022, "type": "metro", "city": "Pune"},
    {"name": "Ruby Hall Metro Station", "lat": 18.5336, "lng": 73.8816, "type": "metro", "city": "Pune"},
]

# ═══════════════════════════════════════════════════════════════
# MUMBAI POIs
# ═══════════════════════════════════════════════════════════════

MUMBAI_POIS: List[Dict[str, Any]] = [
    # ST Bus Stands
    {"name": "Mumbai Central ST Stand", "lat": 18.9690, "lng": 72.8190, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Borivali ST Stand", "lat": 19.2283, "lng": 72.8572, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Thane ST Stand", "lat": 19.1860, "lng": 72.9763, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Dadar ST Stand", "lat": 19.0176, "lng": 72.8435, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Kurla ST Stand", "lat": 19.0726, "lng": 72.8794, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Panvel ST Stand", "lat": 18.9925, "lng": 73.1106, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Vashi ST Stand", "lat": 19.0771, "lng": 72.9987, "type": "st_bus_stand", "city": "Mumbai"},
    {"name": "Kalyan ST Stand", "lat": 19.2395, "lng": 73.1305, "type": "st_bus_stand", "city": "Mumbai"},

    # Railway Stations
    {"name": "Chhatrapati Shivaji Maharaj Terminus (CST)", "lat": 18.9398, "lng": 72.8355, "type": "railway_station", "city": "Mumbai"},
    {"name": "Mumbai Central Station", "lat": 18.9690, "lng": 72.8190, "type": "railway_station", "city": "Mumbai"},
    {"name": "Dadar Station", "lat": 19.0176, "lng": 72.8435, "type": "railway_station", "city": "Mumbai"},
    {"name": "Bandra Terminus", "lat": 19.0544, "lng": 72.8403, "type": "railway_station", "city": "Mumbai"},
    {"name": "Lokmanya Tilak Terminus (LTT)", "lat": 19.0692, "lng": 72.8891, "type": "railway_station", "city": "Mumbai"},
    {"name": "Andheri Station", "lat": 19.1197, "lng": 72.8464, "type": "railway_station", "city": "Mumbai"},
    {"name": "Churchgate Station", "lat": 18.9350, "lng": 72.8276, "type": "railway_station", "city": "Mumbai"},
    {"name": "Borivali Station", "lat": 19.2283, "lng": 72.8572, "type": "railway_station", "city": "Mumbai"},
    {"name": "Thane Station", "lat": 19.1860, "lng": 72.9763, "type": "railway_station", "city": "Mumbai"},
    {"name": "Kalyan Station", "lat": 19.2395, "lng": 73.1305, "type": "railway_station", "city": "Mumbai"},

    # Junctions
    {"name": "Dadar Junction (TT Circle)", "lat": 19.0176, "lng": 72.8435, "type": "junction", "city": "Mumbai"},
    {"name": "Sion Circle", "lat": 19.0413, "lng": 72.8622, "type": "junction", "city": "Mumbai"},
    {"name": "Haji Ali Junction", "lat": 18.9827, "lng": 72.8126, "type": "junction", "city": "Mumbai"},
    {"name": "Andheri Subway Junction", "lat": 19.1197, "lng": 72.8464, "type": "junction", "city": "Mumbai"},
    {"name": "Mahim Causeway", "lat": 19.0400, "lng": 72.8404, "type": "junction", "city": "Mumbai"},
    {"name": "JJ Flyover Junction", "lat": 18.9650, "lng": 72.8340, "type": "junction", "city": "Mumbai"},
    {"name": "Mankhurd Junction", "lat": 19.0461, "lng": 72.9337, "type": "junction", "city": "Mumbai"},
    {"name": "Teen Hath Naka Thane", "lat": 19.1967, "lng": 72.9635, "type": "junction", "city": "Mumbai"},
    {"name": "Ghodbunder Road Junction", "lat": 19.2340, "lng": 72.9557, "type": "junction", "city": "Mumbai"},
    {"name": "Western Express Highway Jn Goregaon", "lat": 19.1553, "lng": 72.8495, "type": "junction", "city": "Mumbai"},

    # Shopping
    {"name": "Crawford Market", "lat": 18.9475, "lng": 72.8332, "type": "shop", "city": "Mumbai"},
    {"name": "Linking Road Bandra", "lat": 19.0595, "lng": 72.8356, "type": "shop", "city": "Mumbai"},
    {"name": "Colaba Causeway", "lat": 18.9192, "lng": 72.8321, "type": "shop", "city": "Mumbai"},
    {"name": "High Street Phoenix Lower Parel", "lat": 18.9947, "lng": 72.8283, "type": "shop", "city": "Mumbai"},
    {"name": "R City Mall Ghatkopar", "lat": 19.0863, "lng": 72.9158, "type": "shop", "city": "Mumbai"},
    {"name": "Inorbit Mall Malad", "lat": 19.1779, "lng": 72.8396, "type": "shop", "city": "Mumbai"},
    {"name": "Hill Road Bandra", "lat": 19.0548, "lng": 72.8355, "type": "shop", "city": "Mumbai"},
    {"name": "Chor Bazaar", "lat": 18.9598, "lng": 72.8310, "type": "shop", "city": "Mumbai"},

    # Landmarks
    {"name": "Gateway of India", "lat": 18.9220, "lng": 72.8347, "type": "landmark", "city": "Mumbai"},
    {"name": "Marine Drive", "lat": 18.9432, "lng": 72.8235, "type": "landmark", "city": "Mumbai"},
    {"name": "Siddhivinayak Temple", "lat": 19.0170, "lng": 72.8310, "type": "landmark", "city": "Mumbai"},
    {"name": "Bandra-Worli Sea Link", "lat": 19.0300, "lng": 72.8165, "type": "landmark", "city": "Mumbai"},
    {"name": "Juhu Beach", "lat": 19.0988, "lng": 72.8267, "type": "landmark", "city": "Mumbai"},
    {"name": "Haji Ali Dargah", "lat": 18.9827, "lng": 72.8090, "type": "landmark", "city": "Mumbai"},

    # Metro Stations (Mumbai Metro)
    {"name": "Versova Metro", "lat": 19.1312, "lng": 72.8201, "type": "metro", "city": "Mumbai"},
    {"name": "Andheri Metro", "lat": 19.1197, "lng": 72.8464, "type": "metro", "city": "Mumbai"},
    {"name": "Ghatkopar Metro", "lat": 19.0868, "lng": 72.9086, "type": "metro", "city": "Mumbai"},
    {"name": "DN Nagar Metro", "lat": 19.1267, "lng": 72.8355, "type": "metro", "city": "Mumbai"},
    {"name": "Marol Naka Metro", "lat": 19.1107, "lng": 72.8802, "type": "metro", "city": "Mumbai"},
]

# ═══════════════════════════════════════════════════════════════
# NAGPUR POIs
# ═══════════════════════════════════════════════════════════════

NAGPUR_POIS: List[Dict[str, Any]] = [
    {"name": "Nagpur ST Stand (Ganeshpeth)", "lat": 21.1431, "lng": 79.0918, "type": "st_bus_stand", "city": "Nagpur"},
    {"name": "Nagpur Railway Station", "lat": 21.1504, "lng": 79.0870, "type": "railway_station", "city": "Nagpur"},
    {"name": "Sitabuldi Junction", "lat": 21.1466, "lng": 79.0849, "type": "junction", "city": "Nagpur"},
    {"name": "Variety Square", "lat": 21.1479, "lng": 79.0737, "type": "junction", "city": "Nagpur"},
    {"name": "LAD Chowk", "lat": 21.1401, "lng": 79.0715, "type": "junction", "city": "Nagpur"},
    {"name": "Dharampeth Market", "lat": 21.1490, "lng": 79.0680, "type": "shop", "city": "Nagpur"},
    {"name": "Sadar Bazaar Nagpur", "lat": 21.1466, "lng": 79.0849, "type": "shop", "city": "Nagpur"},
    {"name": "Empress Mall Nagpur", "lat": 21.1429, "lng": 79.0684, "type": "shop", "city": "Nagpur"},
    {"name": "Futala Lake", "lat": 21.1553, "lng": 79.0479, "type": "landmark", "city": "Nagpur"},
    {"name": "Deekshabhoomi", "lat": 21.1370, "lng": 79.0715, "type": "landmark", "city": "Nagpur"},
    {"name": "Zero Mile Nagpur", "lat": 21.1480, "lng": 79.0816, "type": "landmark", "city": "Nagpur"},
    {"name": "Nagpur Metro Sitabuldi", "lat": 21.1466, "lng": 79.0849, "type": "metro", "city": "Nagpur"},
    {"name": "Nagpur Metro Kasturchand Park", "lat": 21.1431, "lng": 79.0918, "type": "metro", "city": "Nagpur"},
    {"name": "AIIMS Nagpur", "lat": 21.1204, "lng": 79.0430, "type": "hospital", "city": "Nagpur"},
    {"name": "VNIT Nagpur", "lat": 21.1264, "lng": 79.0513, "type": "education", "city": "Nagpur"},
    {"name": "IIM Nagpur", "lat": 21.1290, "lng": 79.0481, "type": "education", "city": "Nagpur"},
]

# ═══════════════════════════════════════════════════════════════
# NASHIK POIs
# ═══════════════════════════════════════════════════════════════

NASHIK_POIS: List[Dict[str, Any]] = [
    {"name": "Nashik CBS (Central Bus Stand)", "lat": 19.9975, "lng": 73.7898, "type": "st_bus_stand", "city": "Nashik"},
    {"name": "Nashik Road ST Stand", "lat": 19.9698, "lng": 73.7994, "type": "st_bus_stand", "city": "Nashik"},
    {"name": "Nashik Road Railway Station", "lat": 19.9698, "lng": 73.7994, "type": "railway_station", "city": "Nashik"},
    {"name": "Dwarka Circle", "lat": 19.9972, "lng": 73.7770, "type": "junction", "city": "Nashik"},
    {"name": "College Road Junction", "lat": 20.0026, "lng": 73.7899, "type": "junction", "city": "Nashik"},
    {"name": "Panchavati", "lat": 20.0067, "lng": 73.7880, "type": "landmark", "city": "Nashik"},
    {"name": "Trimbakeshwar Temple", "lat": 19.9322, "lng": 73.5310, "type": "landmark", "city": "Nashik"},
    {"name": "Sula Vineyards", "lat": 20.0050, "lng": 73.7600, "type": "landmark", "city": "Nashik"},
    {"name": "City Center Mall Nashik", "lat": 20.0050, "lng": 73.7920, "type": "shop", "city": "Nashik"},
    {"name": "Nashik Municipal Hospital", "lat": 20.0000, "lng": 73.7880, "type": "hospital", "city": "Nashik"},
]

# ═══════════════════════════════════════════════════════════════
# AURANGABAD (Chhatrapati Sambhajinagar) POIs
# ═══════════════════════════════════════════════════════════════

AURANGABAD_POIS: List[Dict[str, Any]] = [
    {"name": "Aurangabad CBS", "lat": 19.8762, "lng": 75.3433, "type": "st_bus_stand", "city": "Aurangabad"},
    {"name": "Aurangabad Railway Station", "lat": 19.8724, "lng": 75.3213, "type": "railway_station", "city": "Aurangabad"},
    {"name": "Kranti Chowk", "lat": 19.8762, "lng": 75.3433, "type": "junction", "city": "Aurangabad"},
    {"name": "Mondha Junction", "lat": 19.8820, "lng": 75.3385, "type": "junction", "city": "Aurangabad"},
    {"name": "Prozone Mall Aurangabad", "lat": 19.8650, "lng": 75.3115, "type": "shop", "city": "Aurangabad"},
    {"name": "Ajanta Caves", "lat": 20.5519, "lng": 75.7033, "type": "landmark", "city": "Aurangabad"},
    {"name": "Ellora Caves", "lat": 20.0268, "lng": 75.1790, "type": "landmark", "city": "Aurangabad"},
    {"name": "Bibi Ka Maqbara", "lat": 19.9018, "lng": 75.3210, "type": "landmark", "city": "Aurangabad"},
    {"name": "Daulatabad Fort", "lat": 19.9419, "lng": 75.2132, "type": "landmark", "city": "Aurangabad"},
    {"name": "MGM Hospital Aurangabad", "lat": 19.8895, "lng": 75.3245, "type": "hospital", "city": "Aurangabad"},
]

# ═══════════════════════════════════════════════════════════════
# KOLHAPUR POIs
# ═══════════════════════════════════════════════════════════════

KOLHAPUR_POIS: List[Dict[str, Any]] = [
    {"name": "Kolhapur CBS", "lat": 16.7050, "lng": 74.2433, "type": "st_bus_stand", "city": "Kolhapur"},
    {"name": "Kolhapur Railway Station", "lat": 16.6940, "lng": 74.2298, "type": "railway_station", "city": "Kolhapur"},
    {"name": "Mahadwar Road Junction", "lat": 16.7047, "lng": 74.2380, "type": "junction", "city": "Kolhapur"},
    {"name": "Rajarampuri Junction", "lat": 16.6930, "lng": 74.2290, "type": "junction", "city": "Kolhapur"},
    {"name": "Mahalaxmi Temple Kolhapur", "lat": 16.7058, "lng": 74.2310, "type": "landmark", "city": "Kolhapur"},
    {"name": "Rankala Lake", "lat": 16.6918, "lng": 74.2160, "type": "landmark", "city": "Kolhapur"},
    {"name": "New Palace Kolhapur", "lat": 16.6996, "lng": 74.2248, "type": "landmark", "city": "Kolhapur"},
    {"name": "DYP Mall Kolhapur", "lat": 16.6890, "lng": 74.2155, "type": "shop", "city": "Kolhapur"},
    {"name": "CPR Hospital Kolhapur", "lat": 16.7018, "lng": 74.2323, "type": "hospital", "city": "Kolhapur"},
]

# ═══════════════════════════════════════════════════════════════
# SOLAPUR POIs
# ═══════════════════════════════════════════════════════════════

SOLAPUR_POIS: List[Dict[str, Any]] = [
    {"name": "Solapur CBS", "lat": 17.6599, "lng": 75.9064, "type": "st_bus_stand", "city": "Solapur"},
    {"name": "Solapur Railway Station", "lat": 17.6559, "lng": 75.9048, "type": "railway_station", "city": "Solapur"},
    {"name": "Siddheshwar Temple", "lat": 17.6730, "lng": 75.9150, "type": "landmark", "city": "Solapur"},
    {"name": "Main Market Solapur", "lat": 17.6600, "lng": 75.9070, "type": "shop", "city": "Solapur"},
    {"name": "Solapur Cantonment Junction", "lat": 17.6615, "lng": 75.9100, "type": "junction", "city": "Solapur"},
    {"name": "Government Hospital Solapur", "lat": 17.6580, "lng": 75.9020, "type": "hospital", "city": "Solapur"},
]

# ═══════════════════════════════════════════════════════════════
# OTHER MAHARASHTRA CITIES
# ═══════════════════════════════════════════════════════════════

OTHER_MAHARASHTRA_POIS: List[Dict[str, Any]] = [
    # Sangli
    {"name": "Sangli ST Stand", "lat": 16.8524, "lng": 74.5815, "type": "st_bus_stand", "city": "Sangli"},
    {"name": "Sangli Railway Station", "lat": 16.8546, "lng": 74.5696, "type": "railway_station", "city": "Sangli"},
    {"name": "Ganapati Galli Sangli", "lat": 16.8540, "lng": 74.5750, "type": "shop", "city": "Sangli"},

    # Satara
    {"name": "Satara CBS", "lat": 17.6805, "lng": 74.0183, "type": "st_bus_stand", "city": "Satara"},
    {"name": "Satara Railway Station", "lat": 17.6770, "lng": 74.0050, "type": "railway_station", "city": "Satara"},
    {"name": "Ajinkyatara Fort", "lat": 17.6640, "lng": 74.0110, "type": "landmark", "city": "Satara"},
    {"name": "Kaas Plateau", "lat": 17.7221, "lng": 73.8167, "type": "landmark", "city": "Satara"},

    # Ratnagiri
    {"name": "Ratnagiri ST Stand", "lat": 16.9902, "lng": 73.3120, "type": "st_bus_stand", "city": "Ratnagiri"},
    {"name": "Ratnagiri Railway Station", "lat": 16.9940, "lng": 73.2873, "type": "railway_station", "city": "Ratnagiri"},
    {"name": "Ratnagiri Fort", "lat": 16.9835, "lng": 73.2780, "type": "landmark", "city": "Ratnagiri"},
    {"name": "Jaigad Fort", "lat": 17.3018, "lng": 73.2164, "type": "landmark", "city": "Ratnagiri"},

    # Nanded
    {"name": "Nanded CBS", "lat": 19.1596, "lng": 77.3154, "type": "st_bus_stand", "city": "Nanded"},
    {"name": "Nanded Railway Station", "lat": 19.1570, "lng": 77.3110, "type": "railway_station", "city": "Nanded"},
    {"name": "Sachkhand Gurudwara Hazur Sahib", "lat": 19.1568, "lng": 77.3204, "type": "landmark", "city": "Nanded"},

    # Amravati
    {"name": "Amravati ST Stand", "lat": 20.9320, "lng": 77.7523, "type": "st_bus_stand", "city": "Amravati"},
    {"name": "Amravati Railway Station", "lat": 20.9306, "lng": 77.7504, "type": "railway_station", "city": "Amravati"},
    {"name": "Ambadevi Temple", "lat": 20.9330, "lng": 77.7530, "type": "landmark", "city": "Amravati"},

    # Latur
    {"name": "Latur CBS", "lat": 18.3980, "lng": 76.5606, "type": "st_bus_stand", "city": "Latur"},
    {"name": "Latur Railway Station", "lat": 18.3942, "lng": 76.5657, "type": "railway_station", "city": "Latur"},

    # Akola
    {"name": "Akola ST Stand", "lat": 20.7091, "lng": 77.0029, "type": "st_bus_stand", "city": "Akola"},
    {"name": "Akola Railway Station", "lat": 20.7050, "lng": 76.9981, "type": "railway_station", "city": "Akola"},

    # Jalgaon
    {"name": "Jalgaon CBS", "lat": 21.0077, "lng": 75.5626, "type": "st_bus_stand", "city": "Jalgaon"},
    {"name": "Jalgaon Railway Station", "lat": 21.0051, "lng": 75.5665, "type": "railway_station", "city": "Jalgaon"},

    # Dhule
    {"name": "Dhule CBS", "lat": 20.9042, "lng": 74.7749, "type": "st_bus_stand", "city": "Dhule"},
    {"name": "Dhule Railway Station", "lat": 20.8961, "lng": 74.7671, "type": "railway_station", "city": "Dhule"},

    # Ahmednagar
    {"name": "Ahmednagar CBS", "lat": 19.0948, "lng": 74.7480, "type": "st_bus_stand", "city": "Ahmednagar"},
    {"name": "Ahmednagar Railway Station", "lat": 19.0880, "lng": 74.7420, "type": "railway_station", "city": "Ahmednagar"},
    {"name": "Shirdi Sai Baba Temple", "lat": 19.7664, "lng": 74.4766, "type": "landmark", "city": "Ahmednagar"},

    # Parbhani
    {"name": "Parbhani ST Stand", "lat": 19.2609, "lng": 76.7747, "type": "st_bus_stand", "city": "Parbhani"},
    {"name": "Parbhani Railway Station", "lat": 19.2637, "lng": 76.7747, "type": "railway_station", "city": "Parbhani"},

    # Chandrapur
    {"name": "Chandrapur CBS", "lat": 19.9615, "lng": 79.2961, "type": "st_bus_stand", "city": "Chandrapur"},
    {"name": "Chandrapur Railway Station", "lat": 19.9590, "lng": 79.2980, "type": "railway_station", "city": "Chandrapur"},
    {"name": "Tadoba Tiger Reserve", "lat": 20.2410, "lng": 79.3650, "type": "landmark", "city": "Chandrapur"},

    # Wardha
    {"name": "Wardha CBS", "lat": 20.7452, "lng": 78.6022, "type": "st_bus_stand", "city": "Wardha"},
    {"name": "Wardha Railway Station", "lat": 20.7470, "lng": 78.6110, "type": "railway_station", "city": "Wardha"},
    {"name": "Sevagram Ashram", "lat": 20.7282, "lng": 78.6652, "type": "landmark", "city": "Wardha"},

    # Sindhudurg
    {"name": "Kudal ST Stand", "lat": 16.0161, "lng": 73.6854, "type": "st_bus_stand", "city": "Sindhudurg"},
    {"name": "Sindhudurg Fort", "lat": 16.0412, "lng": 73.4629, "type": "landmark", "city": "Sindhudurg"},
    {"name": "Tarkarli Beach", "lat": 16.0240, "lng": 73.4676, "type": "landmark", "city": "Sindhudurg"},

    # Lonavala / Maval (Tourist)
    {"name": "Lonavala ST Stand", "lat": 18.7546, "lng": 73.4062, "type": "st_bus_stand", "city": "Lonavala"},
    {"name": "Lonavala Railway Station", "lat": 18.7503, "lng": 73.4078, "type": "railway_station", "city": "Lonavala"},
    {"name": "Bhushi Dam", "lat": 18.7422, "lng": 73.3990, "type": "landmark", "city": "Lonavala"},
    {"name": "Tiger Point Lonavala", "lat": 18.7330, "lng": 73.3760, "type": "landmark", "city": "Lonavala"},

    # Mahabaleshwar
    {"name": "Mahabaleshwar ST Stand", "lat": 17.9237, "lng": 73.6586, "type": "st_bus_stand", "city": "Mahabaleshwar"},
    {"name": "Mapro Garden", "lat": 17.9440, "lng": 73.6445, "type": "shop", "city": "Mahabaleshwar"},
    {"name": "Arthur's Seat Point", "lat": 17.9547, "lng": 73.6377, "type": "landmark", "city": "Mahabaleshwar"},
    {"name": "Pratapgad Fort", "lat": 17.9339, "lng": 73.5806, "type": "landmark", "city": "Mahabaleshwar"},

    # Alibaug
    {"name": "Alibaug ST Stand", "lat": 18.6414, "lng": 72.8760, "type": "st_bus_stand", "city": "Alibaug"},
    {"name": "Alibaug Beach", "lat": 18.6398, "lng": 72.8715, "type": "landmark", "city": "Alibaug"},
    {"name": "Kolaba Fort Alibaug", "lat": 18.6265, "lng": 72.8668, "type": "landmark", "city": "Alibaug"},
]

# ═══════════════════════════════════════════════════════════════
# Aggregated POI Database
# ═══════════════════════════════════════════════════════════════

ALL_MAHARASHTRA_POIS: List[Dict[str, Any]] = (
    PUNE_POIS + MUMBAI_POIS + NAGPUR_POIS + NASHIK_POIS +
    AURANGABAD_POIS + KOLHAPUR_POIS + SOLAPUR_POIS + OTHER_MAHARASHTRA_POIS
)


def search_pois(
    query: str = "",
    poi_type: str = "",
    city: str = "",
    lat: float = 0,
    lng: float = 0,
    radius_km: float = 50,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Search POIs with filtering and proximity sorting."""
    from utils.haversine import haversine_km

    results = ALL_MAHARASHTRA_POIS

    if query:
        q = query.lower()
        results = [p for p in results if q in p["name"].lower()]

    if poi_type:
        results = [p for p in results if p["type"] == poi_type]

    if city:
        c = city.lower()
        results = [p for p in results if p["city"].lower() == c]

    if lat != 0 and lng != 0:
        for poi in results:
            poi["distance_km"] = haversine_km(lat, lng, poi["lat"], poi["lng"])
        results = [p for p in results if p["distance_km"] <= radius_km]
        results.sort(key=lambda p: p["distance_km"])

    return results[:limit]


def get_pois_for_map(
    bounds: Dict[str, float] = None,
    types: List[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Get POIs within map bounds for rendering on Leaflet."""
    results = ALL_MAHARASHTRA_POIS

    if bounds:
        results = [
            p for p in results
            if bounds.get("south", -90) <= p["lat"] <= bounds.get("north", 90)
            and bounds.get("west", -180) <= p["lng"] <= bounds.get("east", 180)
        ]

    if types:
        results = [p for p in results if p["type"] in types]

    return results[:limit]


def get_poi_types() -> Dict[str, Dict]:
    """Return POI type definitions for frontend icon rendering."""
    return POI_TYPES


def get_cities() -> List[str]:
    """Return list of all cities with POIs."""
    return sorted(set(p["city"] for p in ALL_MAHARASHTRA_POIS))
