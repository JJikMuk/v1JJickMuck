from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import json
from typing import Optional
import io
from PIL import Image
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_info: str = Form(...)
):
    """
    이미지를 받아 Gemini OCR로 텍스트를 추출하고
    사용자의 알레르기 정보를 바탕으로 위험도를 분석
    """
    try:
        # user_info JSON 파싱
        user_data = json.loads(user_info)
        diet_type = user_data.get("diet_type", "none")
        allergies = user_data.get("allergies", [])

        # 이미지 읽기
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Gemini 모델 설정 (vision 모델 사용)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Gemini 분석 프롬프트 (단일 단계로 통합)
        analysis_prompt = f"""
다음 이미지는 식품의 영양성분표와 원재료 정보입니다. 아래 형식에 맞춰 정확하게 JSON으로 응답해주세요.

**사용자 정보:**
- 알레르기: {', '.join(allergies) if allergies else '없음'}
- 식단 타입: {diet_type}

**응답 형식:**
{{
  "productName": "제품명 (이미지에서 추출)",
  "ingredients": ["성분1", "성분2", ...],
  "nutrition": {{
    "calories": "칼로리 (kcal 단위, 숫자만)",
    "carbs": "탄수화물 (g 단위, 숫자만)",
    "protein": "단백질 (g 단위, 숫자만)",
    "fat": "지방 (g 단위, 숫자만)"
  }},
  "riskLevel": "HIGH 또는 MEDIUM 또는 LOW",
  "riskReason": "위험도 판단 이유 (구체적으로)",
  "detectedAllergens": ["감지된 알레르기 유발 성분"],
  "dietWarnings": ["식단 타입 위반 사항"],
  "summary": "이 제품에 대한 전체 요약 (2-3문장)"
}}

**위험도 판단 기준 (엄격하게 적용):**

HIGH (절대 섭취 금지):
- 사용자의 알레르기 성분이 원재료에 직접 포함된 경우
- 예: 땅콩 알레르기 사용자에게 "땅콩", "peanut" 등이 성분표에 명시됨

MEDIUM (주의 필요, 섭취 비추천):
- 교차오염 가능성: "~를 사용한 제조시설에서 제조", "may contain" 등의 문구
- 알레르기 성분의 파생물 포함 (예: 우유 알레르기 - 유청, 카제인 등)
- 식단 타입 위반 (예: 비건인데 유제품 포함)

LOW (안전, 섭취 가능):
- 알레르기 성분 없음
- 교차오염 위험 없음
- 식단 타입에 적합

**중요 사항:**
1. 성분명은 정확히 추출하되, 괄호 안의 세부 성분도 분리해서 포함할 것
2. 영양정보가 불명확하면 "정보 없음"으로 표시
3. detectedAllergens는 사용자 알레르기와 실제 매칭된 것만 포함
4. dietWarnings는 구체적으로 (예: "유제품 포함 - 비건 부적합")
5. 응답은 반드시 유효한 JSON 형식이어야 하며, 추가 설명 없이 JSON만 반환

**JSON만 응답하세요. 다른 텍스트는 포함하지 마세요.**
        """

        analysis_response = model.generate_content([analysis_prompt, image])
        analysis_text = analysis_response.text

        # JSON 추출 (```json ``` 태그 제거)
        if "```json" in analysis_text:
            analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
        elif "```" in analysis_text:
            analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

        analysis_data = json.loads(analysis_text)

        # 위험도 레벨 결정 (새로운 riskLevel 기준)
        risk_level_text = analysis_data.get("riskLevel", "LOW")
        if risk_level_text == "HIGH":
            risk_level = "red"
            risk_score = 90
        elif risk_level_text == "MEDIUM":
            risk_level = "yellow"
            risk_score = 50
        else:  # LOW
            risk_level = "green"
            risk_score = 10

        # 응답 구성 (새로운 형식에 맞춰)
        result = {
            "status": "success",
            "product_name": analysis_data.get("productName", "제품명 미확인"),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "analysis": {
                "detected_ingredients": analysis_data.get("ingredients", []),
                "allergen_warnings": [
                    {
                        "allergen": allergen,
                        "severity": "high",
                        "message": analysis_data.get("riskReason", "")
                    }
                    for allergen in analysis_data.get("detectedAllergens", [])
                ],
                "diet_warnings": [
                    {
                        "ingredient": warning,
                        "reason": warning
                    }
                    for warning in analysis_data.get("dietWarnings", [])
                ],
                "nutrition": analysis_data.get("nutrition", {})
            },
            "recommendation": analysis_data.get("summary", "추가 정보가 필요합니다."),
            "risk_reason": analysis_data.get("riskReason", "")
        }

        return result

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "product_name": "분석 실패",
            "risk_level": "yellow",
            "risk_score": 50,
            "analysis": {
                "detected_ingredients": [],
                "allergen_warnings": [],
                "diet_warnings": [],
                "nutrition": {}
            },
            "recommendation": f"분석 중 오류가 발생했습니다: {str(e)}",
            "risk_reason": f"JSON 파싱 오류: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "product_name": "분석 실패",
            "risk_level": "yellow",
            "risk_score": 50,
            "analysis": {
                "detected_ingredients": [],
                "allergen_warnings": [],
                "diet_warnings": [],
                "nutrition": {}
            },
            "recommendation": f"오류가 발생했습니다: {str(e)}",
            "risk_reason": f"처리 오류: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
