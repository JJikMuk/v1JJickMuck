import { Request, Response } from 'express';
import UserService from '../services/user.service';

interface AuthRequest extends Request {
    user?: any;
}

// ============================================
// 프로필 API
// ============================================

// 전체 프로필 조회
export const getUserFullProfile = async (req: Request, res: Response) => {
    try {
        const user = req.user!;
        const profile = await UserService.getUserFullProfile(user.uuid);

        if (!profile) {
            return res.status(404).json({
                success: false,
                message: 'Profile not found',
            });
        }

        // null 값 필터링
        const cleanedProfile = {
            ...profile,
            allergies: (profile.allergies || []).filter((a: string | null) => a !== null),
            diseases: (profile.diseases || []).filter((d: string | null) => d !== null),
            special_conditions: (profile.special_conditions || []).filter((s: string | null) => s !== null),
        };

        return res.json({
            success: true,
            data: cleanedProfile,
        });
    } catch (error) {
        console.error('Get full profile error:', error);
        res.status(500).json({ error: 'Failed to get user profile' });
    }
};

// 기존 프로필 조회 (알레르기 포함)
export const getUserProfile = async (req: AuthRequest, res: Response) => {
    try {
        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        const userWithAllergies = await UserService.getUserWithAllergies(userId);
        res.json({ success: true, data: userWithAllergies });
    } catch (error) {
        console.error('Get profile error:', error);
        res.status(500).json({ error: 'Failed to get user profile' });
    }
};

// 프로필 업데이트 (name, diet_type, allergies)
export const updateUserProfile = async (req: AuthRequest, res: Response) => {
    try {
        const { name, diet_type, allergy_ids } = req.body;

        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        await UserService.updateUserProfile(userId, name, diet_type, allergy_ids);

        const updatedUser = await UserService.getUserWithAllergies(userId);
        res.json({ success: true, data: updatedUser });
    } catch (error) {
        console.error('Update profile error:', error);
        res.status(500).json({ error: 'Failed to update profile' });
    }
};

// 건강 프로필 업데이트 (height, weight, age_range, gender)
export const updateUserHealthProfile = async (req: AuthRequest, res: Response) => {
    try {
        const { height, weight, age_range, gender } = req.body;

        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        await UserService.updateUserHealthProfile(userId, { height, weight, age_range, gender });

        const updatedProfile = await UserService.getUserFullProfile(req.user.uuid);
        res.json({ success: true, data: updatedProfile });
    } catch (error) {
        console.error('Update health profile error:', error);
        res.status(500).json({ error: 'Failed to update health profile' });
    }
};

// ============================================
// 질병 API
// ============================================

// 모든 질병 목록 조회
export const getAllDiseases = async (req: Request, res: Response) => {
    try {
        const diseases = await UserService.getAllDiseases();
        res.json({ success: true, data: diseases });
    } catch (error) {
        console.error('Get diseases error:', error);
        res.status(500).json({ error: 'Failed to get diseases' });
    }
};

// 유저 질병 조회
export const getUserDiseases = async (req: AuthRequest, res: Response) => {
    try {
        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        const diseases = await UserService.getUserDiseases(userId);
        res.json({ success: true, data: diseases });
    } catch (error) {
        console.error('Get user diseases error:', error);
        res.status(500).json({ error: 'Failed to get user diseases' });
    }
};

// 유저 질병 업데이트
export const updateUserDiseases = async (req: AuthRequest, res: Response) => {
    try {
        const { disease_ids } = req.body;

        if (!Array.isArray(disease_ids)) {
            return res.status(400).json({ error: 'disease_ids must be an array' });
        }

        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        await UserService.updateUserDiseases(userId, disease_ids);

        const updatedDiseases = await UserService.getUserDiseases(userId);
        res.json({ success: true, data: updatedDiseases });
    } catch (error) {
        console.error('Update user diseases error:', error);
        res.status(500).json({ error: 'Failed to update user diseases' });
    }
};

// ============================================
// 특수 상태 API
// ============================================

// 모든 특수 상태 목록 조회
export const getAllSpecialConditions = async (req: Request, res: Response) => {
    try {
        const conditions = await UserService.getAllSpecialConditions();
        res.json({ success: true, data: conditions });
    } catch (error) {
        console.error('Get special conditions error:', error);
        res.status(500).json({ error: 'Failed to get special conditions' });
    }
};

// 유저 특수 상태 조회
export const getUserSpecialConditions = async (req: AuthRequest, res: Response) => {
    try {
        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        const conditions = await UserService.getUserSpecialConditions(userId);
        res.json({ success: true, data: conditions });
    } catch (error) {
        console.error('Get user special conditions error:', error);
        res.status(500).json({ error: 'Failed to get user special conditions' });
    }
};

// 유저 특수 상태 업데이트
export const updateUserSpecialConditions = async (req: AuthRequest, res: Response) => {
    try {
        const { condition_ids } = req.body;

        if (!Array.isArray(condition_ids)) {
            return res.status(400).json({ error: 'condition_ids must be an array' });
        }

        const userId = await UserService.getUserIdByUuid(req.user.uuid);
        if (!userId) {
            return res.status(404).json({ error: 'User not found' });
        }

        await UserService.updateUserSpecialConditions(userId, condition_ids);

        const updatedConditions = await UserService.getUserSpecialConditions(userId);
        res.json({ success: true, data: updatedConditions });
    } catch (error) {
        console.error('Update user special conditions error:', error);
        res.status(500).json({ error: 'Failed to update user special conditions' });
    }
};