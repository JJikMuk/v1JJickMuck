import { Request, Response } from "express";
import FastAPIService from "../services/fastapi.service";
import UserService from "../services/user.service";
import ScanHistoryModel from "../models/scanHistory.model";
import UsersModel from "../models/user.model";

class ImageController {
    /**
     * 이미지 업로드 - FastAPI로 전달 (OCR + RAG 분석)
     */
    static async uploadImage(req: Request, res: Response) {
        try {
            // multer로 업로드된 파일 확인
            if (!req.file) {
                return res.status(400).json({
                    success: false,
                    message: "이미지 파일이 필요합니다."
                });
            }

            // 파일 정보
            const file = req.file;
            console.log("Uploaded file:", file.originalname, file.size);

            // Base64로 변환하여 FastAPI로 전송
            const base64Image = file.buffer.toString("base64");

            // 사용자 프로필 정보 가져오기 (RAG API용 전체 프로필)
            const user = req.user!;
            const userProfile = await UserService.getUserFullProfile(user.uuid);

            // 🔍 디버깅 로그 추가
            console.log('=== image.controller - userProfile ===');
            console.log(JSON.stringify(userProfile, null, 2));
            console.log('======================================');

            if (!userProfile) {
                return res.status(404).json({
                    success: false,
                    message: "User profile not found"
                });
            }

            // FastAPI로 이미지와 사용자 정보 전송
            const fastapiResponse = await FastAPIService.uploadImage(
                file.buffer,
                file.originalname,
                file.mimetype,
                userProfile,  // 여기서 어떤 값이 전달되는지?
                user.uuid
            );

            // 스캔 히스토리 저장
            const userId = await UsersModel.getUserIdByUuid(user.uuid);
            if (userId && fastapiResponse.status === "success") {
                await ScanHistoryModel.createScanHistory(userId, {
                    product_name: fastapiResponse.product_name,
                    risk_level: fastapiResponse.risk_level,
                    risk_score: fastapiResponse.risk_score,
                    risk_reason: fastapiResponse.risk_reason,
                    calories: fastapiResponse.analysis?.nutrition?.calories ? parseFloat(fastapiResponse.analysis.nutrition.calories) : undefined,
                    carbs: fastapiResponse.analysis?.nutrition?.carbs ? parseFloat(fastapiResponse.analysis.nutrition.carbs) : undefined,
                    protein: fastapiResponse.analysis?.nutrition?.protein ? parseFloat(fastapiResponse.analysis.nutrition.protein) : undefined,
                    fat: fastapiResponse.analysis?.nutrition?.fat ? parseFloat(fastapiResponse.analysis.nutrition.fat) : undefined,
                    detected_ingredients: fastapiResponse.analysis?.detected_ingredients || [],
                    detected_allergens: fastapiResponse.analysis?.allergen_warnings?.map((w: any) => w.allergen) || [],
                    diet_warnings: fastapiResponse.analysis?.diet_warnings?.map((w: any) => w.ingredient) || [],
                    ocr_full_result: fastapiResponse
                });
            }

            return res.status(200).json({
                success: true,
                message: "Image uploaded successfully",
                data: {
                    filename: file.originalname,
                    fastapi_response: fastapiResponse
                }
            });
        } catch (error) {
            console.error("Image upload error:", error);
            return res.status(500).json({
                success: false,
                message: "이미지 업로드 중 오류가 발생했습니다."
            });
        }
    }

    /**
     * FastAPI 서버 상태 체크
     */
    static async checkFastAPIHealth(req: Request, res: Response) {
        try {
            const isHealthy = await FastAPIService.healthCheck();

            if (isHealthy) {
                return res.status(200).json({
                    success: true,
                    message: "FastAPI server is healthy"
                });
            } else {
                return res.status(503).json({
                    success: false,
                    message: "FastAPI server is unavailable"
                });
            }
        } catch (error) {
            return res.status(500).json({
                success: false,
                message: "Failed to check FastAPI health"
            });
        }
    }
}

export default ImageController;