"use client";
import { create } from "zustand";
import api from "@/lib/api";
import type { Ride } from "@/types";

interface RideState {
  rides: Ride[];
  currentRide: Ride | null;
  loading: boolean;
  fetchRides: () => Promise<void>;
  fetchRide: (id: string) => Promise<void>;
  createRide: (data: any) => Promise<Ride>;
  joinRide: (id: string) => Promise<void>;
  searchRides: (params: any) => Promise<any>;
}

export const useRideStore = create<RideState>((set) => ({
  rides: [],
  currentRide: null,
  loading: false,

  fetchRides: async () => {
    set({ loading: true });
    const res = await api.get("/api/rides");
    set({ rides: res.data.rides, loading: false });
  },

  fetchRide: async (id) => {
    const res = await api.get(`/api/rides/${id}`);
    set({ currentRide: res.data.ride });
  },

  createRide: async (data) => {
    const res = await api.post("/api/rides", data);
    return res.data.ride;
  },

  joinRide: async (id) => {
    await api.post(`/api/rides/${id}/join`);
  },

  searchRides: async (params) => {
    const res = await api.get("/api/rides/search", { params });
    return res.data;
  },
}));
