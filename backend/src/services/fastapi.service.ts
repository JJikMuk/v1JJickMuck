import FormData from "form-data";
import axios from "axios";

class FastAPIService {
    private static FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";

    /**
     * FastAPI로 이미지 전송
     * @param imageBuffer 이미지 버퍼
     * @param filename 파일명
     * @param mimetype MIME 타입
     * @param userProfile 사용자 프로필 정보
     */
    static async uploadImage(imageBuffer: Buffer, filename: string, mimetype: string, userProfile: any) {
        try {
            // FormData 생성
            const formData = new FormData();
            formData.append("file", imageBuffer, {
                filename: filename,
                contentType: mimetype,
            });

            // 사용자 정보를 JSON으로 추가
            const userInfo = {
                diet_type: userProfile.diet_type || "none",
                allergies: userProfile.allergies?.map((a: any) => a.display_name) || []
            };
            formData.append("user_info", JSON.stringify(userInfo));

            // FastAPI에 POST 요청
            const response = await axios.post(
                `${this.FASTAPI_URL}/api/upload`,
                formData,
                {
                    headers: formData.getHeaders(),
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
