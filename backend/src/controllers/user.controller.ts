import { Request, Response } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { User } from "../models/User";
import { env } from "../config/env";
import { AuthRequest } from "../middleware/auth";

export async function register(req: Request, res: Response) {
  try {
    const { name, email, password, phone } = req.body;
    const exists = await User.findOne({ email });
    if (exists) return res.status(400).json({ error: "Email already registered" });

    const hashed = await bcrypt.hash(password, 12);
    const user = await User.create({ name, email, password: hashed, phone });

    const token = jwt.sign({ id: user._id, role: user.role }, env.JWT_SECRET, { expiresIn: "7d" });
    res.status(201).json({ token, user: { id: user._id, name: user.name, email: user.email, role: user.role } });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function login(req: Request, res: Response) {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email }).select("+password");
    if (!user) return res.status(401).json({ error: "Invalid credentials" });

    const valid = await bcrypt.compare(password, user.password);
    if (!valid) return res.status(401).json({ error: "Invalid credentials" });

    const token = jwt.sign({ id: user._id, role: user.role }, env.JWT_SECRET, { expiresIn: "7d" });
    res.json({ token, user: { id: user._id, name: user.name, email: user.email, role: user.role, greenScore: user.greenScore, badges: user.badges } });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getProfile(req: AuthRequest, res: Response) {
  try {
    const user = await User.findById(req.userId);
    if (!user) return res.status(404).json({ error: "User not found" });
    res.json({ user });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function updateProfile(req: AuthRequest, res: Response) {
  try {
    const allowedFields = ["name", "phone", "preferences"];
    const update: any = {};
    for (const key of allowedFields) {
      if (req.body[key] !== undefined) update[key] = req.body[key];
    }
    const user = await User.findByIdAndUpdate(req.userId, update, { new: true });
    res.json({ user });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function uploadAvatar(req: AuthRequest, res: Response) {
  try {
    const { avatar } = req.body; // base64 data URI
    if (!avatar || typeof avatar !== "string") return res.status(400).json({ error: "Avatar data required" });
    // Limit size to ~2MB base64
    if (avatar.length > 2_800_000) return res.status(400).json({ error: "Image too large (max 2MB)" });
    const user = await User.findByIdAndUpdate(req.userId, { avatar }, { new: true });
    res.json({ user });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getLeaderboard(_req: Request, res: Response) {
  try {
    const users = await User.find().sort({ greenScore: -1 }).limit(20).select("name greenScore badges totalRides co2Saved avatar");
    res.json({ leaderboard: users });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}
