import mongoose, { Schema, Document } from "mongoose";

export interface IRide extends Document {
  driver: mongoose.Types.ObjectId;
  passengers: mongoose.Types.ObjectId[];
  origin: { lat: number; lng: number; address: string };
  destination: { lat: number; lng: number; address: string };
  waypoints: { lat: number; lng: number }[];
  polyline: number[][];
  departureTime: Date;
  status: "pending" | "active" | "completed" | "cancelled";
  seatsTotal: number;
  seatsAvailable: number;
  distanceKm: number;
  durationMin: number;
  co2Saved: number;
  fare: number;
  vehicleName: string;
  vehicleRegNo: string;
  preferences: {
    smoking: boolean;
    music: boolean;
    petFriendly: boolean;
    quietRide: boolean;
  };
  chatRoomId?: string;
  createdAt: Date;
  updatedAt: Date;
}

const rideSchema = new Schema<IRide>(
  {
    driver: { type: Schema.Types.ObjectId, ref: "User", required: true },
    passengers: [{ type: Schema.Types.ObjectId, ref: "User" }],
    origin: {
      lat: { type: Number, required: true },
      lng: { type: Number, required: true },
      address: { type: String, default: "" },
    },
    destination: {
      lat: { type: Number, required: true },
      lng: { type: Number, required: true },
      address: { type: String, default: "" },
    },
    waypoints: [{ lat: Number, lng: Number }],
    polyline: [[Number]],
    departureTime: { type: Date, required: true },
    status: {
      type: String,
      enum: ["pending", "active", "completed", "cancelled"],
      default: "pending",
    },
    seatsTotal: { type: Number, default: 3 },
    seatsAvailable: { type: Number, default: 3 },
    distanceKm: { type: Number, default: 0 },
    durationMin: { type: Number, default: 0 },
    co2Saved: { type: Number, default: 0 },
    fare: { type: Number, default: 0 },
    vehicleName: { type: String, default: "" },
    vehicleRegNo: { type: String, default: "" },
    preferences: {
      smoking: { type: Boolean, default: false },
      music: { type: Boolean, default: true },
      petFriendly: { type: Boolean, default: false },
      quietRide: { type: Boolean, default: false },
    },
    chatRoomId: { type: String },
  },
  { timestamps: true }
);

rideSchema.index({ status: 1, departureTime: 1 });
rideSchema.index({ "origin.lat": 1, "origin.lng": 1 });

export const Ride = mongoose.model<IRide>("Ride", rideSchema);
