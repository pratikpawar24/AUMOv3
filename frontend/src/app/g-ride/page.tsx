"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import { Car, Plus, Search, MapPin, Clock, Users, Leaf } from "lucide-react";
import api from "@/lib/api";
import { formatCO2, formatDuration, formatDistance } from "@/lib/utils";
import type { Ride } from "@/types";

export default function GRidePage() {
  const [rides, setRides] = useState<Ride[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.get("/api/rides").then((r) => { setRides(r.data.rides || []); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const filtered = rides.filter((r) =>
    r.origin.address?.toLowerCase().includes(search.toLowerCase()) ||
    r.destination.address?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2"><Car className="text-primary-600" /> G-Ride</h1>
            <p className="text-gray-500 text-sm mt-1">Share rides, save CO₂, connect with commuters</p>
          </div>
          <Link href="/g-ride/create" className="flex items-center gap-2 px-5 py-2.5 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition">
            <Plus size={18} /> Offer a Ride
          </Link>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by location..."
            className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 outline-none"
          />
        </div>

        {/* Rides grid */}
        {loading ? (
          <div className="text-center py-20 text-gray-400">Loading rides...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <Car className="mx-auto text-gray-300 mb-4" size={48} />
            <p className="text-gray-500">No rides available. Be the first to offer one!</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((ride) => (
              <Link key={ride._id} href={`/g-ride/${ride._id}`} className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800 hover:shadow-lg hover:border-primary-300 transition group">
                {/* Route */}
                <div className="flex items-start gap-3 mb-3">
                  <div className="flex flex-col items-center gap-1 mt-1">
                    <div className="w-3 h-3 rounded-full bg-blue-500" />
                    <div className="w-0.5 h-8 bg-gray-300" />
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{ride.origin.address || `${ride.origin.lat.toFixed(3)}, ${ride.origin.lng.toFixed(3)}`}</p>
                    <p className="text-xs text-gray-400 my-1">{formatDistance(ride.distanceKm)} • {formatDuration(ride.durationMin)}</p>
                    <p className="text-sm font-medium truncate">{ride.destination.address || `${ride.destination.lat.toFixed(3)}, ${ride.destination.lng.toFixed(3)}`}</p>
                  </div>
                </div>

                {/* Meta */}
                <div className="flex items-center gap-4 text-xs text-gray-500 border-t border-gray-100 dark:border-gray-800 pt-3">
                  <span className="flex items-center gap-1"><Clock size={12} /> {new Date(ride.departureTime).toLocaleString()}</span>
                  <span className="flex items-center gap-1"><Users size={12} /> {ride.seatsAvailable} seats</span>
                  <span className="flex items-center gap-1 text-green-600"><Leaf size={12} /> {formatCO2(ride.co2Saved)} saved</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
