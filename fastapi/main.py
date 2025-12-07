from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import sys
import json
import logging
import base64
import re
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import google.generativeai as genai

# 현재 디렉토리를 sys.path에 추가
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Gemini API 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("✅ Gemini API 키 설정 완료")
else:
    logger.error("❌ GEMINI_API_KEY가 설정되지 않았습니다!")

# RAG API 설정
RAG_API_URL = os.getenv("RAG_API_URL", "https://d9d8d8c533d8.ngrok-free.app/api/v1/rag/analyze")
RAG_API_KEY = os.getenv("API_KEY")
logger.info(f"🔗 RAG API URL: {RAG_API_URL}")

# 전역 변수
security = HTTPBearer()
API_KEY = os.getenv("API_KEY", "your-fastapi-secret-key")
gemini_model = None


# ============================================
# Pydantic 모델 정의
# ============================================

class NutritionData(BaseModel):
    """영양성분 데이터"""
    calories: Optional[str] = None
    carbs: Optional[str] = None
    protein: Optional[str] = None
    fat: Optional[str] = None
    sodium: Optional[str] = None
    sugar: Optional[str] = None
    saturated_fat: Optional[str] = None
    trans_fat: Optional[str] = None
    cholesterol: Optional[str] = None
    total_content: Optional[str] = None
    serving_size: Optional[str] = None


class OCRResult(BaseModel):
    """OCR 결과 모델"""
    nutrition: dict = {}
    materials: List[str] = []


class RAGAnalysisRequestBody(BaseModel):
    """RAG 분석 요청 모델"""
    product_name: str
    ocr_result: OCRResult
    user_info: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    global gemini_model
    
    logger.info("🚀 FastAPI 서버 시작")
    
    # Gemini 모델 초기화
    try:
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("✅ Gemini 모델 초기화 완료")
    except Exception as e:
        logger.error(f"❌ Gemini 모델 초기화 실패: {e}")
    
    yield
    
    logger.info("👋 FastAPI 서버 종료")


