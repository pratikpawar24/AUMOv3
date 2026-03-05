import mongoose, { Schema, Document } from "mongoose";

export interface IUser extends Document {
  name: string;
  email: string;
  password: string;
  avatar?: string;
  phone?: string;
  role: "user" | "driver" | "admin";
  greenScore: number;
  totalRides: number;
  totalDistance: number;
  co2Saved: number;
  badges: string[];
  preferences: {
    smoking: boolean;
    music: boolean;
    petFriendly: boolean;
    quietRide: boolean;
    genderPreference: string;
  };
  createdAt: Date;
  updatedAt: Date;
}

const userSchema = new Schema<IUser>(
  {
    name: { type: String, required: true, trim: true },
    email: { type: String, required: true, unique: true, lowercase: true },
    password: { type: String, required: true, select: false },
    avatar: { type: String, default: "" },
    phone: { type: String, default: "" },
    role: { type: String, enum: ["user", "driver", "admin"], default: "user" },
    greenScore: { type: Number, default: 0 },
    totalRides: { type: Number, default: 0 },
    totalDistance: { type: Number, default: 0 },
    co2Saved: { type: Number, default: 0 },
    badges: [{ type: String }],
    preferences: {
      smoking: { type: Boolean, default: false },
      music: { type: Boolean, default: true },
      petFriendly: { type: Boolean, default: false },
      quietRide: { type: Boolean, default: false },
      genderPreference: { type: String, default: "any" },
    },
  },
  { timestamps: true }
);

export const User = mongoose.model<IUser>("User", userSchema);
