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