app = FastAPI(
    title="JJikMuk Gemini OCR + RAG API",
    description="""
    ## 식품 영양 분석 Gemini OCR + RAG API
    
    ### API 구성
    - **POST /api/upload** - Gemini로 이미지 분석 + RAG 위험도 평가
    - **GET /health** - 서버 상태 확인
    
    ### 파이프라인
    1. **Gemini Vision**: 이미지에서 영양성분/원재료 추출
    2. **RAG API**: AI 기반 위험도 분석
    3. **폴백**: RAG 실패 시 규칙 기반 분석
    """,
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Gemini OCR 함수
# ============================================

async def gemini_ocr_extract(image_bytes: bytes, filename: str) -> dict:
    """
    Gemini Vision API를 사용하여 이미지에서 영양성분/원재료 추출
    """
    global gemini_model
    
    if not gemini_model:
        raise Exception("Gemini 모델이 초기화되지 않았습니다.")
    
    # 이미지를 base64로 인코딩
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # MIME 타입 결정
    extension = filename.lower().split('.')[-1] if '.' in filename else 'jpg'
    mime_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    mime_type = mime_type_map.get(extension, 'image/jpeg')
    
    # Gemini에 전송할 프롬프트
    prompt = """
이 식품 이미지에서 영양성분표와 원재료명을 추출해주세요.

반드시 아래 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):

```json
{
    "product_name": "제품명 (이미지에서 확인 가능한 경우)",
    "nutrition": {
        "calories": "칼로리 (kcal 단위, 숫자만)",
        "carbs": "탄수화물 (g 단위, 숫자만)",
        "protein": "단백질 (g 단위, 숫자만)",
        "fat": "지방 (g 단위, 숫자만)",
        "sodium": "나트륨 (mg 단위, 숫자만)",
        "sugar": "당류 (g 단위, 숫자만)",
        "saturated_fat": "포화지방 (g 단위, 숫자만)",
        "trans_fat": "트랜스지방 (g 단위, 숫자만)",
        "cholesterol": "콜레스테롤 (mg 단위, 숫자만)",
        "total_content": "총 내용량 (g 또는 ml, 숫자만)",
        "serving_size": "1회 제공량 (g 또는 ml, 숫자만)"
    },
    "materials": ["원재료1", "원재료2", "원재료3", ...],
    "allergens": ["알레르기 유발물질1", "알레르기 유발물질2", ...]
}
```

주의사항:
1. 이미지에서 확인할 수 없는 항목은 null로 표시
2. 숫자 값은 단위 없이 숫자만 (예: "200" ← "200kcal")
3. 원재료는 쉼표로 구분된 모든 성분을 배열로
4. 알레르기 유발물질 (밀, 대두, 우유, 계란, 땅콩, 견과류, 갑각류, 생선 등)이 있으면 allergens에 포함
5. JSON만 응답 (설명 텍스트 없이)
"""
    
    try:
        # Gemini API 호출
        response = gemini_model.generate_content([
            {
                "mime_type": mime_type,
                "data": image_base64
            },
            prompt
        ])
        
        response_text = response.text.strip()
        logger.info(f"📝 Gemini 원본 응답:\n{response_text}")
        
        # JSON 추출 (코드 블록 제거)
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 코드 블록 없이 JSON만 있는 경우
            json_str = response_text
        
        # JSON 파싱
        result = json.loads(json_str)
        
        return {
            "status": "success",
            "product_name": result.get("product_name", "제품명 미확인"),
            "nutrition": result.get("nutrition", {}),
            "materials": result.get("materials", []),
            "allergens": result.get("allergens", [])
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 파싱 오류: {e}")
        logger.error(f"원본 응답: {response_text}")
        return {
            "status": "error",
            "product_name": "파싱 오류",
            "nutrition": {},
            "materials": [],
            "allergens": [],
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"❌ Gemini API 오류: {e}")
        return {
            "status": "error",
            "product_name": "API 오류",
            "nutrition": {},
            "materials": [],
            "allergens": [],
            "error": str(e)
        }


# ============================================
# RAG API 호출 함수
# ============================================

async def call_rag_api(
    user_id: str,
    product_name: str,
    nutrition_data: dict,
    detected_materials: list,
    detected_allergens: list,
    user_data: dict
) -> dict:
    """RAG API 호출"""
    
    # RAG API 요청 데이터 구성
    rag_request = {
        "userId": user_id,
        "productData": {
            "productName": product_name,
            "nutritionalInfo": {
                "calories": nutrition_data.get("calories"),
                "carbohydrates": nutrition_data.get("carbs"),
                "protein": nutrition_data.get("protein"),
                "fat": nutrition_data.get("fat"),
                "sodium": nutrition_data.get("sodium"),
                "sugar": nutrition_data.get("sugar"),
                "cholesterol": nutrition_data.get("cholesterol"),
                "saturatedFat": nutrition_data.get("saturated_fat"),
                "transFat": nutrition_data.get("trans_fat")
            },
            "ingredients": detected_materials,
            "allergens": detected_allergens
        },
        "userProfile": {
            "height": user_data.get("height"),
            "weight": user_data.get("weight"),
            "ageRange": user_data.get("age_range"),
            "gender": user_data.get("gender"),
            "allergies": user_data.get("allergies", []),
            "diseases": user_data.get("diseases", []),
            "specialConditions": user_data.get("special_conditions", [])
        }
    }
    
    print("\n" + "="*60)
    print("🤖 RAG API 요청")
    print("="*60)
    print(f"🌐 URL: {RAG_API_URL}")
    print(f"📨 요청 데이터:\n{json.dumps(rag_request, ensure_ascii=False, indent=2)}")
    print("="*60)
    
    logger.info(f"🔍 RAG API 호출: {RAG_API_URL}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Content-Type": "application/json"}
            
            # Add authorization header if API key exists
            if RAG_API_KEY:
                headers["Authorization"] = f"Bearer {RAG_API_KEY}"
            
            response = await client.post(
                RAG_API_URL,
                json=rag_request,
                headers=headers
            )
        
        print("\n" + "="*60)
        print("🎯 RAG API 응답")
        print("="*60)
        print(f"📡 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            rag_data = response.json()
            print("✅ RAG 분석 성공!")
            print(f"📄 응답 데이터:\n{json.dumps(rag_data, ensure_ascii=False, indent=2)}")
            print("="*60)
            
            logger.info(f"✅ RAG 분석 완료")
            
            return {
                "success": True,
                "data": rag_data
            }
        else:
            print(f"❌ RAG API 오류!")
            print(f"📄 응답 내용: {response.text}")
            print("="*60)
            
            logger.error(f"❌ RAG API 오류: {response.status_code}")
            
            return {
                "success": False,
                "error": f"RAG API 오류: {response.status_code}"
            }
            
    except httpx.TimeoutException:
        logger.error("❌ RAG API 타임아웃")
        return {"success": False, "error": "RAG API 타임아웃"}
    except Exception as e:
        logger.error(f"❌ RAG API 호출 실패: {e}")
        return {"success": False, "error": str(e)}


# ============================================
# 폴백 분석 함수 (RAG 실패 시)
# ============================================

def check_allergen_match(detected_materials: list, detected_allergens: list, user_allergies: list) -> list:
    """원재료/알레르기 유발물질과 사용자 알레르기 매칭"""
    allergen_warnings = []
    
    # None 값 필터링
    valid_allergies = [a for a in user_allergies if a is not None and isinstance(a, str)]
    
    # 알레르기 매핑 (한글 ↔ 영문)
    allergen_mapping = {
        "밀": ["밀", "wheat", "글루텐", "gluten", "소맥분"],
        "우유": ["우유", "milk", "유제품", "dairy", "유청", "카제인", "lactose", "치즈", "버터"],
        "대두": ["대두", "soy", "soybean", "콩"],
        "계란": ["계란", "egg", "난류", "난백", "난황", "알"],
        "땅콩": ["땅콩", "peanut"],
        "견과류": ["견과류", "호두", "아몬드", "캐슈넛", "피스타치오", "잣", "nut", "헤이즐넛", "마카다미아"],
        "갑각류": ["새우", "게", "shrimp", "crab", "갑각류", "랍스터", "크랩"],
        "조개류": ["조개", "굴", "홍합", "전복", "오징어", "clam", "oyster", "조개류"],
        "생선": ["고등어", "연어", "참치", "fish", "생선", "어류"],
        "메밀": ["메밀", "buckwheat"],
        "복숭아": ["복숭아", "peach"],
        "토마토": ["토마토", "tomato"],
        "돼지고기": ["돼지고기", "pork", "돈육"],
        "쇠고기": ["쇠고기", "beef", "우육"],
        "닭고기": ["닭고기", "chicken", "계육"],
        "아황산류": ["아황산류", "sulfite", "아황산", "이산화황"],
    }
    
    # 검사할 재료 목록 (원재료 + 알레르기 유발물질)
    all_ingredients = list(set(detected_materials + detected_allergens))
    
    for user_allergy in valid_allergies:
        user_allergy_lower = user_allergy.lower()
        
        # 알레르기 매핑에서 관련 키워드 가져오기
        related_keywords = []
        for allergy_key, keywords in allergen_mapping.items():
            if user_allergy_lower in [k.lower() for k in keywords] or user_allergy == allergy_key:
                related_keywords = keywords
                break
        
        if not related_keywords:
            related_keywords = [user_allergy]
        
        # 재료에서 알레르기 성분 검색
        for ingredient in all_ingredients:
            if ingredient is None:
                continue
            ingredient_lower = ingredient.lower()
            
            for keyword in related_keywords:
                if keyword.lower() in ingredient_lower:
                    allergen_warnings.append({
                        "allergen": user_allergy,
                        "ingredient": ingredient,
                        "severity": "high",
                        "message": f"'{ingredient}'에 '{user_allergy}' 알레르기 성분이 포함되어 있습니다."
                    })
                    break
    
    # 중복 제거
    seen = set()
    unique_warnings = []
    for warning in allergen_warnings:
        key = (warning["allergen"], warning["ingredient"])
        if key not in seen:
            seen.add(key)
            unique_warnings.append(warning)
    
    return unique_warnings


def check_diet_warnings(detected_ingredients: List[str], diet_type: str) -> List[dict]:
    """식단 타입에 따른 경고 생성"""
    warnings = []
    
    if diet_type == "none" or not diet_type:
        return warnings
    
    # 동물성 제품
    animal_products = ["우유", "유제품", "계란", "난류", "치즈", "버터", "크림", "유청", "카제인", "요거트", "요구르트"]
    meat_products = ["돼지고기", "쇠고기", "닭고기", "돈육", "우육", "계육", "육류", "소고기", "돼지", "닭", "오리"]
    fish_products = ["생선", "어류", "고등어", "연어", "참치", "멸치", "새우", "게", "오징어", "조개"]
    
    for ingredient in detected_ingredients:
        if ingredient is None:
            continue
        ingredient_lower = ingredient.lower()
        
        if diet_type == "vegan":
            # 비건: 모든 동물성 제품 제외
            for animal in animal_products + meat_products + fish_products:
                if animal in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"비건 식단 부적합: '{ingredient}' 포함"
                    })
                    break
        
        elif diet_type == "vegetarian":
            # 채식: 육류, 생선 제외 (유제품, 계란은 허용)
            for meat in meat_products + fish_products:
                if meat in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"채식 식단 부적합: '{ingredient}' 포함"
                    })
                    break
        
        elif diet_type == "pescatarian":
            # 페스코: 육류만 제외 (생선, 유제품, 계란 허용)
            for meat in meat_products:
                if meat in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"페스코 식단 부적합: '{ingredient}' 포함"
                    })
                    break
        
        elif diet_type == "halal":
            # 할랄: 돼지고기, 알코올 제외
            halal_forbidden = ["돼지고기", "돼지", "돈육", "pork", "알코올", "와인", "맥주", "소주"]
            for forbidden in halal_forbidden:
                if forbidden in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"할랄 식단 부적합: '{ingredient}' 포함"
                    })
                    break
        
        elif diet_type == "kosher":
            # 코셔: 돼지고기, 갑각류, 유제품+육류 조합 제외
            kosher_forbidden = ["돼지고기", "돼지", "돈육", "새우", "게", "랍스터", "조개", "굴"]
            for forbidden in kosher_forbidden:
                if forbidden in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"코셔 식단 부적합: '{ingredient}' 포함"
                    })
                    break
    
    return warnings


