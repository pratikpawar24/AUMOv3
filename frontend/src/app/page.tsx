"use client";
import { useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import Navbar from "@/components/layout/Navbar";
import {
  Navigation, Leaf, Clock, Activity, Sliders,
  Search, RotateCw, MapPin, X, Locate,
} from "lucide-react";
import api from "@/lib/api";
import { formatCO2, formatDuration, formatDistance } from "@/lib/utils";
import type { RouteResult, POI } from "@/types";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

/* ── Nominatim geocoding (free, no API key) ─────────────── */
interface NominatimResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type: string;
  address?: Record<string, string>;
}

async function searchLocation(query: string): Promise<NominatimResult[]> {
  if (!query || query.length < 2) return [];
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=in&limit=6&addressdetails=1&viewbox=72.5,20.5,75.5,17.5&bounded=0`;
  const res = await fetch(url, {
    headers: { "Accept-Language": "en", "User-Agent": "AUMOv3/3.0" },
  });
  return res.json();
}

async function reverseGeocode(lat: number, lng: number): Promise<string> {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=16`,
      { headers: { "User-Agent": "AUMOv3/3.0" } }
    );
    const data = await res.json();
    return data.display_name || `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  } catch {
    return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
  }
}

/* ── Overpass API — nearby stops/stations (free) ─────────── */
interface NearbyStop {
  id: number;
  name: string;
  type: string;
  lat: number;
  lng: number;
}

async function fetchNearbyStops(lat: number, lng: number, radius = 2000): Promise<NearbyStop[]> {
  try {
    const query = `
      [out:json][timeout:10];
      (
        node["railway"="station"](around:${radius},${lat},${lng});
        node["railway"="halt"](around:${radius},${lat},${lng});
        node["highway"="bus_stop"](around:${radius},${lat},${lng});
        node["amenity"="bus_station"](around:${radius},${lat},${lng});
        node["station"="subway"](around:${radius},${lat},${lng});
        node["public_transport"="stop_position"](around:${radius},${lat},${lng});
      );
      out body 20;
    `;
    const res = await fetch("https://overpass-api.de/api/interpreter", {
      method: "POST",
      body: `data=${encodeURIComponent(query)}`,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const data = await res.json();
    return (data.elements || [])
      .filter((el: any) => el.tags?.name)
      .map((el: any) => ({
        id: el.id,
        name: el.tags.name,
        type: el.tags.railway ? "🚆 Railway" : el.tags.station === "subway" ? "🚇 Metro" : "🚌 Bus Stop",
        lat: el.lat,
        lng: el.lon,
      }));
  } catch {
    return [];
  }
}

/* ── Location Search Input Component ─────────────────────── */
function LocationSearch({
  label,
  icon,
  value,
  onSelect,
  placeholder,
  accentColor,
}: {
  label: string;
  icon: string;
  value: string;
  onSelect: (lat: number, lng: number, name: string) => void;
  placeholder: string;
  accentColor: string;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<NominatimResult[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSearch = (text: string) => {
    setQuery(text);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (text.length < 2) { setResults([]); setShowDropdown(false); return; }
    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      const res = await searchLocation(text);
      setResults(res);
      setShowDropdown(res.length > 0);
      setSearching(false);
    }, 400);
  };

  const handleSelect = (r: NominatimResult) => {
    const name = r.display_name.split(",").slice(0, 3).join(", ");
    setQuery(name);
    setShowDropdown(false);
    onSelect(parseFloat(r.lat), parseFloat(r.lon), name);
  };

  return (
    <div ref={wrapperRef} className="relative">
      <label className="text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
        <span>{icon}</span> {label}
      </label>
      <div className={`flex items-center border-2 rounded-lg overflow-hidden transition ${showDropdown ? `border-${accentColor}-400 ring-2 ring-${accentColor}-100` : "border-gray-200 dark:border-gray-700"}`}>
        <input
          type="text"
          value={query || value}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => results.length > 0 && setShowDropdown(true)}
          placeholder={placeholder}
          className="flex-1 px-3 py-2.5 text-sm bg-transparent outline-none dark:text-white"
        />
        {(query || value) && (
          <button onClick={() => { setQuery(""); setResults([]); setShowDropdown(false); onSelect(0, 0, ""); }} className="px-2 text-gray-400 hover:text-red-500">
            <X size={14} />
          </button>
        )}
        {searching && <RotateCw size={14} className="animate-spin mr-2 text-gray-400" />}
      </div>
      {showDropdown && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl max-h-64 overflow-y-auto">
          {results.map((r) => (
            <button
              key={r.place_id}
              onClick={() => handleSelect(r)}
              className="w-full text-left px-3 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-0 transition"
            >
              <div className="flex items-start gap-2">
                <MapPin size={14} className="text-gray-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 line-clamp-1">
                    {r.display_name.split(",").slice(0, 2).join(", ")}
                  </p>
                  <p className="text-xs text-gray-500 line-clamp-1">
                    {r.display_name.split(",").slice(2, 5).join(", ")}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Strategy configs ────────────────────────────────────── */
const STRATEGIES = [
  { key: "balanced", label: "Balanced", icon: Sliders, color: "bg-blue-500" },
  { key: "fastest", label: "Fastest", icon: Clock, color: "bg-red-500" },
  { key: "eco", label: "Eco-Friendly", icon: Leaf, color: "bg-green-500" },
  { key: "low_traffic", label: "Low Traffic", icon: Activity, color: "bg-orange-500" },
];

/* ── Main Home Page ──────────────────────────────────────── */
export default function HomePage() {
  const [origin, setOrigin] = useState<{ lat: number; lng: number } | null>(null);
  const [destination, setDestination] = useState<{ lat: number; lng: number } | null>(null);
  const [originName, setOriginName] = useState("");
  const [destName, setDestName] = useState("");
  const [clickMode, setClickMode] = useState<"origin" | "destination">("origin");
  const [routes, setRoutes] = useState<Record<string, RouteResult>>({});
  const [activeStrategy, setActiveStrategy] = useState("balanced");
  const [loading, setLoading] = useState(false);
  const [pois, setPois] = useState<POI[]>([]);
  const [showPois, setShowPois] = useState(true);
  const [nearbyStops, setNearbyStops] = useState<NearbyStop[]>([]);
  const [weights, setWeights] = useState({ alpha: 0.4, beta: 0.3, gamma: 0.15, delta: 0.15 });

  // Fetch POIs on mount
  useEffect(() => {
    api.get("/api/poi/map", { params: { south: 18.3, north: 18.7, west: 73.7, east: 74.1 } })
      .then((r) => setPois(r.data.pois || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const point = origin || destination;
    if (!point) return;
    fetchNearbyStops(point.lat, point.lng).then(setNearbyStops);
  }, [origin, destination]);

  const handleMapClick = useCallback(async (lat: number, lng: number) => {
    const name = await reverseGeocode(lat, lng);
    if (clickMode === "origin") {
      setOrigin({ lat, lng });
      setOriginName(name.split(",").slice(0, 3).join(", "));
      setClickMode("destination");
    } else {
      setDestination({ lat, lng });
      setDestName(name.split(",").slice(0, 3).join(", "));
      setClickMode("origin");
    }
  }, [clickMode]);

  const handleOriginSelect = (lat: number, lng: number, name: string) => {
    if (lat === 0 && lng === 0) { setOrigin(null); setOriginName(""); return; }
    setOrigin({ lat, lng });
    setOriginName(name);
  };
  const handleDestSelect = (lat: number, lng: number, name: string) => {
    if (lat === 0 && lng === 0) { setDestination(null); setDestName(""); return; }
    setDestination({ lat, lng });
    setDestName(name);
  };

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        const name = await reverseGeocode(latitude, longitude);
        setOrigin({ lat: latitude, lng: longitude });
        setOriginName(name.split(",").slice(0, 3).join(", "));
      },
      () => alert("Could not get your location. Please allow location access.")
    );
  };

  const calculateRoute = async () => {
    if (!origin || !destination) return;
    setLoading(true);
    try {
      const res = await api.post("/api/routes/multi", {
        origin_lat: origin.lat, origin_lng: origin.lng,
        dest_lat: destination.lat, dest_lng: destination.lng,
        departure_time: new Date().toISOString(),
      });
      setRoutes(res.data.routes || {});
    } catch {
      try {
        const res = await api.post("/api/routes/calculate", {
          origin_lat: origin.lat, origin_lng: origin.lng,
          dest_lat: destination.lat, dest_lng: destination.lng,
          ...weights,
        });
        setRoutes({ balanced: res.data.route });
      } catch {
        alert("Route calculation failed. Make sure the AI service is running.");
      }
    }
    setLoading(false);
  };

  const swapLocations = () => {
    setOrigin(destination);
    setDestination(origin);
    setOriginName(destName);
    setDestName(originName);
  };

  const activeRoute = routes[activeStrategy] || Object.values(routes)[0] || null;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full lg:w-[420px] p-4 space-y-4 overflow-y-auto bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 shadow-sm">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Navigation className="text-emerald-600" size={20} />
            AUMOv3 Route Planner
          </h2>

          {/* Location Search */}
          <div className="space-y-3">
            <LocationSearch
              label="Origin"
              icon="📍"
              value={originName}
              onSelect={handleOriginSelect}
              placeholder="Search origin... (e.g. Pune Station)"
              accentColor="blue"
            />
            <div className="flex justify-center">
              <button
                onClick={swapLocations}
                className="p-1.5 rounded-full border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                title="Swap origin and destination"
              >
                <RotateCw size={14} className="text-gray-500" />
              </button>
            </div>
            <LocationSearch
              label="Destination"
              icon="🏁"
              value={destName}
              onSelect={handleDestSelect}
              placeholder="Search destination... (e.g. Hinjawadi IT Park)"
              accentColor="green"
            />
          </div>

          {/* Use my location + Click mode */}
          <div className="flex gap-2">
            <button
              onClick={useMyLocation}
              className="flex-1 py-2 rounded-lg text-xs font-medium border border-gray-200 dark:border-gray-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition flex items-center justify-center gap-1.5"
            >
              <Locate size={13} className="text-blue-500" /> Use My Location
            </button>
            <button
              onClick={() => setClickMode(clickMode === "origin" ? "destination" : "origin")}
              className={`flex-1 py-2 rounded-lg text-xs font-medium border-2 transition ${
                clickMode === "origin"
                  ? "border-blue-400 bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300"
                  : "border-green-400 bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300"
              }`}
            >
              🖱 Click Map → {clickMode === "origin" ? "Origin" : "Destination"}
            </button>
          </div>

          {/* Nearby stops */}
          {nearbyStops.length > 0 && (
            <details className="group">
              <summary className="cursor-pointer text-xs font-semibold text-gray-600 dark:text-gray-400">
                🚏 Nearby Stops & Stations ({nearbyStops.length})
              </summary>
              <div className="mt-2 max-h-36 overflow-y-auto space-y-1">
                {nearbyStops.map((stop) => (
                  <button
                    key={stop.id}
                    onClick={() => {
                      if (!origin) {
                        setOrigin({ lat: stop.lat, lng: stop.lng });
                        setOriginName(stop.name);
                      } else {
                        setDestination({ lat: stop.lat, lng: stop.lng });
                        setDestName(stop.name);
                      }
                    }}
                    className="w-full text-left px-2.5 py-1.5 text-xs rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent hover:border-gray-200 dark:hover:border-gray-700 transition"
                  >
                    <span className="font-medium">{stop.type}</span>{" "}
                    <span className="text-gray-700 dark:text-gray-300">{stop.name}</span>
                  </button>
                ))}
              </div>
            </details>
          )}

          {/* Weight sliders */}
          <details className="group">
            <summary className="cursor-pointer text-xs font-semibold text-gray-600 dark:text-gray-400 flex items-center gap-2">
              <Sliders size={13} /> Advanced Weights
            </summary>
            <div className="mt-2 space-y-2">
              {([
                ["alpha", "⏱ Time", weights.alpha],
                ["beta", "🌿 Eco", weights.beta],
                ["gamma", "📏 Distance", weights.gamma],
                ["delta", "🚦 Traffic", weights.delta],
              ] as const).map(([key, label, val]) => (
                <div key={key} className="flex items-center gap-2 text-xs">
                  <span className="w-20">{label}</span>
                  <input type="range" min={0} max={100} value={val * 100}
                    onChange={(e) => setWeights((w) => ({ ...w, [key]: Number(e.target.value) / 100 }))
                    }
                    className="flex-1 h-1.5 accent-emerald-600"
                  />
                  <span className="w-10 text-right">{(val * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </details>

          {/* Calculate button */}
          <button
            onClick={calculateRoute}
            disabled={!origin || !destination || loading}
            className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-500 text-white rounded-xl font-semibold text-sm hover:shadow-lg hover:shadow-emerald-200 disabled:opacity-50 transition flex items-center justify-center gap-2"
          >
            {loading ? <RotateCw size={16} className="animate-spin" /> : <Search size={16} />}
            {loading ? "Calculating Routes..." : "Calculate Route"}
          </button>

          {/* Strategy tabs */}
          {Object.keys(routes).length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Route Strategies</h3>
              <div className="grid grid-cols-2 gap-2">
                {STRATEGIES.map((s) => {
                  const r = routes[s.key];
                  if (!r) return null;
                  const Icon = s.icon;
                  return (
                    <button
                      key={s.key}
                      onClick={() => setActiveStrategy(s.key)}
                      className={`p-3 rounded-xl text-left border-2 transition ${
                        activeStrategy === s.key
                          ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20"
                          : "border-gray-200 dark:border-gray-700"
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <div className={`w-5 h-5 rounded ${s.color} flex items-center justify-center`}>
                          <Icon size={12} className="text-white" />
                        </div>
                        <span className="text-xs font-semibold">{s.label}</span>
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                        <div>📏 {formatDistance(r.distanceKm)}</div>
                        <div>⏱ {formatDuration(r.durationMin)}</div>
                        <div>🌿 {formatCO2(r.co2Grams)}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Route details */}
          {activeRoute && (
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 p-4 rounded-xl space-y-2 border border-emerald-100 dark:border-emerald-800/30">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <Navigation size={14} className="text-emerald-600" /> Route Details
              </h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>📏 Distance: <b>{formatDistance(activeRoute.distanceKm)}</b></div>
                <div>⏱ Duration: <b>{formatDuration(activeRoute.durationMin)}</b></div>
                <div>🌿 CO₂: <b>{formatCO2(activeRoute.co2Grams)}</b></div>
                <div>🚦 Congestion: <b>{(activeRoute.avgCongestion * 100).toFixed(0)}%</b></div>
              </div>
              <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-emerald-100 dark:border-emerald-800/30">
                Algorithm: {activeRoute.algorithm} • Powered by AUMORoute™
              </div>
            </div>
          )}

          {/* POI toggle */}
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={showPois} onChange={(e) => setShowPois(e.target.checked)} className="accent-emerald-600" />
            Show Maharashtra POIs ({pois.length})
          </label>
        </aside>

        {/* Map */}
        <main className="flex-1 relative">
          <MapView
            route={activeRoute}
            pois={showPois ? pois : []}
            onMapClick={handleMapClick}
            origin={origin}
            destination={destination}
            nearbyStops={nearbyStops}
            className="h-[calc(100vh-4rem)]"
          />
        </main>
      </div>
    </div>
  );
}
