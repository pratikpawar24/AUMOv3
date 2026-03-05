"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/auth/AuthGuard";
import { Car, MapPin, Calendar, Users, IndianRupee, ArrowLeft } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

export default function CreateRidePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    originLat: "", originLng: "", originAddress: "",
    destLat: "", destLng: "", destAddress: "",
    departureTime: "",
    seatsAvailable: "3",
    farePerSeat: "50",
    smoking: false, music: true, petFriendly: false, quietRide: false,
  });

  const update = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    setLoading(true);
    try {
      await api.post("/api/rides", {
        origin: { lat: +form.originLat, lng: +form.originLng, address: form.originAddress },
        destination: { lat: +form.destLat, lng: +form.destLng, address: form.destAddress },
        departureTime: form.departureTime,
        seatsAvailable: +form.seatsAvailable,
        farePerSeat: +form.farePerSeat,
        preferences: { smoking: form.smoking, music: form.music, petFriendly: form.petFriendly, quietRide: form.quietRide },
      });
      router.push("/g-ride");
    } catch (e: any) {
      alert(e.response?.data?.error || "Failed to create ride");
    } finally {
      setLoading(false);
    }
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

          {/* Origin */}
          <div className="mb-5">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2"><MapPin size={14} className="text-blue-500" /> Pickup Location</label>
            <input placeholder="Address" value={form.originAddress} onChange={(e) => update("originAddress", e.target.value)} className={inputCls + " mb-2"} />
            <div className="grid grid-cols-2 gap-2">
              <input placeholder="Latitude" type="number" step="any" value={form.originLat} onChange={(e) => update("originLat", e.target.value)} className={inputCls} />
              <input placeholder="Longitude" type="number" step="any" value={form.originLng} onChange={(e) => update("originLng", e.target.value)} className={inputCls} />
            </div>
          </div>

          {/* Destination */}
          <div className="mb-5">
            <label className="text-sm font-medium text-gray-600 flex items-center gap-1 mb-2"><MapPin size={14} className="text-green-500" /> Drop-off Location</label>
            <input placeholder="Address" value={form.destAddress} onChange={(e) => update("destAddress", e.target.value)} className={inputCls + " mb-2"} />
            <div className="grid grid-cols-2 gap-2">
              <input placeholder="Latitude" type="number" step="any" value={form.destLat} onChange={(e) => update("destLat", e.target.value)} className={inputCls} />
              <input placeholder="Longitude" type="number" step="any" value={form.destLng} onChange={(e) => update("destLng", e.target.value)} className={inputCls} />
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
