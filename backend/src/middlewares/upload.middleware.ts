import multer from "multer";

// 메모리 스토리지 사용 (파일을 메모리에 버퍼로 저장)
const storage = multer.memoryStorage();

// 파일 필터 (이미지만 허용)
const fileFilter = (req: any, file: Express.Multer.File, cb: multer.FileFilterCallback) => {
    if (file.mimetype.startsWith("image/")) {
        cb(null, true);
    } else {
        cb(new Error("Only image files are allowed"));
    }
};

// multer 설정
export const upload = multer({
    storage: storage,
    fileFilter: fileFilter,
    limits: {
        fileSize: 10 * 1024 * 1024, // 10MB 제한
    },
});
