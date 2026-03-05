"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Shield, Users, Car, Leaf, TrendingUp, BarChart3, Activity, LogOut } from "lucide-react";
import api from "@/lib/api";

interface DashboardData {
  totalUsers: number;
  totalRides: number;
  activeRides: number;
  totalCO2Saved: number;
  totalDistance: number;
  avgGreenScore: number;
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { router.push("/admin/login"); return; }

    const headers = { Authorization: `Bearer ${token}` };
    Promise.all([
      api.get("/api/admin/dashboard", { headers }),
      api.get("/api/admin/users", { headers }),
    ]).then(([dash, usr]) => {
      setData(dash.data);
      setUsers(usr.data.users || []);
      setLoading(false);
    }).catch(() => {
      localStorage.removeItem("adminToken");
      router.push("/admin/login");
    });
  }, []);

  const logout = () => { localStorage.removeItem("adminToken"); router.push("/admin/login"); };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">Loading dashboard...</div>;

  const stats = [
    { label: "Total Users", value: data?.totalUsers || 0, icon: Users, color: "text-blue-500", bg: "bg-blue-50" },
    { label: "Total Rides", value: data?.totalRides || 0, icon: Car, color: "text-purple-500", bg: "bg-purple-50" },
    { label: "Active Rides", value: data?.activeRides || 0, icon: Activity, color: "text-orange-500", bg: "bg-orange-50" },
    { label: "CO₂ Saved (kg)", value: ((data?.totalCO2Saved || 0) / 1000).toFixed(1), icon: Leaf, color: "text-green-500", bg: "bg-green-50" },
    { label: "Distance (km)", value: (data?.totalDistance || 0).toFixed(0), icon: TrendingUp, color: "text-cyan-500", bg: "bg-cyan-50" },
    { label: "Avg Green Score", value: (data?.avgGreenScore || 0).toFixed(1), icon: BarChart3, color: "text-primary-500", bg: "bg-primary-50" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="text-primary-600" size={24} />
            <h1 className="text-lg font-bold">AUMOv3 Admin</h1>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/" className="text-sm text-gray-500 hover:text-primary-600">View Site</Link>
            <button onClick={logout} className="flex items-center gap-1 text-sm text-red-500 hover:text-red-700">
              <LogOut size={14} /> Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Stats grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {stats.map((s) => (
            <div key={s.label} className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-4">
              <div className={`w-10 h-10 ${s.bg} rounded-xl flex items-center justify-center mb-3`}>
                <s.icon className={s.color} size={20} />
              </div>
              <p className="text-2xl font-bold">{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Users table */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
            <h2 className="font-semibold flex items-center gap-2"><Users size={18} /> Registered Users ({users.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Green Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Badges</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                {users.map((u) => (
                  <tr key={u._id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-6 py-3 font-medium">{u.name}</td>
                    <td className="px-6 py-3 text-gray-500">{u.email}</td>
                    <td className="px-6 py-3"><span className="px-2 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">{u.greenScore || 0}</span></td>
                    <td className="px-6 py-3 text-xs">{(u.badges || []).join(", ") || "—"}</td>
                    <td className="px-6 py-3 text-gray-500">{new Date(u.createdAt).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
