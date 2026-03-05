"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/auth/AuthGuard";
import Link from "next/link";
import { ArrowLeft, MapPin, Clock, Users, Leaf, IndianRupee, UserPlus, MessageCircle, Car, Route } from "lucide-react";
import api from "@/lib/api";
import { formatCO2, formatDuration, formatDistance } from "@/lib/utils";
import dynamic from "next/dynamic";
import type { Ride } from "@/types";

const MapView = dynamic(() => import("@/components/map/MapView"), { ssr: false });

export default function RideDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [ride, setRide] = useState<Ride | null>(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    if (!id) return;
    api.get(`/api/rides/${id}`).then((r) => { setRide(r.data.ride); setLoading(false); }).catch(() => setLoading(false));
  }, [id]);

  const handleJoin = async () => {
    setJoining(true);
    try {
      await api.post(`/api/rides/${id}/join`);
      const r = await api.get(`/api/rides/${id}`);
      setRide(r.data.ride);
    } catch (e: any) {
      alert(e.response?.data?.error || "Failed to join");
    } finally {
      setJoining(false);
    }
  };

  if (loading) return (<AuthGuard><div className="min-h-screen bg-gray-50 dark:bg-gray-950"><Navbar /><div className="text-center py-20 text-gray-400">Loading...</div></div></AuthGuard>);
  if (!ride) return (<AuthGuard><div className="min-h-screen bg-gray-50 dark:bg-gray-950"><Navbar /><div className="text-center py-20 text-gray-400">Ride not found</div></div></AuthGuard>);

  const routeResult = ride.polyline ? {
    polyline: ride.polyline,
    distanceKm: ride.distanceKm,
    durationMin: ride.durationMin,
    co2Grams: ride.co2Saved * 1000 || 0,
    cost: ride.fare || 0,
    avgCongestion: 0,
    algorithm: "AUMORoute",
    trafficOverlay: [] as { lat: number; lng: number; congestion: number; speed: number }[],
  } : undefined;

  return (
    <AuthGuard>
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-6">
        <Link href="/g-ride" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600 mb-4">
          <ArrowLeft size={16} /> Back to rides
        </Link>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Details */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
              <h1 className="text-lg font-bold mb-4">Ride Details</h1>

              {/* Route line */}
              <div className="flex gap-3 mb-4">
                <div className="flex flex-col items-center gap-1 mt-1">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <div className="w-0.5 h-10 bg-gray-300" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                </div>
                <div>
                  <p className="font-medium text-sm">{ride.origin.address || `${ride.origin.lat.toFixed(4)}, ${ride.origin.lng.toFixed(4)}`}</p>
                  <p className="text-xs text-gray-400 my-2">{formatDistance(ride.distanceKm)} • {formatDuration(ride.durationMin)}</p>
                  <p className="font-medium text-sm">{ride.destination.address || `${ride.destination.lat.toFixed(4)}, ${ride.destination.lng.toFixed(4)}`}</p>
                </div>
              </div>

              {/* Info grid */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-gray-600"><Clock size={14} /> {new Date(ride.departureTime).toLocaleString()}</div>
                <div className="flex items-center gap-2 text-gray-600"><Users size={14} /> {ride.seatsAvailable} seats left</div>
                <div className="flex items-center gap-2 text-green-600"><Leaf size={14} /> {formatCO2(ride.co2Saved)} saved</div>
                <div className="flex items-center gap-2 text-gray-600"><IndianRupee size={14} /> ₹{ride.fare}/seat</div>
              </div>

              {/* Vehicle Info */}
              {(ride.vehicleName || ride.vehicleRegNo) && (
                <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-1">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Vehicle</h3>
                  {ride.vehicleName && (
                    <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"><Car size={14} /> {ride.vehicleName}</div>
                  )}
                  {ride.vehicleRegNo && (
                    <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"><Route size={14} /> {ride.vehicleRegNo}</div>
                  )}
                </div>
              )}

              {/* Distance & Time */}
              {(ride.distanceKm > 0 || ride.durationMin > 0) && (
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl flex gap-4 text-sm">
                  {ride.distanceKm > 0 && <span className="text-blue-700 dark:text-blue-300 font-medium">📍 {formatDistance(ride.distanceKm)}</span>}
                  {ride.durationMin > 0 && <span className="text-blue-700 dark:text-blue-300 font-medium">⏱ {formatDuration(ride.durationMin)}</span>}
                </div>
              )}

              {/* Preferences */}
              {ride.preferences && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {ride.preferences.music && <span className="px-3 py-1 bg-purple-50 text-purple-600 rounded-full text-xs">🎵 Music</span>}
                  {ride.preferences.smoking && <span className="px-3 py-1 bg-orange-50 text-orange-600 rounded-full text-xs">🚬 Smoking</span>}
                  {ride.preferences.petFriendly && <span className="px-3 py-1 bg-amber-50 text-amber-600 rounded-full text-xs">🐾 Pets OK</span>}
                  {ride.preferences.quietRide && <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs">🤫 Quiet</span>}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <button onClick={handleJoin} disabled={joining || ride.seatsAvailable <= 0 || ride.status === "completed" || ride.status === "cancelled"}
                className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50 transition">
                <UserPlus size={16} /> {joining ? "Joining..." : ride.seatsAvailable <= 0 ? "Full" : ride.status === "completed" ? "Completed" : ride.status === "cancelled" ? "Cancelled" : "Join Ride"}
              </button>
              {ride.chatRoomId && (
                <Link href={`/chat/${ride.chatRoomId}`}
                  className="flex items-center justify-center gap-2 px-5 py-3 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                  <MessageCircle size={16} /> Chat
                </Link>
              )}
            </div>

            {/* Passengers */}
            {ride.passengers && ride.passengers.length > 0 && (
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
                <h3 className="font-semibold text-sm mb-3">Passengers ({ride.passengers.length})</h3>
                <div className="space-y-2">
                  {ride.passengers.map((p: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <div className="w-8 h-8 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center font-bold text-xs">
                        {(p.name || p).toString().charAt(0).toUpperCase()}
                      </div>
                      <span>{p.name || p}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Map */}
          <div className="lg:col-span-3 h-[500px] rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-800">
            <MapView
              origin={{ lat: ride.origin.lat, lng: ride.origin.lng }}
              destination={{ lat: ride.destination.lat, lng: ride.destination.lng }}
              route={routeResult}
            />
          </div>
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}