def fallback_analyze(
    detected_materials: list,
    detected_allergens: list,
    user_allergies: list,
    diet_type: str
) -> dict:
    """RAG 실패 시 규칙 기반 폴백 분석"""
    
    print("\n" + "="*60)
    print("⚠️ RAG 실패 → 규칙 기반 폴백 분석")
    print("="*60)
    
    allergen_warnings = check_allergen_match(detected_materials, detected_allergens, user_allergies)
    diet_warnings = check_diet_warnings(detected_materials + detected_allergens, diet_type)
    
    # 위험도 결정
    if len(allergen_warnings) > 0:
        risk_level = "red"
        risk_score = min(90 + len(allergen_warnings) * 5, 100)
        risk_reason = f"알레르기 성분 감지: {', '.join([w['allergen'] for w in allergen_warnings])}"
        recommendation = f"⚠️ 주의! {', '.join(set([w['allergen'] for w in allergen_warnings]))} 알레르기 성분이 포함되어 있습니다. 섭취를 피해주세요."
    elif len(diet_warnings) > 0:
        risk_level = "yellow"
        risk_score = 50 + len(diet_warnings) * 10
        risk_reason = f"식단 주의: {diet_type} 식단에 부적합한 성분 포함"
        recommendation = f"🟡 주의! {diet_type} 식단에 맞지 않는 성분이 포함되어 있습니다: {', '.join([w['ingredient'] for w in diet_warnings])}"
    else:
        risk_level = "green"
        risk_score = 10
        risk_reason = "알레르기 및 식단 위험 요소 없음"
        recommendation = "✅ 안전합니다. 알레르기 및 식단 관련 위험 요소가 발견되지 않았습니다."
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_reason": risk_reason,
        "recommendation": recommendation,
        "allergen_warnings": allergen_warnings,
        "diet_warnings": diet_warnings,
        "rag_enabled": False
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy", 
        "gemini_model": gemini_model is not None,
        "gemini_api_key": GEMINI_API_KEY is not None,
        "rag_api_url": RAG_API_URL
    }


