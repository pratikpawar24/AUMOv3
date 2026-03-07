import axios, { AxiosError } from "axios";
import { env } from "../config/env";

const aiClient = axios.create({
  baseURL: env.AI_SERVICE_URL,
  timeout: 300000,
});

// Retry wrapper: retries on 503 (service initializing) up to 3 times with exponential backoff
async function withRetry<T>(fn: () => Promise<T>, retries = 3, delayMs = 5000): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 503 && i < retries - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
        continue;
      }
      throw err;
    }
  }
  throw new Error("Max retries exceeded");
}

export async function getRoute(params: {
  origin_lat: number; origin_lng: number;
  dest_lat: number; dest_lng: number;
  departure_time?: string;
  alpha?: number; beta?: number; gamma?: number; delta?: number;
}) {
  return withRetry(async () => {
    const res = await aiClient.post("/api/route", params);
    return res.data;
  });
}

export async function getMultiRoute(params: {
  origin_lat: number; origin_lng: number;
  dest_lat: number; dest_lng: number;
  departure_time?: string;
}) {
  return withRetry(async () => {
    const res = await aiClient.post("/api/multi-route", params);
    return res.data;
  });
}

export async function getEmissions(params: {
  distance_km: number;
  avg_speed_kmh?: number;
  fuel_type?: string;
  num_passengers?: number;
}) {
  const res = await aiClient.post("/api/emissions", params);
  return res.data;
}

export async function matchRides(params: any) {
  const res = await aiClient.post("/api/match", params);
  return res.data;
}

export async function getTrafficPredictions(segments: any[]) {
  const res = await aiClient.post("/api/traffic/predict", { segments });
  return res.data;
}

export async function getTrafficHeatmap() {
  const res = await aiClient.get("/api/traffic/heatmap");
  return res.data;
}

export async function getPOIs(params: {
  query?: string; poi_type?: string; city?: string;
  lat?: number; lng?: number; radius_km?: number;
}) {
  const res = await aiClient.get("/api/poi", { params });
  return res.data;
}

export async function getPOIsForMap(bounds: {
  south: number; north: number; west: number; east: number;
  types?: string;
}) {
  const res = await aiClient.get("/api/poi/map", { params: bounds });
  return res.data;
}

export async function reroute(params: {
  current_lat: number; current_lng: number;
  dest_lat: number; dest_lng: number;
}) {
  const res = await aiClient.post("/api/reroute", params);
  return res.data;
}

export async function getRouteSpeed(params: {
  origin_lat: number; origin_lng: number;
  dest_lat: number; dest_lng: number;
}) {
  const res = await aiClient.post("/api/traffic/route-speed", params);
  return res.data;
}

export async function getLiveSegments(segments: any[]) {
  const res = await aiClient.post("/api/traffic/live-segments", { segments });
  return res.data;
}

export async function aiHealth() {
  const res = await aiClient.get("/api/health");
  return res.data;
}
