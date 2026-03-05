export interface User {
  id: string;
  name: string;
  email: string;
  role: "user" | "driver" | "admin";
  avatar?: string;
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
}

export interface Ride {
  _id: string;
  driver: User | string;
  passengers: (User | string)[];
  origin: { lat: number; lng: number; address: string };
  destination: { lat: number; lng: number; address: string };
  polyline: number[][];
  departureTime: string;
  status: "pending" | "active" | "completed" | "cancelled";
  seatsTotal: number;
  seatsAvailable: number;
  distanceKm: number;
  durationMin: number;
  co2Saved: number;
  fare: number;
  preferences: { smoking: boolean; music: boolean; petFriendly: boolean; quietRide: boolean };
  chatRoomId?: string;
}

export interface RouteResult {
  polyline: number[][];
  distanceKm: number;
  durationMin: number;
  co2Grams: number;
  cost: number;
  avgCongestion: number;
  algorithm: string;
  trafficOverlay?: { lat: number; lng: number; congestion: number; speed: number }[];
  co2Details?: { co2_grams: number; fuel_liters: number; fuel_type: string };
}

export interface POI {
  name: string;
  lat: number;
  lng: number;
  type: string;
  city: string;
  distance_km?: number;
}

export interface MatchResult {
  offerId: string;
  score: number;
  routeOverlap: number;
  timeCompatibility: number;
  co2SavingsGrams: number;
  estimatedFare: number;
  pickupDetourKm: number;
}
