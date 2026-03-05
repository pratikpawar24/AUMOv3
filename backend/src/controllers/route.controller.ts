import { Request, Response } from "express";
import * as ai from "../services/ai.service";
import logger from "../utils/logger";

export async function getRoute(req: Request, res: Response) {
  try {
    logger.info("Route", "Calculating route", { body: req.body });
    const result = await ai.getRoute(req.body);
    logger.info("Route", "Route calculated successfully");
    res.json(result);
  } catch (err: any) {
    logger.error("Route", "Route calculation failed", err);
    res.status(500).json({ error: "Route calculation failed", details: err.message });
  }
}

export async function getMultiRoute(req: Request, res: Response) {
  try {
    logger.info("Route", "Calculating multi-route", { body: req.body });
    const result = await ai.getMultiRoute(req.body);
    res.json(result);
  } catch (err: any) {
    logger.error("Route", "Multi-route failed", err);
    res.status(500).json({ error: "Multi-route failed", details: err.message });
  }
}

export async function getEmissions(req: Request, res: Response) {
  try {
    const result = await ai.getEmissions(req.body);
    res.json(result);
  } catch (err: any) {
    logger.error("Route", "Emission calc failed", err);
    res.status(500).json({ error: "Emission calc failed", details: err.message });
  }
}

export async function rerouteHandler(req: Request, res: Response) {
  try {
    logger.info("Route", "Rerouting", { body: req.body });
    const result = await ai.reroute(req.body);
    res.json(result);
  } catch (err: any) {
    logger.error("Route", "Reroute failed", err);
    res.status(500).json({ error: "Reroute failed", details: err.message });
  }
}
