import { Router } from "express";
import multer from "multer";
import { authMiddleware } from "../middlewares/auth.middleware";
import ImageController from "../controllers/image.controller";

const router = Router();

// multer 설정 (메모리 저장)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB
  },
});

// 이미지 업로드 (multipart/form-data)
router.post("/upload", authMiddleware, upload.single("image"), ImageController.uploadImage);

export default router;
