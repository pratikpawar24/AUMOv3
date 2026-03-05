import { Router } from "express";
import { searchPOIs, getPOIsForMap } from "../controllers/poi.controller";

const router = Router();

router.get("/search", searchPOIs);
router.get("/map", getPOIsForMap);

export default router;
