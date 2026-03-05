"use client";
import { create } from "zustand";
import api from "@/lib/api";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, phone?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("aumo_token") : null,
  loading: false,

  login: async (email, password) => {
    set({ loading: true });
    try {
      const res = await api.post("/api/users/login", { email, password });
      localStorage.setItem("aumo_token", res.data.token);
      set({ user: res.data.user, token: res.data.token, loading: false });
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },

  register: async (name, email, password, phone?) => {
    set({ loading: true });
    try {
      const res = await api.post("/api/users/register", { name, email, password, phone });
      localStorage.setItem("aumo_token", res.data.token);
      set({ user: res.data.user, token: res.data.token, loading: false });
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem("aumo_token");
    set({ user: null, token: null });
  },

  loadUser: async () => {
    try {
      const res = await api.get("/api/users/profile");
      set({ user: res.data.user });
    } catch {
      localStorage.removeItem("aumo_token");
      set({ user: null, token: null });
    }
  },
}));
