import { Request, Response } from "express";
import { User } from "../models/User";
import { Ride } from "../models/Ride";
import { SiteStats } from "../models/TrafficData";
import { AuthRequest } from "../middleware/auth";
import * as ai from "../services/ai.service";

export async function getDashboard(_req: Request, res: Response) {
  try {
    const [totalUsers, totalRides, activeRides, aiHealthData] = await Promise.all([
      User.countDocuments(),
      Ride.countDocuments(),
      Ride.countDocuments({ status: "active" }),
      ai.aiHealth().catch(() => null),
    ]);

    const completedRides = await Ride.find({ status: "completed" });
    const totalCo2 = completedRides.reduce((s, r) => s + (r.co2Saved || 0), 0);
    const totalDist = completedRides.reduce((s, r) => s + (r.distanceKm || 0), 0);

    res.json({
      stats: { totalUsers, totalRides, activeRides, totalCo2Saved: totalCo2, totalDistance: totalDist },
      aiService: aiHealthData,
    });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAnalytics(_req: Request, res: Response) {
  try {
    // Rides per day (last 30 days)
    const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000);
    const dailyRides = await Ride.aggregate([
      { $match: { createdAt: { $gte: thirtyDaysAgo } } },
      { $group: { _id: { $dateToString: { format: "%Y-%m-%d", date: "$createdAt" } }, count: { $sum: 1 }, co2: { $sum: "$co2Saved" } } },
      { $sort: { _id: 1 } },
    ]);

    // Top routes
    const topRoutes = await Ride.aggregate([
      { $group: { _id: { oAddr: "$origin.address", dAddr: "$destination.address" }, count: { $sum: 1 } } },
      { $sort: { count: -1 } },
      { $limit: 10 },
    ]);

    // Peak hours
    const peakHours = await Ride.aggregate([
      { $group: { _id: { $hour: "$departureTime" }, count: { $sum: 1 } } },
      { $sort: { _id: 1 } },
    ]);

    res.json({ dailyRides, topRoutes, peakHours });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getAllUsers(req: Request, res: Response) {
  try {
    const page = Number(req.query.page) || 1;
    const limit = 20;
    const users = await User.find().skip((page - 1) * limit).limit(limit).sort({ createdAt: -1 });
    const total = await User.countDocuments();
    res.json({ users, total, page, pages: Math.ceil(total / limit) });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function adminLogin(req: Request, res: Response) {
  try {
    const { email, password } = req.body;
    // Simple admin check
    const { env: envConfig } = await import("../config/env");
    if (email !== envConfig.ADMIN_EMAIL || password !== envConfig.ADMIN_PASSWORD) {
      return res.status(401).json({ error: "Invalid admin credentials" });
    }

    let admin = await User.findOne({ email, role: "admin" });
    if (!admin) {
      const bcrypt = await import("bcryptjs");
      const hashed = await bcrypt.hash(password, 12);
      admin = await User.create({ name: "Admin", email, password: hashed, role: "admin" });
    }

    const jwt = await import("jsonwebtoken");
    const token = jwt.sign({ id: admin._id, role: "admin" }, envConfig.JWT_SECRET, { expiresIn: "7d" });
    res.json({ token, user: { id: admin._id, name: admin.name, email: admin.email, role: "admin" } });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}
