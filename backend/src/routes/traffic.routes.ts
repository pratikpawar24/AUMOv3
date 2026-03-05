import { Router } from "express";
import { getPredictions, getHeatmap, getHistorical } from "../controllers/traffic.controller";

const router = Router();

router.post("/predict", getPredictions);
router.get("/heatmap", getHeatmap);
router.get("/historical", getHistorical);

export default router;
