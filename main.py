# uvicorn ocr:app --reload

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from MaterialAndNutritionOCR import MaterialAndNutritionImageToText
import numpy as np
import cv2

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 요청 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- OCR 객체 준비 (서버 로드시 1번만 로드) ---
mnocr = MaterialAndNutritionImageToText()
mnocr.load_nutrition_yolo()
mnocr.load_material_yolo()
mnocr.load_easyocr()


@app.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    try:
        # 1) 업로드 파일을 메모리에서 바로 읽기
        image_bytes = await file.read()
        np_image = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

        # 2) execute() 가 경로가 아닌 이미지도 받을 수 있게 했다고 가정
        nutrition_result, material_result = mnocr.execute(img)

        return JSONResponse({
            "status": "success",
            "nutrition": nutrition_result,
            "material": material_result
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)
