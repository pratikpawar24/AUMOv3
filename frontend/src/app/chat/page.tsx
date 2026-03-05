"use client";
import { useEffect, useState } from "react";
import Navbar from "@/components/layout/Navbar";
import Link from "next/link";
import { MessageCircle, Users } from "lucide-react";
import api from "@/lib/api";

interface ChatRoom {
  _id: string;
  rideId?: string;
  lastMessage?: string;
  participants: number;
  updatedAt: string;
}

export default function ChatListPage() {
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/rides?status=active")
      .then((r) => {
        const rides = r.data.rides || [];
        const chatRooms: ChatRoom[] = rides
          .filter((ride: any) => ride.chatRoomId)
          .map((ride: any) => ({
            _id: ride.chatRoomId,
            rideId: ride._id,
            lastMessage: `${ride.origin.address || "Origin"} → ${ride.destination.address || "Destination"}`,
            participants: (ride.passengers?.length || 0) + 1,
            updatedAt: ride.updatedAt || ride.departureTime,
          }));
        setRooms(chatRooms);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold flex items-center gap-2 mb-6">
          <MessageCircle className="text-primary-600" /> Ride Chats
        </h1>

        {loading ? (
          <div className="text-center py-20 text-gray-400">Loading chats...</div>
        ) : rooms.length === 0 ? (
          <div className="text-center py-20">
            <MessageCircle className="mx-auto text-gray-300 mb-4" size={48} />
            <p className="text-gray-500">No active chats. Join a ride to start chatting!</p>
            <Link href="/g-ride" className="inline-block mt-4 px-6 py-2 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700">
              Browse Rides
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {rooms.map((room) => (
              <Link key={room._id} href={`/chat/${room._id}`}
                className="flex items-center gap-4 p-4 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 hover:shadow-md hover:border-primary-300 transition">
                <div className="w-12 h-12 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center">
                  <MessageCircle size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{room.lastMessage}</p>
                  <p className="text-xs text-gray-400 mt-1 flex items-center gap-2">
                    <Users size={12} /> {room.participants} members • {new Date(room.updatedAt).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
