"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/auth/AuthGuard";
import { Car, MapPin, Calendar, Users, IndianRupee, ArrowLeft, Search, Clock, Route, Loader2 } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

interface LocationSuggestion {
  display_name: string;
  lat: string;
  lon: string;
}

function LocationInput({ label, icon, color, value, onSelect }: {
  label: string;
  icon: React.ReactNode;
  color: string;
  value: { address: string; lat: number; lng: number };
  onSelect: (loc: { address: string; lat: number; lng: number }) => void;
}) {
  const [query, setQuery] = useState(value.address);
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout>();
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setQuery(value.address); }, [value.address]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) setShowSuggestions(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const searchLocation = useCallback(async (q: string) => {
    if (q.length < 3) { setSuggestions([]); return; }
    setSearching(true);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q + " Maharashtra India")}&limit=6&addressdetails=1&countrycodes=in`
      );
      const data = await res.json();
      setSuggestions(data);
      setShowSuggestions(true);
    } catch { setSuggestions([]); }
    setSearching(false);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setQuery(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => searchLocation(v), 400);
  };

  const selectSuggestion = (s: LocationSuggestion) => {
    const shortName = s.display_name.split(",").slice(0, 3).join(",");
    setQuery(shortName);
    setShowSuggestions(false);
    onSelect({ address: shortName, lat: parseFloat(s.lat), lng: parseFloat(s.lon) });
  };

  return (
    <div ref={wrapperRef} className="relative mb-5">
      <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2">
        {icon} {label}
      </label>
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input value={query} onChange={handleChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="Search location... e.g. Pune Station, Hinjewadi"
          className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 outline-none text-sm" />
        {searching && <Loader2 size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 animate-spin" />}
        {value.lat !== 0 && !searching && (
          <div className={`absolute right-3 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full ${color}`} />
        )}
      </div>
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg max-h-60 overflow-y-auto">
          {suggestions.map((s, i) => (
            <button key={i} onClick={() => selectSuggestion(s)}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 text-sm border-b border-gray-100 dark:border-gray-800 last:border-0 flex items-start gap-2">
              <MapPin size={14} className="text-gray-400 mt-0.5 shrink-0" />
              <span className="line-clamp-2">{s.display_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function CreateRidePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [routeInfo, setRouteInfo] = useState<{ distanceKm: number; durationMin: number } | null>(null);
  const [origin, setOrigin] = useState({ address: "", lat: 0, lng: 0 });
  const [destination, setDestination] = useState({ address: "", lat: 0, lng: 0 });
  const [form, setForm] = useState({
    departureTime: "",
    seatsAvailable: "3",
    farePerSeat: "50",
    vehicleName: "",
    vehicleRegNo: "",
    smoking: false, music: true, petFriendly: false, quietRide: false,
  });

  const update = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  // Auto-calculate route distance & time when both locations set
  useEffect(() => {
    if (origin.lat && origin.lng && destination.lat && destination.lng) {
      fetch(`https://router.project-osrm.org/route/v1/driving/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=false`)
        .then(r => r.json()).then(data => {
          if (data.code === "Ok" && data.routes?.[0]) {
            setRouteInfo({
              distanceKm: Math.round(data.routes[0].distance / 100) / 10,
              durationMin: Math.round(data.routes[0].duration / 60),
            });
          }
        }).catch(() => {});
    }
  }, [origin, destination]);

  const submit = async () => {
    if (!origin.lat || !destination.lat) return alert("Please select both pickup and drop-off locations");
    if (!form.vehicleName || !form.vehicleRegNo) return alert("Please enter vehicle name and registration number");
    setLoading(true);
    try {
      await api.post("/api/rides", {
        origin: { lat: origin.lat, lng: origin.lng, address: origin.address },
        destination: { lat: destination.lat, lng: destination.lng, address: destination.address },
        departureTime: form.departureTime,
        seatsTotal: +form.seatsAvailable,
        seatsAvailable: +form.seatsAvailable,
        fare: +form.farePerSeat,
        vehicleName: form.vehicleName,
        vehicleRegNo: form.vehicleRegNo,
        distanceKm: routeInfo?.distanceKm || 0,
        durationMin: routeInfo?.durationMin || 0,
        preferences: { smoking: form.smoking, music: form.music, petFriendly: form.petFriendly, quietRide: form.quietRide },
      });
      router.push("/g-ride");
    } catch (e: any) {
      alert(e.response?.data?.error || "Failed to create ride");
    } finally { setLoading(false); }
  };

  const inputCls = "w-full px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 outline-none text-sm";

  return (
    <AuthGuard>
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-6">
        <Link href="/g-ride" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 mb-4">
          <ArrowLeft size={16} /> Back to rides
        </Link>

        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <h1 className="text-xl font-bold flex items-center gap-2 mb-6"><Car className="text-primary-600" /> Offer a Ride</h1>

          <LocationInput label="Pickup Location" icon={<MapPin size={14} className="text-blue-500" />} color="bg-blue-500" value={origin} onSelect={setOrigin} />
          <LocationInput label="Drop-off Location" icon={<MapPin size={14} className="text-green-500" />} color="bg-green-500" value={destination} onSelect={setDestination} />

          {routeInfo && (
            <div className="mb-5 p-3 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-xl flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1 text-primary-700 dark:text-primary-300"><Route size={14} /> {routeInfo.distanceKm} km</span>
              <span className="flex items-center gap-1 text-primary-700 dark:text-primary-300"><Clock size={14} /> ~{routeInfo.durationMin} min</span>
            </div>
          )}

          {/* Vehicle info */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2"><Car size={14} /> Vehicle Name</label>
              <input placeholder="e.g. Maruti Swift" value={form.vehicleName} onChange={(e) => update("vehicleName", e.target.value)} className={inputCls} />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2">🔢 Registration No.</label>
              <input placeholder="e.g. MH12AB1234" value={form.vehicleRegNo} onChange={(e) => update("vehicleRegNo", e.target.value.toUpperCase())} className={inputCls} />
            </div>
          </div>

          {/* Time & seats */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2"><Calendar size={14} /> Departure</label>
              <input type="datetime-local" value={form.departureTime} onChange={(e) => update("departureTime", e.target.value)} className={inputCls} />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2"><Users size={14} /> Seats</label>
              <input type="number" min="1" max="6" value={form.seatsAvailable} onChange={(e) => update("seatsAvailable", e.target.value)} className={inputCls} />
            </div>
          </div>

          {/* Fare */}
          <div className="mb-5">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2"><IndianRupee size={14} /> Fare per seat (₹)</label>
            <input type="number" min="0" value={form.farePerSeat} onChange={(e) => update("farePerSeat", e.target.value)} className={inputCls} />
          </div>

          {/* Preferences */}
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-600 mb-2 block">Preferences</label>
            <div className="flex flex-wrap gap-3">
              {(["smoking", "music", "petFriendly", "quietRide"] as const).map((p) => (
                <button key={p} onClick={() => update(p, !form[p])}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition ${form[p] ? "bg-primary-50 border-primary-300 text-primary-700" : "bg-gray-50 border-gray-200 text-gray-500"}`}>
                  {p === "petFriendly" ? "🐾 Pets OK" : p === "quietRide" ? "🤫 Quiet" : p === "smoking" ? "🚬 Smoking" : "🎵 Music"}
                </button>
              ))}
            </div>
          </div>

          <button onClick={submit} disabled={loading}
            className="w-full py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50 transition">
            {loading ? "Creating..." : "Offer Ride"}
          </button>
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}
