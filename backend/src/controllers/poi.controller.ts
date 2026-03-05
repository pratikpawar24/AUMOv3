import { Request, Response } from "express";
import * as ai from "../services/ai.service";

export async function searchPOIs(req: Request, res: Response) {
  try {
    const result = await ai.getPOIs(req.query as any);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: "POI search failed", details: err.message });
  }
}

export async function getPOIsForMap(req: Request, res: Response) {
  try {
    const result = await ai.getPOIsForMap(req.query as any);
    res.json(result);
  } catch (err: any) {
    res.status(500).json({ error: "POI map query failed", details: err.message });
  }
}
