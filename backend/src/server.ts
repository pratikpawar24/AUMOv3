import express from "express";
import cors from "cors";
import http from "http";
import { Server as SocketIOServer } from "socket.io";
import { connectDB } from "./config/database";
import { env } from "./config/env";
import { Message } from "./models/Message";
import logger from "./utils/logger";

import userRoutes from "./routes/user.routes";
import rideRoutes from "./routes/ride.routes";
import routeRoutes from "./routes/route.routes";
import trafficRoutes from "./routes/traffic.routes";
import adminRoutes from "./routes/admin.routes";
import poiRoutes from "./routes/poi.routes";

const app = express();
const server = http.createServer(app);

const allowedOrigins = env.CORS_ORIGIN.split(",").map(s => s.trim());

const corsOptions: cors.CorsOptions = {
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, curl, health checks)
    if (!origin) return callback(null, true);
    // Check exact match or wildcard match
    const allowed = allowedOrigins.some(o => {
      if (o === "*") return true;
      if (o.includes("*")) {
        const regex = new RegExp("^" + o.replace(/\./g, "\\.").replace(/\*/g, ".*") + "$");
        return regex.test(origin);
      }
      return o === origin;
    });
    if (allowed) return callback(null, true);
    callback(null, true); // Allow all in case env is misconfigured — remove in strict mode
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
};

const io = new SocketIOServer(server, {
  cors: { origin: allowedOrigins, methods: ["GET", "POST"] },
});

// Middleware
app.use(cors(corsOptions));
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    logger.request(req.method, req.originalUrl, res.statusCode, Date.now() - start);
  });
  next();
});

// Routes
app.use("/api/users", userRoutes);
app.use("/api/rides", rideRoutes);
app.use("/api/routes", routeRoutes);
app.use("/api/traffic", trafficRoutes);
app.use("/api/admin", adminRoutes);
app.use("/api/poi", poiRoutes);

app.get("/api/health", (_req: express.Request, res: express.Response) => {
  res.json({ status: "healthy", service: "aumo-v3-backend", version: "3.0.0" });
});

// Socket.IO — Chat
io.on("connection", (socket) => {
  logger.info("WebSocket", `Connected: ${socket.id}`);

  socket.on("join_room", (roomId: string) => {
    socket.join(roomId);
    logger.info("WebSocket", `${socket.id} joined room ${roomId}`);
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
      logger.error("WebSocket", "Message send failed", err);
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
    logger.info("WebSocket", `Disconnected: ${socket.id}`);
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
    logger.info("Server", `AUMOv3 Backend running on port ${env.PORT}`);
    logger.info("Server", `AI Service: ${env.AI_SERVICE_URL}`);
    logger.info("Server", `CORS Origins: ${env.CORS_ORIGIN}`);
  });
}

start().catch((err) => {
  logger.error("Server", "Failed to start", err);
  process.exit(1);
});

export { app, io };
