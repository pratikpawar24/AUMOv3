"""Quick API test - writes results to file."""
import httpx, json, time, sys

DATA = "https://qrmanual-aumov3-2.hf.space"
ML = "https://qrmanual-aumov3-1.hf.space"
BE = "https://aumo3-backend.onrender.com"
T = 60
R = []
out = open("c:/Users/Pratik/Desktop/AUMO3/test_results.txt", "w", encoding="utf-8")

def p(s):
    print(s)
    out.write(s + "\n")

def t(n, m, u, **kw):
    try:
        r = httpx.request(m, u, timeout=T, **kw)
        s = r.status_code
        try: b = r.json()
        except: b = r.text[:200]
        ok = s < 400
        p(f"{'PASS' if ok else 'FAIL'} [{s}] {n}")
        if isinstance(b, dict):
            for k, v in list(b.items())[:5]:
                p(f"  {k}: {str(v)[:120]}")
        R.append((n, s, ok))
        return b
    except Exception as e:
        p(f"ERR  [---] {n}: {e}")
        R.append((n, 0, False))
        return None

p("AUMO3 API TEST RESULTS")
p("=" * 50)
p(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

# Data Service
p("\n--- DATA SERVICE ---")
t("Data Health", "GET", f"{DATA}/api/health")
t("Data Stats", "GET", f"{DATA}/api/data/stats")
t("POI Pune stations", "GET", f"{DATA}/api/poi", params={"query": "station", "city": "Pune", "limit": "3"})
t("POI Mumbai hospitals", "GET", f"{DATA}/api/poi", params={"query": "hospital", "city": "Mumbai", "limit": "3"})
t("POI Cities", "GET", f"{DATA}/api/poi/cities")
t("POI Types", "GET", f"{DATA}/api/poi/types")
t("Places Search", "POST", f"{DATA}/api/places/search", json={"query": "Shivajinagar Pune", "limit": 3})
t("Nearby Stops", "GET", f"{DATA}/api/places/stops", params={"lat": "18.52", "lng": "73.86", "radius": "3000"})

# ML Service
p("\n--- ML SERVICE ---")
t("ML Health", "GET", f"{ML}/api/health")
t("ML Root", "GET", f"{ML}/")
t("Traffic Predict", "POST", f"{ML}/api/traffic/predict", json={"segments": [{"lat": 18.52, "lng": 73.86, "hour": 9, "day_of_week": 2, "month": 6}]})

# Backend
p("\n--- BACKEND ---")
t("Backend Health", "GET", f"{BE}/api/health")

email = f"apitest{int(time.time())}@test.com"
reg = t("Register", "POST", f"{BE}/api/users/register", json={"name": "Tester", "email": email, "password": "Test1234!", "phone": "9999999999"})

tk = None
if reg and "token" in reg: tk = reg["token"]
if not tk:
    lg = t("Admin Login", "POST", f"{BE}/api/users/login", json={"email": "admin@aumo3.com", "password": "Admin123!"})
    if lg and "token" in lg: tk = lg["token"]

if tk:
    h = {"Authorization": f"Bearer {tk}"}
    t("Profile", "GET", f"{BE}/api/users/profile", headers=h)
    ride = t("Create Ride", "POST", f"{BE}/api/rides", json={
        "origin": {"lat": 18.53, "lng": 73.84, "address": "Shivajinagar Pune"},
        "destination": {"lat": 18.51, "lng": 73.81, "address": "Kothrud Pune"},
        "departureTime": "2026-06-15T09:00:00Z", "availableSeats": 3, "fare": 150,
        "vehicleName": "Honda City", "vehicleRegNo": "MH12AB1234",
        "distanceKm": 8.5, "durationMin": 25,
        "preferences": {"smoking": False, "music": True, "petFriendly": False, "quietRide": False}
    }, headers=h)
    t("List Rides", "GET", f"{BE}/api/rides", headers=h)
    t("Search Rides", "GET", f"{BE}/api/rides/search", params={"originLat":"18.53","originLng":"73.84","destLat":"18.51","destLng":"73.81","radius":"5"}, headers=h)
    if ride and "_id" in ride:
        t("Ride Detail", "GET", f"{BE}/api/rides/{ride['_id']}", headers=h)

# Summary
p("\n" + "=" * 50)
p("SUMMARY")
p("=" * 50)
ok = sum(1 for _,_,x in R if x)
fail = sum(1 for _,_,x in R if not x)
p(f"Total: {len(R)} | PASS: {ok} | FAIL: {fail}\n")
for n, s, x in R:
    p(f"  {'PASS' if x else 'FAIL'} [{s}] {n}")
p("=" * 50)
out.close()
print(f"\nResults saved to test_results.txt")
