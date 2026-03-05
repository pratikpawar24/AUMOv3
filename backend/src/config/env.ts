import { z } from "zod";
import dotenv from "dotenv";
dotenv.config();

const envSchema = z.object({
  PORT: z.string().default("5000"),
  MONGODB_URI: z.string().default("mongodb://localhost:27017/aumov3"),
  JWT_SECRET: z.string().default("aumo-v3-secret-key-2025"),
  AI_SERVICE_URL: z.string().default("http://localhost:8000"),
  CORS_ORIGIN: z.string().default("http://localhost:3000"),
  ADMIN_EMAIL: z.string().default("admin@aumo3.com"),
  ADMIN_PASSWORD: z.string().default("admin123"),
});

export const env = envSchema.parse(process.env);
