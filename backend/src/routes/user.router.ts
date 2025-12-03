import { Router } from 'express';
import { authMiddleware } from '../middlewares/auth.middleware';
import {
    getUserFullProfile,
    getUserProfile,
    updateUserProfile,
    updateUserHealthProfile,
    getAllDiseases,
    getUserDiseases,
    updateUserDiseases,
    getAllSpecialConditions,
    getUserSpecialConditions,
    updateUserSpecialConditions
} from '../controllers/user.controller';

const router = Router();

// ============================================
// 프로필 API
// ============================================
router.get('/profile/full', authMiddleware, getUserFullProfile);      // 전체 프로필 (RAG용)
router.get('/profile', authMiddleware, getUserProfile);               // 기본 프로필
router.put('/profile', authMiddleware, updateUserProfile);            // 기본 프로필 업데이트
router.put('/profile/health', authMiddleware, updateUserHealthProfile); // 건강 프로필 업데이트

// ============================================
// 질병 API
// ============================================
router.get('/diseases/all', getAllDiseases);                          // 전체 질병 목록 (로그인 불필요)
router.get('/diseases', authMiddleware, getUserDiseases);             // 내 질병 조회
router.put('/diseases', authMiddleware, updateUserDiseases);          // 내 질병 업데이트

// ============================================
// 특수 상태 API
// ============================================
router.get('/conditions/all', getAllSpecialConditions);               // 전체 상태 목록 (로그인 불필요)
router.get('/conditions', authMiddleware, getUserSpecialConditions);  // 내 상태 조회
router.put('/conditions', authMiddleware, updateUserSpecialConditions); // 내 상태 업데이트

export default router;