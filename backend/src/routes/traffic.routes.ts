import { Router } from "express";
import { getPredictions, getHeatmap, getHistorical, getRouteSpeed, getLiveSegments } from "../controllers/traffic.controller";

const router = Router();

router.post("/predict", getPredictions);
router.get("/heatmap", getHeatmap);
router.get("/historical", getHistorical);
router.post("/route-speed", getRouteSpeed);
router.post("/live-segments", getLiveSegments);

export default router;
