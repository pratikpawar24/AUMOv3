import express from "express";
import cors from "cors";
import http from "http";
import { Server as SocketIOServer } from "socket.io";
import { connectDB } from "./config/database";
import { env } from "./config/env";
import { Message } from "./models/Message";

import userRoutes from "./routes/user.routes";
import rideRoutes from "./routes/ride.routes";
import routeRoutes from "./routes/route.routes";
import trafficRoutes from "./routes/traffic.routes";
import adminRoutes from "./routes/admin.routes";
import poiRoutes from "./routes/poi.routes";

const app = express();
const server = http.createServer(app);

const io = new SocketIOServer(server, {
  cors: { origin: env.CORS_ORIGIN.split(","), methods: ["GET", "POST"] },
});

// Middleware
app.use(cors({ origin: env.CORS_ORIGIN.split(","), credentials: true }));
app.use(express.json());

// Routes
app.use("/api/users", userRoutes);
app.use("/api/rides", rideRoutes);
app.use("/api/routes", routeRoutes);
app.use("/api/traffic", trafficRoutes);
app.use("/api/admin", adminRoutes);
app.use("/api/poi", poiRoutes);

app.get("/api/health", (_req, res) => {
  res.json({ status: "healthy", service: "aumo-v3-backend", version: "3.0.0" });
});

// Socket.IO — Chat
io.on("connection", (socket) => {
  console.log(`[WS] Connected: ${socket.id}`);

  socket.on("join_room", (roomId: string) => {
    socket.join(roomId);
    console.log(`[WS] ${socket.id} joined room ${roomId}`);
  });

  socket.on("leave_room", (roomId: string) => {
    socket.leave(roomId);
  });

  socket.on("send_message", async (data: { roomId: string; senderId: string; content: string }) => {
    try {
      const msg = await Message.create({
        roomId: data.roomId,
        sender: data.senderId,
        content: data.content,
        type: "text",
      });
      const populated = await msg.populate("sender", "name avatar");
      io.to(data.roomId).emit("new_message", populated);
    } catch (err) {
      console.error("[WS] Message error:", err);
    }
  });

  socket.on("typing", (data: { roomId: string; userName: string }) => {
    socket.to(data.roomId).emit("user_typing", data.userName);
  });

  // Real-time traffic updates
  socket.on("subscribe_traffic", () => {
    socket.join("traffic_updates");
  });

  socket.on("disconnect", () => {
    console.log(`[WS] Disconnected: ${socket.id}`);
  });
});

// Broadcast traffic updates periodically
setInterval(async () => {
  try {
    const { getTrafficHeatmap } = await import("./services/ai.service");
    const data = await getTrafficHeatmap();
    io.to("traffic_updates").emit("traffic_update", data);
  } catch {
    // AI service may not be running
  }
}, 300000); // Every 5 minutes

// Start
async function start() {
  await connectDB();
  server.listen(Number(env.PORT), () => {
    console.log(`\n${"=".repeat(50)}`);
    console.log(`  AUMOv3 Backend running on port ${env.PORT}`);
    console.log(`  AI Service: ${env.AI_SERVICE_URL}`);
    console.log(`${"=".repeat(50)}\n`);
  });
}

start();

export { app, io };
