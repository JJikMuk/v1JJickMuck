import { dbpool } from "../config/mariadb";
import { ScanHistory } from "../types/dashboard.type";

class ScanHistoryModel {
    /**
     * 스캔 히스토리 저장
     */
    static async createScanHistory(userId: number, scanData: {
        product_name: string;
        risk_level: 'green' | 'yellow' | 'red';
        risk_score: number;
        risk_reason: string;
        calories?: number;
        carbs?: number;
        protein?: number;
        fat?: number;
        detected_ingredients?: string[];
        detected_allergens?: string[];
        diet_warnings?: string[];
        ocr_full_result?: any;
    }): Promise<number> {
        const connection = await dbpool.getConnection();
        try {
            const result = await connection.query(
                `INSERT INTO SCAN_HISTORY (
                    user_id, product_name, risk_level, risk_score, risk_reason,
                    calories, carbs, protein, fat,
                    detected_ingredients, detected_allergens, diet_warnings, ocr_full_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
                [
                    userId,
                    scanData.product_name,
                    scanData.risk_level,
                    scanData.risk_score,
                    scanData.risk_reason,
                    scanData.calories || null,
                    scanData.carbs || null,
                    scanData.protein || null,
                    scanData.fat || null,
                    JSON.stringify(scanData.detected_ingredients || []),
                    JSON.stringify(scanData.detected_allergens || []),
                    JSON.stringify(scanData.diet_warnings || []),
                    JSON.stringify(scanData.ocr_full_result || {})
                ]
            );
            return result.insertId;
        } finally {
            connection.release();
        }
    }

    /**
     * 사용자의 스캔 히스토리 조회 (기간별)
     */
    static async getScanHistoryByPeriod(userId: number, period: 'week' | 'month' | 'all'): Promise<ScanHistory[]> {
        const connection = await dbpool.getConnection();
        try {
            let dateCondition = '';
            if (period === 'week') {
                dateCondition = 'AND scanned_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)';
            } else if (period === 'month') {
                dateCondition = 'AND scanned_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)';
            }

            const rows = await connection.query(
                `SELECT * FROM SCAN_HISTORY
                 WHERE user_id = ? ${dateCondition}
                 ORDER BY scanned_at DESC`,
                [userId]
            );

            return rows.map((row: any) => ({
                ...row,
                detected_ingredients: typeof row.detected_ingredients === 'string'
                    ? JSON.parse(row.detected_ingredients || '[]')
                    : (row.detected_ingredients || []),
                detected_allergens: typeof row.detected_allergens === 'string'
                    ? JSON.parse(row.detected_allergens || '[]')
                    : (row.detected_allergens || []),
                diet_warnings: typeof row.diet_warnings === 'string'
                    ? JSON.parse(row.diet_warnings || '[]')
                    : (row.diet_warnings || []),
                ocr_full_result: typeof row.ocr_full_result === 'string'
                    ? JSON.parse(row.ocr_full_result || '{}')
                    : (row.ocr_full_result || {})
            }));
        } finally {
            connection.release();
        }
    }

    /**
     * 대시보드 통계 조회
     */
    static async getDashboardStats(userId: number, period: 'week' | 'month' | 'all') {
        const connection = await dbpool.getConnection();
        try {
            let dateCondition = '';
            if (period === 'week') {
                dateCondition = 'AND scanned_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)';
            } else if (period === 'month') {
                dateCondition = 'AND scanned_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)';
            }

            // 1. 전체 스캔 횟수 및 위험도 분포
            const riskDistRows = await connection.query(
                `SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN risk_level = 'green' THEN 1 ELSE 0 END) as green_count,
                    SUM(CASE WHEN risk_level = 'yellow' THEN 1 ELSE 0 END) as yellow_count,
                    SUM(CASE WHEN risk_level = 'red' THEN 1 ELSE 0 END) as red_count
                 FROM SCAN_HISTORY
                 WHERE user_id = ? ${dateCondition}`,
                [userId]
            );

            // 2. 평균 영양 정보
            const nutritionRows = await connection.query(
                `SELECT
                    AVG(calories) as avg_calories,
                    AVG(carbs) as avg_carbs,
                    AVG(protein) as avg_protein,
                    AVG(fat) as avg_fat
                 FROM SCAN_HISTORY
                 WHERE user_id = ? ${dateCondition} AND calories IS NOT NULL`,
                [userId]
            );

            // 3. 알레르기 빈도 및 식단 위반 수 (JSON 필드 집계)
            const historyRows = await connection.query(
                `SELECT detected_allergens, diet_warnings
                 FROM SCAN_HISTORY
                 WHERE user_id = ? ${dateCondition}`,
                [userId]
            );

            // 알레르기 빈도 계산
            const allergenFrequency: { [key: string]: number } = {};
            let dietViolationCount = 0;

            historyRows.forEach((row: any) => {
                const allergens = typeof row.detected_allergens === 'string'
                    ? JSON.parse(row.detected_allergens || '[]')
                    : (row.detected_allergens || []);
                allergens.forEach((allergen: string) => {
                    allergenFrequency[allergen] = (allergenFrequency[allergen] || 0) + 1;
                });

                const warnings = typeof row.diet_warnings === 'string'
                    ? JSON.parse(row.diet_warnings || '[]')
                    : (row.diet_warnings || []);
                if (warnings.length > 0) {
                    dietViolationCount++;
                }
            });

            return {
                scan_count: Number(riskDistRows[0].total_count || 0),
                risk_distribution: {
                    green: Number(riskDistRows[0].green_count || 0),
                    yellow: Number(riskDistRows[0].yellow_count || 0),
                    red: Number(riskDistRows[0].red_count || 0)
                },
                allergen_frequency: allergenFrequency,
                diet_violation_count: dietViolationCount,
                avg_nutrition: {
                    calories: parseFloat(nutritionRows[0]?.avg_calories || 0).toFixed(1),
                    carbs: parseFloat(nutritionRows[0]?.avg_carbs || 0).toFixed(1),
                    protein: parseFloat(nutritionRows[0]?.avg_protein || 0).toFixed(1),
                    fat: parseFloat(nutritionRows[0]?.avg_fat || 0).toFixed(1)
                }
            };
        } finally {
            connection.release();
        }
    }
}

export default ScanHistoryModel;
