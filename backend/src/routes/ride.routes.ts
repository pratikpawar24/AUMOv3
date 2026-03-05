import { Router } from "express";
import { createRide, getRides, getRideById, joinRide, completeRide, searchRides, getMyRides } from "../controllers/ride.controller";
import { authMiddleware } from "../middleware/auth";

const router = Router();

router.get("/", getRides);
router.get("/search", searchRides);
router.get("/my", authMiddleware, getMyRides);
router.post("/", authMiddleware, createRide);
router.get("/:id", getRideById);
router.post("/:id/join", authMiddleware, joinRide);
router.post("/:id/complete", authMiddleware, completeRide);

export default router;
