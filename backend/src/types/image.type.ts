// 이미지 업로드 관련 타입 정의

export interface ImageUploadResponse {
    success: boolean;
    message: string;
    data?: {
        filename: string;
        fastapi_response?: any;
    };
}

export interface FastAPIImageRequest {
    image: Buffer;
    filename: string;
    mimetype: string;
}
