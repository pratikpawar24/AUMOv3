import mongoose, { Schema, Document } from "mongoose";

export interface ITrafficData extends Document {
  segmentId: string;
  lat: number;
  lng: number;
  speed: number;
  volume: number;
  congestion: number;
  roadType: string;
  timestamp: Date;
}

const trafficDataSchema = new Schema<ITrafficData>(
  {
    segmentId: { type: String, required: true },
    lat: { type: Number, required: true },
    lng: { type: Number, required: true },
    speed: { type: Number, default: 40 },
    volume: { type: Number, default: 500 },
    congestion: { type: Number, default: 0.3 },
    roadType: { type: String, default: "primary" },
    timestamp: { type: Date, default: Date.now },
  },
  { timestamps: true }
);

trafficDataSchema.index({ segmentId: 1, timestamp: -1 });

export const TrafficData = mongoose.model<ITrafficData>("TrafficData", trafficDataSchema);

// Site Stats
export interface ISiteStats extends Document {
  date: Date;
  totalUsers: number;
  totalRides: number;
  totalDistance: number;
  totalCo2Saved: number;
  activeRides: number;
}

const siteStatsSchema = new Schema<ISiteStats>(
  {
    date: { type: Date, required: true, unique: true },
    totalUsers: { type: Number, default: 0 },
    totalRides: { type: Number, default: 0 },
    totalDistance: { type: Number, default: 0 },
    totalCo2Saved: { type: Number, default: 0 },
    activeRides: { type: Number, default: 0 },
  },
  { timestamps: true }
);

export const SiteStats = mongoose.model<ISiteStats>("SiteStats", siteStatsSchema);
