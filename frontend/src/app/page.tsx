"use client";
import { useState, useCallback, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import Navbar from "@/components/layout/Navbar";
import { Navigation, Leaf, Clock, Activity, Sliders, Search, RotateCw } from "lucide-react";
import api from "@/lib/api";
import { formatCO2, formatDuration, formatDistance } from "@/lib/utils";
import type { RouteResult, POI } from "@/types";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

const STRATEGIES = [
  { key: "balanced", label: "Balanced", icon: Sliders, color: "bg-blue-500" },
  { key: "fastest", label: "Fastest", icon: Clock, color: "bg-red-500" },
  { key: "eco", label: "Eco-Friendly", icon: Leaf, color: "bg-green-500" },
  { key: "low_traffic", label: "Low Traffic", icon: Activity, color: "bg-orange-500" },
];

export default function HomePage() {
  const [origin, setOrigin] = useState<{ lat: number; lng: number } | null>(null);
  const [destination, setDestination] = useState<{ lat: number; lng: number } | null>(null);
  const [clickMode, setClickMode] = useState<"origin" | "destination">("origin");
  const [routes, setRoutes] = useState<Record<string, RouteResult>>({});
  const [activeStrategy, setActiveStrategy] = useState("balanced");
  const [loading, setLoading] = useState(false);
  const [pois, setPois] = useState<POI[]>([]);
  const [showPois, setShowPois] = useState(true);
  const [weights, setWeights] = useState({ alpha: 0.4, beta: 0.3, gamma: 0.15, delta: 0.15 });

  // Fetch POIs on mount
  useEffect(() => {
    api.get("/api/poi/map", { params: { south: 18.3, north: 18.7, west: 73.7, east: 74.1 } })
      .then((r) => setPois(r.data.pois || []))
      .catch(() => {});
  }, []);

  const handleMapClick = useCallback((lat: number, lng: number) => {
    if (clickMode === "origin") {
      setOrigin({ lat, lng });
      setClickMode("destination");
    } else {
      setDestination({ lat, lng });
      setClickMode("origin");
    }
  }, [clickMode]);

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
    } catch (err) {
      // Fallback: single route
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

  const activeRoute = routes[activeStrategy] || Object.values(routes)[0] || null;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside className="w-full lg:w-96 p-4 space-y-4 overflow-y-auto bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Navigation className="text-primary-600" size={20} />
            Route Planner
          </h2>

          {/* Click mode */}
          <div className="flex gap-2">
            <button
              onClick={() => setClickMode("origin")}
              className={`flex-1 py-2 rounded-lg text-sm font-medium border-2 transition ${clickMode === "origin" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-200"}`}
            >
              📍 Set Origin
            </button>
            <button
              onClick={() => setClickMode("destination")}
              className={`flex-1 py-2 rounded-lg text-sm font-medium border-2 transition ${clickMode === "destination" ? "border-green-500 bg-green-50 text-green-700" : "border-gray-200"}`}
            >
              🏁 Set Destination
            </button>
          </div>

          {/* Coordinates display */}
          <div className="space-y-2 text-sm">
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <span className="text-gray-500">Origin: </span>
              {origin ? `${origin.lat.toFixed(4)}, ${origin.lng.toFixed(4)}` : "Click map to set"}
            </div>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
              <span className="text-gray-500">Destination: </span>
              {destination ? `${destination.lat.toFixed(4)}, ${destination.lng.toFixed(4)}` : "Click map to set"}
            </div>
          </div>

          {/* Weight sliders */}
          <details className="group">
            <summary className="cursor-pointer text-sm font-medium text-gray-600 dark:text-gray-400 flex items-center gap-2">
              <Sliders size={14} /> Advanced Weights
            </summary>
            <div className="mt-2 space-y-2">
              {([["alpha", "⏱ Time", weights.alpha], ["beta", "🌿 Eco", weights.beta], ["gamma", "📏 Distance", weights.gamma], ["delta", "🚦 Traffic", weights.delta]] as const).map(([key, label, val]) => (
                <div key={key} className="flex items-center gap-2 text-xs">
                  <span className="w-20">{label}</span>
                  <input type="range" min={0} max={100} value={val * 100}
                    onChange={(e) => setWeights((w) => ({ ...w, [key]: Number(e.target.value) / 100 }))}
                    className="flex-1 h-1.5 accent-primary-600"
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
            className="w-full py-3 bg-gradient-to-r from-primary-600 to-accent-500 text-white rounded-xl font-semibold text-sm hover:shadow-lg disabled:opacity-50 transition flex items-center justify-center gap-2"
          >
            {loading ? <RotateCw size={16} className="animate-spin" /> : <Search size={16} />}
            {loading ? "Calculating..." : "Calculate Route"}
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
                      className={`p-3 rounded-xl text-left border-2 transition ${activeStrategy === s.key ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20" : "border-gray-200 dark:border-gray-700"}`}
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
            <div className="bg-gradient-to-br from-primary-50 to-accent-50 dark:from-primary-900/20 dark:to-accent-900/20 p-4 rounded-xl space-y-2">
              <h3 className="font-semibold text-sm">Route Details</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>Distance: <b>{formatDistance(activeRoute.distanceKm)}</b></div>
                <div>Duration: <b>{formatDuration(activeRoute.durationMin)}</b></div>
                <div>CO₂: <b>{formatCO2(activeRoute.co2Grams)}</b></div>
                <div>Congestion: <b>{(activeRoute.avgCongestion * 100).toFixed(0)}%</b></div>
              </div>
              <div className="text-xs text-gray-500 mt-2">Algorithm: {activeRoute.algorithm}</div>
            </div>
          )}

          {/* POI toggle */}
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={showPois} onChange={(e) => setShowPois(e.target.checked)} className="accent-primary-600" />
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
            className="h-[calc(100vh-4rem)]"
          />
        </main>
      </div>
    </div>
  );
}
