import { Router } from 'express';
import AuthController from '../controllers/auth.controller';

const router = Router();

// 이메일/비밀번호 인증
// POST /api/auth/register
router.post('/register', AuthController.register);
// POST /api/auth/login
router.post('/login', AuthController.login);

export default router;