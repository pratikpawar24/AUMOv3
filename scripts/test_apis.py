"""
AUMO3 End-to-End API Tester
============================
Tests all endpoints across all services.
"""
import httpx
import json
import time
import sys

# ── Service URLs ──
GATEWAY_URL = "https://qrmanual-aumov3.hf.space"
ML_URL = "https://qrmanual-aumov3-1.hf.space"
DATA_URL = "https://qrmanual-aumov3-2.hf.space"
BACKEND_URL = "https://aumo3-backend.onrender.com"

TIMEOUT = 60  # seconds

results = []

def test(name, method, url, **kwargs):
    """Run a test and print result."""
    print(f"\n{'─'*60}")
    print(f"TEST: {name}")
    print(f"  {method} {url}")
    try:
        if method == "GET":
            r = httpx.get(url, timeout=TIMEOUT, **kwargs)
        elif method == "POST":
            r = httpx.post(url, timeout=TIMEOUT, **kwargs)
        elif method == "PUT":
            r = httpx.put(url, timeout=TIMEOUT, **kwargs)
        else:
            r = httpx.get(url, timeout=TIMEOUT, **kwargs)

        status = r.status_code
        try:
            body = r.json()
        except:
            body = r.text[:500]

        passed = status < 400
        symbol = "✅" if passed else "❌"
        print(f"  {symbol} Status: {status}")
        if isinstance(body, dict):
            # Print first level keys and truncated values
            for k, v in body.items():
                sv = str(v)
                if len(sv) > 200:
                    sv = sv[:200] + "..."
                print(f"    {k}: {sv}")
        elif isinstance(body, list):
            print(f"    [{len(body)} items]")
            if body:
                print(f"    First: {str(body[0])[:200]}")
        else:
            print(f"    {str(body)[:500]}")

        results.append({"name": name, "status": status, "passed": passed})
        return body
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        results.append({"name": name, "status": 0, "passed": False, "error": str(e)})
        return None


