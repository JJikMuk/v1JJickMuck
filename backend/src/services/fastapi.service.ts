import FormData from "form-data";
import axios from "axios";

class FastAPIService {
    private static FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";

    /**
     * FastAPI로 이미지 전송 (OCR + RAG 분석)
     * @param imageBuffer 이미지 버퍼
     * @param filename 파일명
     * @param mimetype MIME 타입
     * @param userProfile 사용자 프로필 정보
     * @param userId 사용자 ID (RAG 분석용)
     */
    static async uploadImage(imageBuffer: Buffer, filename: string, mimetype: string, userProfile: any, userId?: string) {
        try {
            // FormData 생성
            const formData = new FormData();
            formData.append("file", imageBuffer, {
                filename: filename,
                contentType: mimetype,
            });

            // 사용자 정보를 JSON으로 추가 (RAG에 필요한 추가 정보 포함)
            const userInfo = {
                user_id: userId || userProfile.uuid || "anonymous",
                diet_type: userProfile.diet_type || "none",
                // ✅ 이미 문자열 배열이므로 그대로 사용
                allergies: userProfile.allergies || [],
                // RAG 분석을 위한 추가 정보
                height: userProfile.height || null,
                weight: userProfile.weight || null,
                age_range: userProfile.age_range || "20대",
                gender: userProfile.gender || null,
                diseases: userProfile.diseases || [],
                special_conditions: userProfile.special_conditions || []
            };
            formData.append("user_info", JSON.stringify(userInfo));

            // FastAPI에 POST 요청
            const response = await axios.post(
                `${this.FASTAPI_URL}/api/upload`,
                formData,
                {
                    headers: formData.getHeaders(),
                    timeout: 60000  // 60초 타임아웃 (RAG + GPT 처리 시간 고려)
                }
            );

            return response.data;
        } catch (error) {
            console.error("FastAPI upload error:", error);
            throw error;
        }
    }

    /**
     * FastAPI 서버 헬스 체크
     */
    static async healthCheck() {
        try {
            const response = await axios.get(`${this.FASTAPI_URL}/health`);
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }
}

export default FastAPIService;
