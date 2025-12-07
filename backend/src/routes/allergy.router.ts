import { Router } from 'express';
import AllergyController from '../controllers/allergy.controller';

const allergyRouter = Router();

// 알레르기 목록 조회
allergyRouter.get('/', AllergyController.getAllAllergies);

export default allergyRouter;
