"use client";
import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import AuthGuard from "@/components/auth/AuthGuard";
import Link from "next/link";
import { ArrowLeft, Send } from "lucide-react";
import { io, Socket } from "socket.io-client";
import { useAuthStore } from "@/stores/authStore";

interface Message {
  _id?: string;
  sender: { _id: string; name: string } | string;
  content: string;
  type: "text" | "system" | "location";
  createdAt: string;
}

export default function ChatRoomPage() {
  const { roomId } = useParams();
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [socket, setSocket] = useState<Socket | null>(null);
  const [typing, setTyping] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
    const token = localStorage.getItem("token") || "";
    const s = io(apiUrl, { auth: { token } });
    setSocket(s);

    s.emit("join_room", roomId);

    s.on("new_message", (msg: Message) => {
      setMessages((prev) => [...prev, msg]);
    });

    s.on("user_typing", (data: { userName: string }) => {
      setTyping(data.userName);
      setTimeout(() => setTyping(null), 2000);
    });

    s.on("room_history", (history: Message[]) => {
      setMessages(history);
    });

    return () => { s.emit("leave_room", roomId); s.disconnect(); };
  }, [roomId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = () => {
    if (!input.trim() || !socket) return;
    socket.emit("send_message", { roomId, content: input.trim(), type: "text" });
    setInput("");
  };

  const handleTyping = () => {
    socket?.emit("typing", { roomId });
  };

  const getSenderName = (sender: Message["sender"]) => {
    if (typeof sender === "string") return sender;
    return sender.name || "Unknown";
  };

  const isMe = (sender: Message["sender"]) => {
    if (!user) return false;
    if (typeof sender === "string") return sender === user._id;
    return sender._id === user._id;
  };

  return (
    <AuthGuard>
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      <Navbar />

      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Link href="/chat" className="text-gray-400 hover:text-primary-600"><ArrowLeft size={20} /></Link>
          <h1 className="font-semibold text-sm">Ride Chat</h1>
          {typing && <span className="text-xs text-gray-400 animate-pulse">{typing} is typing...</span>}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-3">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 py-10 text-sm">No messages yet. Say hello! 👋</div>
          )}
          {messages.map((msg, i) => {
            if (msg.type === "system") {
              return <div key={i} className="text-center text-xs text-gray-400 py-1">{msg.content}</div>;
            }
            const mine = isMe(msg.sender);
            return (
              <div key={i} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[75%] ${mine ? "bg-primary-600 text-white" : "bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"} rounded-2xl px-4 py-2.5 shadow-sm`}>
                  {!mine && <p className="text-xs font-medium text-primary-600 dark:text-primary-400 mb-1">{getSenderName(msg.sender)}</p>}
                  <p className="text-sm">{msg.content}</p>
                  <p className={`text-[10px] mt-1 ${mine ? "text-primary-200" : "text-gray-400"}`}>
                    {new Date(msg.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") send(); else handleTyping(); }}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 outline-none focus:ring-2 focus:ring-primary-500 text-sm"
          />
          <button onClick={send} className="px-4 py-2.5 bg-primary-600 text-white rounded-xl hover:bg-primary-700 transition">
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}
