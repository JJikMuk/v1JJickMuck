import {Request, Response} from "express";
import UserService from "../services/user.service";

class UserController {
    static async getProfile(req: Request, res: Response) {
        try {
            const user = req.user!;
            const userProfile = await UserService.getUserByUUID(user.uuid);
            return res.status(200).json({
                success: true,
                data: userProfile
            });
        }
        catch (error) {
            return res.status(500).json({
                success: false,
                message: "Failed to retrieve user profile."
            });
        }
    }

    static async updateProfile(req: Request, res: Response) {
        try {
            const user = req.user!;
            const { name, diet_type, allergy_ids } = req.body;

            // 유효성 검사
            if (name !== undefined && (!name || name.trim().length === 0)) {
                return res.status(400).json({
                    success: false,
                    message: "Name cannot be empty"
                });
            }

            if (diet_type !== undefined && diet_type !== null) {
                const validDietTypes = ['vegetarian', 'vegan', 'halal', 'kosher', 'pescatarian', 'none'];
                if (!validDietTypes.includes(diet_type)) {
                    return res.status(400).json({
                        success: false,
                        message: "Invalid diet_type. Must be one of: vegetarian, vegan, halal, kosher, pescatarian, none"
                    });
                }
            }

            if (allergy_ids !== undefined && !Array.isArray(allergy_ids)) {
                return res.status(400).json({
                    success: false,
                    message: "allergy_ids must be an array"
                });
            }

            // 프로필 업데이트
            const updatedProfile = await UserService.updateUserProfile(
                user.uuid,
                name,
                diet_type,
                allergy_ids
            );

            return res.status(200).json({
                success: true,
                message: "Profile updated successfully",
                data: updatedProfile
            });
        }
        catch (error) {
            console.error("Update profile error:", error);
            return res.status(500).json({
                success: false,
                message: "Failed to update user profile."
            });
        }
    }
}

export default UserController;