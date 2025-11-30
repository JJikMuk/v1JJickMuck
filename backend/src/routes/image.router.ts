import { Router } from "express";
import ImageController from "../controllers/image.controller";
import { authMiddleware } from "../middlewares/auth.middleware";
import { upload } from "../middlewares/upload.middleware";

const imageRouter = Router();

// 이미지 업로드 (인증 필요, FastAPI로 전달)
imageRouter.post(
    "/upload",
    authMiddleware,
    upload.single("image"),  // "image" 필드로 단일 파일 업로드
    ImageController.uploadImage
);

// FastAPI 서버 헬스 체크
imageRouter.get("/health", ImageController.checkFastAPIHealth);

export default imageRouter;