def main():
    print("=" * 60)
    print("  AUMO3 END-TO-END API TEST SUITE")
    print("=" * 60)

    # ━━━ 1. HEALTH CHECKS ━━━
    print("\n\n═══ SECTION 1: HEALTH CHECKS ═══")

    test("Gateway Health", "GET", f"{GATEWAY_URL}/api/health")
    test("ML Service Health", "GET", f"{ML_URL}/api/health")
    test("Data Service Health", "GET", f"{DATA_URL}/api/health")
    test("Backend Health", "GET", f"{BACKEND_URL}/api/health")

    # ━━━ 2. DATA SERVICE ━━━
    print("\n\n═══ SECTION 2: DATA SERVICE ═══")

    test("Data Stats", "GET", f"{DATA_URL}/api/data/stats")

    test("POI Search - Pune stations", "GET",
         f"{DATA_URL}/api/poi", params={"query": "station", "city": "Pune", "limit": "5"})

    test("POI Search - Mumbai hospitals", "GET",
         f"{DATA_URL}/api/poi", params={"query": "hospital", "city": "Mumbai", "limit": "5"})

    test("POI Cities", "GET", f"{DATA_URL}/api/poi/cities")

    test("POI Map Data", "GET",
         f"{DATA_URL}/api/poi/map", params={"city": "Pune", "limit": "10"})

    test("Places Search - Pune", "POST",
         f"{DATA_URL}/api/places/search",
         json={"query": "Shivajinagar Pune", "limit": 5})

    test("Nearby Stops - Pune center", "POST",
         f"{DATA_URL}/api/places/nearby-stops",
         json={"lat": 18.5204, "lng": 73.8567, "radius": 3000, "limit": 5})

    # ━━━ 3. ML SERVICE ━━━
    print("\n\n═══ SECTION 3: ML SERVICE ═══")

    test("ML Model Info", "GET", f"{ML_URL}/api/model-info")

    test("Traffic Prediction - Pune",
         "POST", f"{ML_URL}/api/traffic/predict",
         json={
             "lat": 18.5204,
             "lng": 73.8567,
             "hour": 9,
             "day": 2,
             "month": 6
         })

    # ━━━ 4. GATEWAY / ROUTING ━━━
    print("\n\n═══ SECTION 4: GATEWAY (ROUTING) ═══")

    test("Gateway Root", "GET", f"{GATEWAY_URL}/")

    # Pune: Shivajinagar → Kothrud
    route_payload = {
        "origin": {"lat": 18.5314, "lng": 73.8446},
        "destination": {"lat": 18.5074, "lng": 73.8077},
        "mode": "car",
        "optimize": "fastest"
    }
    route_result = test("Route - Shivajinagar to Kothrud", "POST",
         f"{GATEWAY_URL}/api/route", json=route_payload)

    # Multi-route
    multi_payload = {
        "origin": {"lat": 18.5314, "lng": 73.8446},
        "destination": {"lat": 18.5074, "lng": 73.8077},
        "mode": "car"
    }
    test("Multi-Route - Pune", "POST",
         f"{GATEWAY_URL}/api/multi-route", json=multi_payload)

    # Emissions
    emissions_payload = {
        "distance_km": 12.5,
        "vehicle_type": "car",
        "fuel_type": "petrol"
    }
    test("Emissions Calculation", "POST",
         f"{GATEWAY_URL}/api/emissions", json=emissions_payload)

    # POI Search via gateway
    test("Gateway POI Search", "GET",
         f"{GATEWAY_URL}/api/poi", params={"query": "station", "city": "Pune", "limit": "5"})

    # Traffic via gateway
    test("Gateway Traffic Predict", "POST",
         f"{GATEWAY_URL}/api/traffic/predict",
         json={"lat": 18.5204, "lng": 73.8567, "hour": 17, "day": 5, "month": 6})

    # Matching
    match_payload = {
        "riders": [
            {"id": "r1", "origin": {"lat": 18.53, "lng": 73.84}, "destination": {"lat": 18.50, "lng": 73.81}},
            {"id": "r2", "origin": {"lat": 18.52, "lng": 73.85}, "destination": {"lat": 18.51, "lng": 73.80}}
        ],
        "max_detour_km": 3
    }
    test("Rider Matching", "POST",
         f"{GATEWAY_URL}/api/match", json=match_payload)

    # Green score
    test("Green Score", "POST",
         f"{GATEWAY_URL}/api/green-score",
         json={
             "distance_km": 10,
             "vehicle_type": "car",
             "fuel_type": "petrol",
             "passengers": 3
         })

    # ━━━ 5. BACKEND ━━━
    print("\n\n═══ SECTION 5: BACKEND ═══")

    test("Backend Root", "GET", BACKEND_URL)

    # Register test user (may already exist)
    test_email = f"apitest_{int(time.time())}@test.com"
    register_result = test("Register User", "POST",
         f"{BACKEND_URL}/api/users/register",
         json={
             "name": "API Tester",
             "email": test_email,
             "password": "Test1234!",
             "phone": "9876543210"
         })

    token = None
    if register_result and "token" in register_result:
        token = register_result["token"]
    else:
        # Try login with admin
        login_result = test("Login Admin", "POST",
             f"{BACKEND_URL}/api/users/login",
             json={"email": "admin@aumo3.com", "password": "Admin123!"})
        if login_result and "token" in login_result:
            token = login_result["token"]

    if token:
        auth_headers = {"Authorization": f"Bearer {token}"}

        test("Get Profile", "GET",
             f"{BACKEND_URL}/api/users/profile",
             headers=auth_headers)

        # Create a ride
        ride_payload = {
            "origin": {
                "address": "Shivajinagar, Pune",
                "coordinates": [73.8446, 18.5314]
            },
            "destination": {
                "address": "Kothrud, Pune",
                "coordinates": [73.8077, 18.5074]
            },
            "departureTime": "2025-06-15T09:00:00Z",
            "availableSeats": 3,
            "fare": 150,
            "vehicleName": "Honda City",
            "vehicleRegNo": "MH12AB1234",
            "distance": 8.5,
            "duration": 25,
            "preferences": {
                "smoking": False,
                "music": True,
                "pets": False
            }
        }
        ride_result = test("Create Ride", "POST",
             f"{BACKEND_URL}/api/rides",
             json=ride_payload,
             headers=auth_headers)

        # List rides
        test("List Rides", "GET",
             f"{BACKEND_URL}/api/rides",
             headers=auth_headers)

        # Search rides
        test("Search Rides", "GET",
             f"{BACKEND_URL}/api/rides/search",
             params={
                 "originLat": "18.5314",
                 "originLng": "73.8446",
                 "destLat": "18.5074",
                 "destLng": "73.8077",
                 "radius": "5"
             },
             headers=auth_headers)

        # Get ride detail if created
        if ride_result and "_id" in ride_result:
            test("Get Ride Detail", "GET",
                 f"{BACKEND_URL}/api/rides/{ride_result['_id']}",
                 headers=auth_headers)

        # Route via backend (proxied to AI)
        test("Backend Route Proxy", "POST",
             f"{BACKEND_URL}/api/routes/calculate",
             json={
                 "origin": {"lat": 18.5314, "lng": 73.8446},
                 "destination": {"lat": 18.5074, "lng": 73.8077},
                 "mode": "car"
             },
             headers=auth_headers)

        # Traffic via backend
        test("Backend Traffic Proxy", "POST",
             f"{BACKEND_URL}/api/traffic/predict",
             json={"lat": 18.5204, "lng": 73.8567, "hour": 9, "day": 2, "month": 6},
             headers=auth_headers)

    else:
        print("\n  ⚠️ No auth token available — skipping authenticated tests")

    # ━━━ 6. ADDITIONAL ROUTE TESTS ━━━
    print("\n\n═══ SECTION 6: ADDITIONAL ROUTE TESTS ═══")

    # Pune → Mumbai route (long distance)
    test("Long Route - Pune to Mumbai", "POST",
         f"{GATEWAY_URL}/api/route",
         json={
             "origin": {"lat": 18.5204, "lng": 73.8567},
             "destination": {"lat": 19.0760, "lng": 72.8777},
             "mode": "car",
             "optimize": "greenest"
         })

    # Nagpur local route
    test("Route - Nagpur local", "POST",
         f"{GATEWAY_URL}/api/route",
         json={
             "origin": {"lat": 21.1458, "lng": 79.0882},
             "destination": {"lat": 21.1565, "lng": 79.0727},
             "mode": "car",
             "optimize": "fastest"
         })

    # Walking route
    test("Walking Route - Pune", "POST",
         f"{GATEWAY_URL}/api/route",
         json={
             "origin": {"lat": 18.5204, "lng": 73.8567},
             "destination": {"lat": 18.5250, "lng": 73.8600},
             "mode": "walk",
             "optimize": "shortest"
         })

    # ━━━ SUMMARY ━━━
    print("\n\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)
    print(f"  Total: {total}  |  ✅ Passed: {passed}  |  ❌ Failed: {failed}")
    print()
    for r in results:
        symbol = "✅" if r["passed"] else "❌"
        status = r.get("status", "ERR")
        error = f" ({r['error']})" if "error" in r else ""
        print(f"  {symbol} [{status}] {r['name']}{error}")
    print("=" * 60)


if __name__ == "__main__":
    main()
