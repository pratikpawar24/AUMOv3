import { Router } from "express";
import { getDashboard, getAnalytics, getAllUsers, adminLogin } from "../controllers/admin.controller";
import { authMiddleware, adminMiddleware } from "../middleware/auth";

const router = Router();

router.post("/login", adminLogin);
router.get("/dashboard", authMiddleware, adminMiddleware, getDashboard);
router.get("/analytics", authMiddleware, adminMiddleware, getAnalytics);
router.get("/users", authMiddleware, adminMiddleware, getAllUsers);

export default router;
