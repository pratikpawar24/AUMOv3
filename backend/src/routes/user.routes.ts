import { Router } from "express";
import { register, login, getProfile, updateProfile, getLeaderboard, uploadAvatar } from "../controllers/user.controller";
import { authMiddleware } from "../middleware/auth";

const router = Router();

router.post("/register", register);
router.post("/login", login);
router.get("/profile", authMiddleware, getProfile);
router.put("/profile", authMiddleware, updateProfile);
router.post("/avatar", authMiddleware, uploadAvatar);
router.get("/leaderboard", getLeaderboard);

export default router;
