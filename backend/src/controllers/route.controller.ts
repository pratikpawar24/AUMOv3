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
    const status = err?.response?.status;
    if (status === 503) {
      return res.status(503).json({ error: "AI routing service is still initializing. Please try again in 1-2 minutes.", code: "SERVICE_INITIALIZING" });
    }
    if (status === 504 || err?.code === "ECONNABORTED") {
      return res.status(504).json({ error: "Route calculation timed out. The AI service may be loading a large graph.", code: "TIMEOUT" });
    }
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
    const status = err?.response?.status;
    if (status === 503) {
      return res.status(503).json({ error: "AI routing service is still initializing. Please try again in 1-2 minutes.", code: "SERVICE_INITIALIZING" });
    }
    if (status === 504 || err?.code === "ECONNABORTED") {
      return res.status(504).json({ error: "Route calculation timed out. The AI service may be loading a large graph.", code: "TIMEOUT" });
    }
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

export async function getRouteStatus(_req: Request, res: Response) {
  try {
    const result = await ai.aiHealth();
    res.json({
      ready: result.status === "healthy",
      ch_ready: result.ch_ready,
      graph_nodes: result.graph_nodes,
      status: result.status,
    });
  } catch (err: any) {
    res.status(503).json({ ready: false, status: "ai_service_unavailable", error: err.message });
  }
}
