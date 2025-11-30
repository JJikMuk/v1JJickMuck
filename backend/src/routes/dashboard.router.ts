import { Router } from "express";
import DashboardController from "../controllers/dashboard.controller";
import { authMiddleware } from "../middlewares/auth.middleware";

const router = Router();

// 모든 대시보드 API는 인증 필요
router.use(authMiddleware);

/**
 * GET /api/dashboard/stats
 * 대시보드 통계 조회
 * Query: period (week | month | all)
 */
router.get("/stats", DashboardController.getStats);

/**
 * GET /api/dashboard/history
 * 스캔 히스토리 목록 조회
 * Query: period (week | month | all)
 */
router.get("/history", DashboardController.getHistory);

export default router;
