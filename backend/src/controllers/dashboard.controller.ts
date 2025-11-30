import { Request, Response } from "express";
import ScanHistoryModel from "../models/scanHistory.model";
import UsersModel from "../models/user.model";

class DashboardController {
    /**
     * 대시보드 통계 조회
     * GET /api/dashboard/stats?period=week
     */
    static async getStats(req: Request, res: Response) {
        try {
            const user = req.user!;
            const period = (req.query.period as 'week' | 'month' | 'all') || 'week';

            // 유효한 period 값 검증
            if (!['week', 'month', 'all'].includes(period)) {
                return res.status(400).json({
                    success: false,
                    message: "Invalid period. Use 'week', 'month', or 'all'"
                });
            }

            const userId = await UsersModel.getUserIdByUuid(user.uuid);
            if (!userId) {
                return res.status(404).json({
                    success: false,
                    message: "User not found"
                });
            }

            const stats = await ScanHistoryModel.getDashboardStats(userId, period);

            return res.status(200).json({
                success: true,
                data: stats
            });
        } catch (error) {
            console.error("Dashboard stats error:", error);
            return res.status(500).json({
                success: false,
                message: "Failed to fetch dashboard stats"
            });
        }
    }

    /**
     * 스캔 히스토리 목록 조회
     * GET /api/dashboard/history?period=week
     */
    static async getHistory(req: Request, res: Response) {
        try {
            const user = req.user!;
            const period = (req.query.period as 'week' | 'month' | 'all') || 'week';

            // 유효한 period 값 검증
            if (!['week', 'month', 'all'].includes(period)) {
                return res.status(400).json({
                    success: false,
                    message: "Invalid period. Use 'week', 'month', or 'all'"
                });
            }

            const userId = await UsersModel.getUserIdByUuid(user.uuid);
            if (!userId) {
                return res.status(404).json({
                    success: false,
                    message: "User not found"
                });
            }

            const history = await ScanHistoryModel.getScanHistoryByPeriod(userId, period);

            return res.status(200).json({
                success: true,
                data: history
            });
        } catch (error) {
            console.error("Dashboard history error:", error);
            return res.status(500).json({
                success: false,
                message: "Failed to fetch scan history"
            });
        }
    }
}

export default DashboardController;
