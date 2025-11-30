import { Request, Response } from "express";
import { dbpool } from "../config/mariadb";

class AllergyController {
    // 모든 알레르기 목록 조회
    static async getAllAllergies(req: Request, res: Response) {
        try {
            const allergies = await dbpool.query(
                "SELECT id, name, display_name FROM ALLERGIES ORDER BY id"
            );

            return res.status(200).json({
                success: true,
                data: allergies
            });
        } catch (error) {
            console.error("Get allergies error:", error);
            return res.status(500).json({
                success: false,
                message: "Failed to fetch allergies"
            });
        }
    }
}

export default AllergyController;
