"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import { User, Leaf, Award, Settings, LogOut, Car, MapPin, TrendingUp } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import api from "@/lib/api";
import { formatCO2 } from "@/lib/utils";

const BADGE_ICONS: Record<string, string> = {
  "First Ride": "🚗", "Green Starter": "🌱", "Eco Warrior": "🌿", "Carbon Cutter": "✂️",
  "Green Champion": "🏆", "Eco Legend": "🌍", "Climate Hero": "🦸", "Planet Saver": "🌏",
};

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout, loadUser } = useAuthStore();
  const [stats, setStats] = useState({ totalRides: 0, totalCO2: 0, totalDistance: 0 });
  const [leaderboard, setLeaderboard] = useState<any[]>([]);

  useEffect(() => {
    loadUser();
    api.get("/api/users/leaderboard").then((r) => setLeaderboard(r.data.leaderboard || [])).catch(() => {});
    api.get("/api/rides?status=completed").then((r) => {
      const rides = r.data.rides || [];
      setStats({
        totalRides: rides.length,
        totalCO2: rides.reduce((a: number, r: any) => a + (r.co2Saved || 0), 0),
        totalDistance: rides.reduce((a: number, r: any) => a + (r.distanceKm || 0), 0),
      });
    }).catch(() => {});
  }, []);

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Navbar />
        <div className="text-center py-20">
          <User className="mx-auto text-gray-300 mb-4" size={48} />
          <p className="text-gray-500 mb-4">Please sign in to view your profile</p>
          <button onClick={() => router.push("/login")} className="px-6 py-2 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700">
            Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Profile header */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <h1 className="text-xl font-bold">{user.name}</h1>
              <p className="text-gray-500 text-sm">{user.email}</p>
            </div>
            <button onClick={() => { logout(); router.push("/login"); }}
              className="flex items-center gap-2 px-4 py-2 text-red-500 hover:bg-red-50 rounded-xl text-sm transition">
              <LogOut size={16} /> Logout
            </button>
          </div>
        </div>

        {/* Green Score */}
        <div className="bg-gradient-to-r from-primary-500 to-primary-700 rounded-2xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-primary-100 text-sm font-medium">Green Score</p>
              <p className="text-4xl font-bold mt-1">{user.greenScore || 0}</p>
            </div>
            <Leaf size={48} className="text-primary-200" />
          </div>
          {/* Badges */}
          {user.badges && user.badges.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {user.badges.map((badge) => (
                <span key={badge} className="px-3 py-1 bg-white/20 rounded-full text-sm font-medium">
                  {BADGE_ICONS[badge] || "🏅"} {badge}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 text-center">
            <Car className="mx-auto text-primary-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{stats.totalRides}</p>
            <p className="text-xs text-gray-500">Total Rides</p>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 text-center">
            <Leaf className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{formatCO2(stats.totalCO2)}</p>
            <p className="text-xs text-gray-500">CO₂ Saved</p>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 text-center">
            <MapPin className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{stats.totalDistance.toFixed(0)}</p>
            <p className="text-xs text-gray-500">Km Travelled</p>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <h2 className="text-lg font-bold flex items-center gap-2 mb-4"><TrendingUp className="text-primary-600" size={20} /> Leaderboard</h2>
          {leaderboard.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-4">No data yet</p>
          ) : (
            <div className="space-y-3">
              {leaderboard.slice(0, 10).map((u: any, i: number) => (
                <div key={u._id} className={`flex items-center gap-3 p-3 rounded-xl ${u._id === user._id ? "bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800" : "hover:bg-gray-50 dark:hover:bg-gray-800"}`}>
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${i < 3 ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-600"}`}>
                    {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : i + 1}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{u.name} {u._id === user._id && <span className="text-primary-600">(You)</span>}</p>
                  </div>
                  <span className="text-sm font-bold text-primary-600">{u.greenScore}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