# ============================================
# 통합 API: /api/upload
# ============================================

@app.post("/api/upload", tags=["Upload"])
async def upload_image(
    file: UploadFile = File(...),
    user_info: str = Form(...)
):
    """
    ## Gemini Vision OCR + RAG를 사용한 식품 이미지 분석
    
    ### 파이프라인
    1. Gemini Vision으로 이미지에서 영양성분/원재료 추출
    2. RAG API로 AI 기반 위험도 분석
    3. RAG 실패 시 규칙 기반 폴백 분석
    """
    try:
        user_data = json.loads(user_info)
        
        # 파일명 처리
        filename = file.filename or "unknown.jpg"
        from urllib.parse import unquote
        filename = unquote(filename)
        
        logger.info(f"📤 업로드 요청: {filename}")
        logger.info(f"👤 사용자 정보: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
        
        # ============================================
        # 1. Gemini OCR 실행
        # ============================================
        image_bytes = await file.read()
        
        print("\n" + "="*60)
        print("🤖 Gemini Vision OCR 처리 시작")
        print("="*60)
        
        ocr_result = await gemini_ocr_extract(image_bytes, filename)
        
        if ocr_result["status"] == "error":
            logger.error(f"❌ OCR 실패: {ocr_result.get('error')}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "product_name": "OCR 실패",
                    "risk_level": "yellow",
                    "risk_score": 50,
                    "analysis": {"detected_ingredients": [], "allergen_warnings": [], "diet_warnings": [], "nutrition": {}},
                    "recommendation": f"이미지 분석 실패: {ocr_result.get('error')}",
                    "risk_reason": "OCR 처리 오류",
                    "rag_enabled": False,
                    "raw_ocr": {"nutrition": {}, "materials": []}
                }
            )
        
        product_name = ocr_result.get("product_name", filename.rsplit('.', 1)[0])
        nutrition_data = ocr_result.get("nutrition", {})
        detected_materials = ocr_result.get("materials", [])
        detected_allergens = ocr_result.get("allergens", [])
        
        # OCR 결과 출력
        print(f"📦 제품명: {product_name}")
        print("-"*60)
        print("📊 영양성분:")
        if nutrition_data:
            for key, value in nutrition_data.items():
                if value:
                    print(f"   • {key}: {value}")
        print("-"*60)
        print("🥗 원재료:")
        if detected_materials:
            for i, material in enumerate(detected_materials, 1):
                print(f"   {i}. {material}")
        print("-"*60)
        print("⚠️ 알레르기 유발물질:")
        if detected_allergens:
            for allergen in detected_allergens:
                print(f"   • {allergen}")
        print("="*60 + "\n")
        
        logger.info(f"✅ Gemini OCR 완료 - 영양성분: {len([v for v in nutrition_data.values() if v])}개, 원재료: {len(detected_materials)}개")
        
        # ============================================
        # 2. RAG API 호출
        # ============================================
        user_id = user_data.get("user_id", "anonymous")
        user_allergies = user_data.get("allergies", [])
        diet_type = user_data.get("diet_type", "none")
        
        rag_response = await call_rag_api(
            user_id=user_id,
            product_name=product_name,
            nutrition_data=nutrition_data,
            detected_materials=detected_materials,
            detected_allergens=detected_allergens,
            user_data=user_data
        )
        
        # ============================================
        # 3. 결과 처리
        # ============================================
        if rag_response["success"]:
            # RAG 성공
            rag_data = rag_response["data"]
            
            # RAG 응답에서 analysis 객체 추출
            analysis = rag_data.get("analysis", {})
            
            # suitability → risk_level 매핑
            suitability = analysis.get("suitability", "safe")
            suitability_map = {
                "danger": "red",
                "warning": "yellow", 
                "safe": "green",
                "caution": "yellow"
            }
            risk_level = suitability_map.get(suitability, "green")
            
            # score → risk_score
            risk_score = analysis.get("score", 0)
            
            # recommendations → recommendation (배열을 문자열로)
            recommendations = analysis.get("recommendations", [])
            nutritional_advice = analysis.get("nutritionalAdvice", "")
            
            if recommendations:
                recommendation = "\n".join([f"• {r}" for r in recommendations])
                if nutritional_advice:
                    recommendation += f"\n\n{nutritional_advice}"
            else:
                recommendation = nutritional_advice or "분석 결과를 확인해주세요."
            
            # alternatives 처리
            alternatives = analysis.get("alternatives", [])
            
            # risk_reason 생성
            if risk_level == "red":
                risk_reason = "위험: 알레르기 또는 건강 위험 성분 포함"
            elif risk_level == "yellow":
                risk_reason = "주의: 건강 상태에 따라 섭취 주의 필요"
            else:
                risk_reason = "안전: 특별한 위험 요소 없음"
            
            analyze_result = {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "risk_reason": risk_reason,
                "recommendation": recommendation,
                "allergen_warnings": [],
                "diet_warnings": [],
                "alternatives": alternatives,
                "rag_enabled": True
            }
            
            print(f"✅ RAG 분석 매핑 완료:")
            print(f"   suitability: {suitability} → risk_level: {risk_level}")
            print(f"   score: {risk_score}")
            print(f"   recommendations: {len(recommendations)}개")
        else:
            # RAG 실패 → 폴백 분석
            logger.warning(f"⚠️ RAG 실패, 폴백 분석 실행: {rag_response.get('error')}")
            analyze_result = fallback_analyze(
                detected_materials=detected_materials,
                detected_allergens=detected_allergens,
                user_allergies=user_allergies,
                diet_type=diet_type
            )
        
        # ============================================
        # 최종 결과 출력
        # ============================================
        print("\n" + "="*60)
        print("📊 최종 분석 결과")
        print("="*60)
        print(f"📦 제품명: {product_name}")
        print(f"🚦 위험도: {analyze_result['risk_level'].upper()} (점수: {analyze_result['risk_score']})")
        print(f"📝 사유: {analyze_result.get('risk_reason', 'N/A')}")
        print(f"💡 권장사항: {analyze_result.get('recommendation', 'N/A')}")
        print(f"🤖 RAG 사용: {'예' if analyze_result.get('rag_enabled') else '아니오 (폴백)'}")
        print("="*60 + "\n")
        
        logger.info(f"📊 분석 완료: {product_name} → {analyze_result['risk_level']}")
        
        return {
            "status": "success",
            "product_name": product_name,
            "risk_level": analyze_result["risk_level"],
            "risk_score": analyze_result["risk_score"],
            "analysis": {
                "detected_ingredients": detected_materials,
                "allergen_warnings": analyze_result.get("allergen_warnings", []),
                "diet_warnings": analyze_result.get("diet_warnings", []),
                "nutrition": nutrition_data,
                "alternatives": analyze_result.get("alternatives", [])
            },
            "recommendation": analyze_result.get("recommendation", ""),
            "risk_reason": analyze_result.get("risk_reason", ""),
            "rag_enabled": analyze_result.get("rag_enabled", False),
            "raw_ocr": {
                "nutrition": nutrition_data,
                "materials": detected_materials,
                "allergens": detected_allergens
            }
        }

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 파싱 오류: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "product_name": "분석 실패",
                "risk_level": "yellow",
                "risk_score": 50,
                "analysis": {"detected_ingredients": [], "allergen_warnings": [], "diet_warnings": [], "nutrition": {}},
                "recommendation": f"사용자 정보 파싱 오류: {str(e)}",
                "risk_reason": f"JSON 파싱 오류: {str(e)}",
                "rag_enabled": False,
                "raw_ocr": {"nutrition": {}, "materials": []}
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"❌ 처리 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "product_name": "분석 실패",
                "risk_level": "yellow",
                "risk_score": 50,
                "analysis": {"detected_ingredients": [], "allergen_warnings": [], "diet_warnings": [], "nutrition": {}},
                "recommendation": f"처리 중 오류: {str(e)}",
                "risk_reason": f"처리 오류: {str(e)}",
                "rag_enabled": False,
                "raw_ocr": {"nutrition": {}, "materials": []}
            }
        )


# ============================================
# OCR 전용 API
# ============================================

@app.post("/api/ocr", tags=["OCR"])
async def ocr_only(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form(None)
):
    """
    ## Gemini Vision OCR만 실행 (분석 없이 텍스트 추출만)
    """
    try:
        image_bytes = await file.read()
        filename = file.filename or "unknown.jpg"
        
        ocr_result = await gemini_ocr_extract(image_bytes, filename)
        
        return {
            "status": ocr_result["status"],
            "product_name": product_name or ocr_result.get("product_name", "제품명 미확인"),
            "ocr_result": {
                "nutrition": ocr_result.get("nutrition", {}),
                "materials": ocr_result.get("materials", []),
                "allergens": ocr_result.get("allergens", [])
            }
        }
        
    except Exception as e:
        logger.error(f"❌ OCR 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "product_name": "OCR 실패",
                "ocr_result": {"nutrition": {}, "materials": [], "allergens": []},
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    # Windows 콘솔 인코딩 설정
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    uvicorn.run(app, host="0.0.0.0", port=8000)