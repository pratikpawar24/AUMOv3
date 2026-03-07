import { Router } from "express";
import { getRoute, getMultiRoute, getEmissions, rerouteHandler, getRouteStatus } from "../controllers/route.controller";

const router = Router();

router.post("/calculate", getRoute);
router.post("/multi", getMultiRoute);
router.post("/emissions", getEmissions);
router.post("/reroute", rerouteHandler);
router.get("/status", getRouteStatus);

export default router;
