import { Request, Response } from "express";
import * as ai from "../services/ai.service";
import { TrafficData } from "../models/TrafficData";
import logger from "../utils/logger";

export async function getPredictions(req: Request, res: Response) {
  try {
    logger.info("Traffic", "Predicting traffic", { segments: (req.body.segments || []).length });
    const result = await ai.getTrafficPredictions(req.body.segments || []);
    res.json(result);
  } catch (err: any) {
    logger.error("Traffic", "Traffic prediction failed", err);
    res.status(500).json({ error: "Traffic prediction failed", details: err.message });
  }
}

export async function getHeatmap(_req: Request, res: Response) {
  try {
    const result = await ai.getTrafficHeatmap();
    res.json(result);
  } catch (err: any) {
    logger.error("Traffic", "Heatmap failed", err);
    res.status(500).json({ error: "Heatmap failed", details: err.message });
  }
}

export async function getHistorical(req: Request, res: Response) {
  try {
    const { segmentId, hours = 24 } = req.query;
    const since = new Date(Date.now() - Number(hours) * 3600000);
    const data = await TrafficData.find({
      ...(segmentId ? { segmentId } : {}),
      timestamp: { $gte: since },
    }).sort({ timestamp: -1 }).limit(200);
    res.json({ data });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}

export async function getRouteSpeed(req: Request, res: Response) {
  try {
    const { origin_lat, origin_lng, dest_lat, dest_lng } = req.body;
    if (!origin_lat || !origin_lng || !dest_lat || !dest_lng) {
      return res.status(400).json({ error: "origin_lat, origin_lng, dest_lat, dest_lng required" });
    }
    logger.info("Traffic", "Route speed check", { origin_lat, origin_lng, dest_lat, dest_lng });
    const result = await ai.getRouteSpeed({ origin_lat, origin_lng, dest_lat, dest_lng });
    res.json(result);
  } catch (err: any) {
    logger.error("Traffic", "Route speed check failed", err);
    res.status(500).json({ error: "Route speed check failed", details: err.message });
  }
}

export async function getLiveSegments(req: Request, res: Response) {
  try {
    const result = await ai.getLiveSegments(req.body.segments || []);
    res.json(result);
  } catch (err: any) {
    logger.error("Traffic", "Live segments failed", err);
    res.status(500).json({ error: "Live segments failed", details: err.message });
  }
}
