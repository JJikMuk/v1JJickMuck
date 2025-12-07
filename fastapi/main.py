from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import sys
import json
import logging
from typing import Optional, List
import cv2
import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx  # 추가 (비동기 HTTP 클라이언트)

# 현재 디렉토리를 sys.path에 추가 (모듈 임포트를 위해)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# MaterialAndNutritionOCR 모듈 임포트
from MaterialAndNutritionOCR.MaterialAndNutritionImageToText import MaterialAndNutritionImageToText

# RAG 모듈 임포트 (v1JJickMuck-main에서)
sys.path.insert(0, os.path.join(CURRENT_DIR, "v1JJickMuck-main", "fastapi"))
try:
    from app.config.settings import get_settings
    from app.services.rag_service import RAGService
    from app.services.gpt_service import GPTService
    from app.models.rag_models import (
        RAGAnalysisRequest, 
        RAGAnalysisResponse,
        UserProfile, 
        ProductData, 
        NutritionalInfo
    )
    from app.database import init_database
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAG 모듈 로드 실패 (OCR만 사용): {e}")
    RAG_AVAILABLE = False

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 전역 모델 변수
ocr_model = None
rag_service = None
gpt_service = None
security = HTTPBearer()
API_KEY = os.getenv("API_KEY", "your-fastapi-secret-key")


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
    global ocr_model, rag_service, gpt_service
    
    logger.info("🚀 FastAPI 서버 시작")
    
    # 1. YOLO + EasyOCR 모델 로드
    try:
        ocr_model = MaterialAndNutritionImageToText()
        ocr_model.load_nutrition_yolo()
        ocr_model.load_material_yolo()
        ocr_model.load_easyocr()
        logger.info("✅ YOLO + EasyOCR 모델 로드 완료")
    except Exception as e:
        logger.error(f"❌ OCR 모델 로드 실패: {e}")
    
    # 2. RAG 서비스 초기화 (RAG 모듈이 로드된 경우만)
    if RAG_AVAILABLE:
        try:
            rag_service = RAGService()
            gpt_service = GPTService()
            logger.info("✅ RAG + GPT 서비스 초기화 완료")
        except Exception as e:
            logger.warning(f"⚠️ RAG 서비스 초기화 실패 (OCR만 사용): {e}")
        
        # 3. 데이터베이스 연결 (PostgreSQL + pgvector)
        try:
            await init_database()
            logger.info("✅ PostgreSQL + pgvector 연결 완료")
        except Exception as e:
            logger.warning(f"⚠️ 데이터베이스 연결 실패 (RAG 없이 동작): {e}")
    else:
        logger.info("ℹ️ RAG 모듈 비활성화 - OCR 전용 모드로 실행")
    
    yield
    
    logger.info("👋 FastAPI 서버 종료")


app = FastAPI(
    title="JJikMuk OCR + RAG API",
    description="""
    ## 식품 영양 분석 OCR + RAG + LLM 통합 API
    
    ### API 구성
    - **POST /api/ocr** - YOLO + EasyOCR로 이미지에서 텍스트 추출
    - **POST /api/analyze** - RAG + GPT로 사용자 맞춤 위험도 분석
    
    ### 아키텍처
    ```
    Front → Node.js → FastAPI(/api/ocr) → Node.js → FastAPI(/api/analyze) → Node.js → Front
    ```
    
    ### 파이프라인
    1. **YOLO**: 이미지에서 텍스트 영역 감지
    2. **EasyOCR**: 감지된 영역에서 텍스트 추출
    3. **RAG**: PostgreSQL + pgvector로 관련 규칙/지식 검색
    4. **GPT**: 개인화된 영양 조언 생성
    """,
    version="2.0.0",
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

# 알레르기 매핑 (한글 ↔ 영문)
ALLERGEN_MAPPING = {
    "밀": ["밀", "wheat", "글루텐", "gluten"],
    "우유": ["우유", "milk", "유제품", "dairy", "유청", "카제인", "lactose"],
    "대두": ["대두", "soy", "soybean", "콩"],
    "돼지고기": ["돼지고기", "pork", "돈육"],
    "쇠고기": ["쇠고기", "beef", "우육"],
    "아황산류": ["아황산류", "sulfite", "아황산"],
    "계란": ["계란", "egg", "난류", "난백", "난황"],
    "땅콩": ["땅콩", "peanut"],
    "견과류": ["견과류", "호두", "아몬드", "캐슈넛", "피스타치오", "잣", "nut"],
    "갑각류": ["새우", "게", "shrimp", "crab", "갑각류"],
    "조개류": ["조개", "굴", "홍합", "전복", "오징어", "clam", "oyster"],
    "생선": ["고등어", "연어", "참치", "fish"],
    "메밀": ["메밀", "buckwheat"],
    "토마토": ["토마토", "tomato"],
    "복숭아": ["복숭아", "peach"],
}


def check_allergen_match(detected_materials: list, allergies: list) -> list:
    """원재료와 사용자 알레르기 매칭"""
    allergen_warnings = []
    
    # None 값 필터링
    valid_allergies = [a for a in allergies if a is not None and isinstance(a, str)]
    
    for material in detected_materials:
        if material is None:
            continue
        material_lower = material.lower()
        
        for user_allergy in valid_allergies:
            user_allergy_lower = user_allergy.lower()
            
            if user_allergy_lower in material_lower or material_lower in user_allergy_lower:
                allergen_warnings.append({
                    "allergen": user_allergy,
                    "ingredient": material,
                    "severity": "high",
                    "message": f"'{material}'에 '{user_allergy}' 알레르기 성분이 포함되어 있습니다."
                })
    
    return allergen_warnings


def check_diet_warnings(detected_ingredients: List[str], diet_type: str) -> List[dict]:
    """식단 타입에 따른 경고 생성"""
    warnings = []
    
    if diet_type == "none":
        return warnings
    
    # 비건/채식 관련 성분
    animal_products = ["우유", "유제품", "계란", "난류", "치즈", "버터", "크림", "유청", "카제인"]
    meat_products = ["돼지고기", "쇠고기", "닭고기", "돈육", "우육", "계육", "육류"]
    
    for ingredient in detected_ingredients:
        ingredient_lower = ingredient.lower()
        
        if diet_type == "vegan":
            for animal in animal_products + meat_products:
                if animal in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"비건 식단 부적합: {ingredient} 포함"
                    })
                    break
        
        elif diet_type == "vegetarian":
            for meat in meat_products:
                if meat in ingredient_lower:
                    warnings.append({
                        "ingredient": ingredient,
                        "reason": f"채식 식단 부적합: {ingredient} 포함"
                    })
                    break
    
    return warnings


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy", 
        "ocr_model": ocr_model is not None,
        "rag_service": rag_service is not None,
        "gpt_service": gpt_service is not None
    }


# ============================================
# API 1: OCR API (YOLO + EasyOCR)
# ============================================

@app.post("/api/ocr", tags=["OCR"])
async def ocr_extract(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form(None)
):
    """
    ## YOLO + EasyOCR로 이미지에서 영양성분/원재료 텍스트 추출
    
    ### Request
    - **file**: 이미지 파일 (jpg, png 등)
    - **product_name**: 제품명 (선택, 없으면 파일명 사용)
    
    ### Response
    ```json
    {
        "status": "success",
        "product_name": "제품명",
        "ocr_result": {
            "nutrition": {"calories": "200", "protein": "5g", ...},
            "materials": ["밀가루", "설탕", "우유", ...]
        },
        "raw_ocr": {
            "nutrition": {"kcal": 200, "단백질": 5, ...},
            "materials": ["밀가루", "설탕", "우유", ...]
        }
    }
    ```
    """
    try:
        # 이미지 읽기 및 OpenCV 형식으로 변환
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "이미지를 읽을 수 없습니다. 다른 이미지를 시도해주세요.",
                    "product_name": product_name or "이미지 오류",
                    "ocr_result": {"nutrition": {}, "materials": []},
                    "raw_ocr": {"nutrition": {}, "materials": []}
                }
            )

        # 제품명 설정
        final_product_name = product_name or (file.filename.rsplit('.', 1)[0] if file.filename else "제품명 미확인")

        # YOLO + EasyOCR 실행
        logger.info(f"📷 OCR 처리 시작: {final_product_name}")
        nutrition_result, material_result = ocr_model.execute(image)
        logger.info(f"✅ OCR 완료 - 영양성분: {len(nutrition_result) if nutrition_result else 0}개, 원재료: {len(material_result) if material_result else 0}개")

        # 영양성분 파싱 (표준화된 키)
        nutrition_data = {}
        if nutrition_result:
            nutrition_mapping = {
                "kcal": "calories",
                "탄수화물": "carbs",
                "단백질": "protein",
                "지방": "fat",
                "나트륨": "sodium",
                "당류": "sugar",
                "포화지방": "saturated_fat",
                "트랜스지방": "trans_fat",
                "콜레스테롤": "cholesterol",
                "총내용량": "total_content",
                "기준내용량": "serving_size"
            }
            for korean_key, english_key in nutrition_mapping.items():
                if korean_key in nutrition_result:
                    value = nutrition_result[korean_key][0]
                    nutrition_data[english_key] = str(value)

        return {
            "status": "success",
            "product_name": final_product_name,
            "ocr_result": {
                "nutrition": nutrition_data,
                "materials": material_result if material_result else []
            },
            "raw_ocr": {
                "nutrition": {k: v[0] for k, v in nutrition_result.items()} if nutrition_result else {},
                "materials": material_result if material_result else []
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"OCR 처리 중 오류가 발생했습니다: {str(e)}",
                "product_name": product_name or "분석 실패",
                "ocr_result": {"nutrition": {}, "materials": []},
                "raw_ocr": {"nutrition": {}, "materials": []}
            }
        )


# ============================================
# API 2: RAG + LLM 분석 API
# ============================================

# 인증 함수 추가
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return credentials.credentials


# ============================================
# 내부용 RAG 분석 함수 (API 인증 불필요, DB는 자동 사용)
# ============================================

async def _internal_rag_analyze(
    product_name: str,
    ocr_result: OCRResult,
    user_data: dict
) -> dict:
    """
    내부 호출용 RAG 분석 함수
    - API 인증: 불필요 (내부 함수)
    - DB 연결: 서버 시작 시 이미 연결됨 (rag_service, gpt_service 사용)
    """
    diet_type = user_data.get("diet_type", "none")
    allergies = user_data.get("allergies", [])
    user_id = user_data.get("user_id", "anonymous")

    detected_allergens = ocr_result.materials
    nutrition_data = ocr_result.nutrition

    allergen_warnings = check_allergen_match(detected_allergens, allergies)
    diet_warnings = check_diet_warnings(detected_allergens, diet_type)

    rag_analysis = None
    
    # DB 연결은 이미 되어 있음 (rag_service, gpt_service는 전역 변수)
    if RAG_AVAILABLE and rag_service and gpt_service:
        try:
            logger.info("🔍 RAG + GPT 분석 시작 (DB 연결 활용)...")
            
            nutritional_info = NutritionalInfo(
                calories=nutrition_data.get("calories"),
                carbohydrates=nutrition_data.get("carbs"),
                protein=nutrition_data.get("protein"),
                fat=nutrition_data.get("fat"),
                sodium=nutrition_data.get("sodium"),
                sugar=nutrition_data.get("sugar"),
                cholesterol=nutrition_data.get("cholesterol"),
                saturated_fat=nutrition_data.get("saturated_fat"),
                trans_fat=nutrition_data.get("trans_fat"),
            ) if nutrition_data else None
            
            product_data = ProductData(
                product_name=product_name,
                nutritional_info=nutritional_info,
                ingredients=detected_allergens,
                allergens=detected_allergens
            )
            
            user_profile = UserProfile(
                height=user_data.get("height"),
                weight=user_data.get("weight"),
                age_range=user_data.get("age_range", "20대"),
                gender=user_data.get("gender"),
                allergies=allergies,
                diseases=user_data.get("diseases", []),
                special_conditions=user_data.get("special_conditions", [])
            )
            
            rag_request = RAGAnalysisRequest(
                user_id=user_id,
                product_data=product_data,
                user_profile=user_profile
            )
            
            # DB에서 규칙 조회 (rag_service가 DB 연결을 관리)
            rules = await rag_service.get_matching_rules(
                user_allergies=user_profile.allergies,
                user_diseases=user_profile.diseases
            )
            
            nutritional_dict = {}
            if product_data.nutritional_info:
                info = product_data.nutritional_info
                nutritional_dict = {
                    "calories": info.calories,
                    "carbohydrates": info.carbohydrates,
                    "protein": info.protein,
                    "fat": info.fat,
                    "sodium": info.sodium,
                    "sugar": info.sugar,
                    "cholesterol": info.cholesterol,
                    "saturated_fat": info.saturated_fat,
                    "trans_fat": info.trans_fat
                }
            
            rule_result = await rag_service.apply_rules(
                rules=rules,
                product_allergens=product_data.allergens or [],
                nutritional_info=nutritional_dict
            )
            
            # DB에서 컨텍스트 검색 (pgvector)
            context = await rag_service.get_context_for_analysis(
                allergies=user_profile.allergies,
                diseases=user_profile.diseases,
                product_allergens=product_data.allergens or []
            )
            
            # GPT 분석 (OpenAI API 호출)
            rag_analysis = await gpt_service.analyze(rag_request, context, rule_result)
            logger.info(f"✅ RAG 분석 완료 - suitability: {rag_analysis.suitability}, score: {rag_analysis.score}")
            
        except Exception as e:
            logger.error(f"⚠️ RAG 분석 실패: {e}")
            import traceback
            traceback.print_exc()

    # 응답 구성
    if rag_analysis:
        suitability_to_level = {"danger": "red", "warning": "yellow", "safe": "green"}
        risk_level = suitability_to_level.get(rag_analysis.suitability, "yellow")
        risk_score = rag_analysis.score
        recommendation = rag_analysis.nutritional_advice
        risk_reason = "; ".join(rag_analysis.recommendations) if rag_analysis.recommendations else "분석 완료"
        alternatives = [
            {"product_name": alt.product_name, "reason": alt.reason}
            for alt in rag_analysis.alternatives
        ] if rag_analysis.alternatives else []
    else:
        if len(allergen_warnings) > 0:
            risk_level = "red"
            risk_score = 90
            risk_reason = f"알레르기 성분 감지: {', '.join([w['detected'] for w in allergen_warnings])}"
            recommendation = f"⚠️ 주의! {', '.join(allergies)} 알레르기 성분이 포함되어 있습니다."
        elif len(diet_warnings) > 0:
            risk_level = "yellow"
            risk_score = 50
            risk_reason = f"식단 주의: {', '.join([w['reason'] for w in diet_warnings])}"
            recommendation = "식단 타입에 맞지 않는 성분이 포함되어 있습니다."
        else:
            risk_level = "green"
            risk_score = 10
            risk_reason = "알레르기 및 식단 위험 요소 없음"
            recommendation = "✅ 안전합니다."
        alternatives = []

    return {
        "status": "success",
        "product_name": product_name,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "analysis": {
            "detected_ingredients": detected_allergens,
            "allergen_warnings": allergen_warnings,
            "diet_warnings": diet_warnings,
            "nutrition": nutrition_data,
            "alternatives": alternatives
        },
        "recommendation": recommendation,
        "risk_reason": risk_reason,
        "rag_enabled": rag_analysis is not None
    }


# ============================================
# API 2: RAG + LLM 분석 API (외부용 - 인증 필요)
# ============================================

@app.post("/api/v1/rag/analyze", tags=["RAG + LLM"])
async def rag_analyze(
    request: RAGAnalysisRequestBody,
    token: str = Depends(verify_token)
):
    """
    ## 외부 호출용 RAG API (Bearer 토큰 인증 필요)
    """
    return await _internal_rag_analyze(
        product_name=request.product_name,
        ocr_result=request.ocr_result,
        user_data=request.user_info
    )


# ============================================
# 통합 API: /api/upload (Node.js 연동용)
# ============================================

@app.post("/api/upload", tags=["Upload"])
async def upload_image(
    file: UploadFile = File(...),
    user_info: str = Form(...)
):
    try:
        user_data = json.loads(user_info)
        
        # 파일명 디코딩 수정
        filename = file.filename
        if filename:
            # URL 인코딩된 파일명 디코딩
            from urllib.parse import unquote
            filename = unquote(filename)
            product_name = filename.rsplit('.', 1)[0]
        else:
            product_name = "제품명 미확인"
        
        logger.info(f"📤 업로드 요청: {product_name}")
        logger.info(f"👤 사용자 정보: {json.dumps(user_data, ensure_ascii=False, indent=2)}")
        
        # ============================================
        # 1. YOLO + OCR 실행
        # ============================================
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "product_name": "이미지 오류",
                    "risk_level": "yellow",
                    "risk_score": 50,
                    "analysis": {"detected_ingredients": [], "allergen_warnings": [], "diet_warnings": [], "nutrition": {}},
                    "recommendation": "이미지를 읽을 수 없습니다.",
                    "risk_reason": "이미지 디코딩 실패",
                    "raw_ocr": {"nutrition": {}, "materials": []}
                }
            )

        logger.info(f"📷 YOLO + OCR 처리 시작: {product_name}")
        nutrition_result, material_result = ocr_model.execute(image)
        
        # ============================================
        # OCR 결과 터미널 출력
        # ============================================
        print("\n" + "="*60)
        print("🔍 YOLO + OCR 결과")
        print("="*60)
        print(f"📦 제품명: {product_name}")
        print("-"*60)
        print("📊 영양성분 (raw):")
        if nutrition_result:
            for key, value in nutrition_result.items():
                print(f"   • {key}: {value}")
        else:
            print("   (감지된 영양성분 없음)")
        print("-"*60)
        print("🥗 원재료:")
        if material_result:
            for i, material in enumerate(material_result, 1):
                print(f"   {i}. {material}")
        else:
            print("   (감지된 원재료 없음)")
        print("="*60 + "\n")
        
        logger.info(f"✅ OCR 완료 - 영양성분: {len(nutrition_result) if nutrition_result else 0}개, 원재료: {len(material_result) if material_result else 0}개")
        
        # 영양성분 파싱
        nutrition_data = {}
        if nutrition_result:
            nutrition_mapping = {
                "kcal": "calories", "탄수화물": "carbs", "단백질": "protein",
                "지방": "fat", "나트륨": "sodium", "당류": "sugar",
                "포화지방": "saturated_fat", "트랜스지방": "trans_fat",
                "콜레스테롤": "cholesterol", "총내용량": "total_content",
                "기준내용량": "serving_size"
            }
            for korean_key, english_key in nutrition_mapping.items():
                if korean_key in nutrition_result:
                    nutrition_data[english_key] = str(nutrition_result[korean_key][0])

        detected_materials = material_result if material_result else []
        
        # ============================================
        # 2. RAG API 호출 (HTTP 요청 + Bearer 토큰 인증)
        # ============================================
        RAG_API_URL = os.getenv("RAG_API_URL", "https://d9d8d8c533d8.ngrok-free.app")
        
        # RAG API가 기대하는 형식으로 변환
        rag_request_data = {
            "userId": user_data.get("user_id", "anonymous"),
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
                "allergens": detected_materials
            },
            "userProfile": {
                "height": user_data.get("height"),
                "weight": user_data.get("weight"),
                "ageRange": user_data.get("age_range", "20대"),
                "gender": user_data.get("gender"),
                "allergies": user_data.get("allergies", []),
                "diseases": user_data.get("diseases", []),
                "specialConditions": user_data.get("special_conditions", [])
            }
        }
        
        print("\n" + "="*60)
        print("🤖 RAG API 요청")
        print("="*60)
        print(f"🌐 URL: {RAG_API_URL}/api/v1/rag/analyze")
        print(f"📨 요청 데이터:")
        print(json.dumps(rag_request_data, ensure_ascii=False, indent=2))
        print("="*60 + "\n")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info(f"🔍 RAG API 호출: {RAG_API_URL}/api/v1/rag/analyze")
                
                rag_response = await client.post(
                    f"{RAG_API_URL}/api/v1/rag/analyze",
                    json=rag_request_data,
                    headers={"Authorization": f"Bearer {API_KEY}"}
                )
                
                # ============================================
                # RAG 결과 터미널 출력
                # ============================================
                print("\n" + "="*60)
                print("🎯 RAG API 응답")
                print("="*60)
                print(f"📡 상태 코드: {rag_response.status_code}")
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    
                    # RAG 응답 키 확인 및 매핑
                    analyze_result = {
                        "status": "success",
                        "product_name": product_name,
                        "risk_level": rag_data.get("risk_level") or rag_data.get("riskLevel") or "green",
                        "risk_score": rag_data.get("risk_score") or rag_data.get("riskScore") or 0,
                        "risk_reason": rag_data.get("risk_reason") or rag_data.get("riskReason") or "",
                        "recommendation": rag_data.get("recommendation") or "",
                        "rag_enabled": rag_data.get("rag_enabled", True),
                        "analysis": rag_data.get("analysis", {
                            "detected_ingredients": detected_materials,
                            "allergen_warnings": [],
                            "diet_warnings": [],
                            "nutrition": nutrition_data,
                            "alternatives": []
                        })
                    }
                    
                    # risk_level 유효성 검사
                    if analyze_result["risk_level"] not in ["red", "yellow", "green"]:
                        analyze_result["risk_level"] = "green"
                    
                    print(f"✅ 분석 성공!")

                else:
                    print(f"❌ RAG API 오류!")
                    print(f"📄 응답 내용: {rag_response.text}")
                    print("="*60 + "\n")
                    logger.error(f"❌ RAG API 오류: {rag_response.status_code}")
                    # RAG 실패 시 규칙 기반 폴백
                    analyze_result = await _fallback_analyze(
                        product_name, nutrition_data, detected_materials, user_data
                    )
                    _print_fallback_result(analyze_result)
                    
        except Exception as e:
            print("\n" + "="*60)
            print("⚠️ RAG API 호출 실패")
            print("="*60)
            print(f"❌ 오류: {str(e)}")
            print("🔄 규칙 기반 폴백 분석 실행...")
            print("="*60 + "\n")
            
            logger.error(f"⚠️ RAG API 호출 실패: {e}")
            # RAG 실패 시 규칙 기반 폴백
            analyze_result = await _fallback_analyze(
                product_name, nutrition_data, detected_materials, user_data
            )
            _print_fallback_result(analyze_result)
        
        # raw_ocr 추가
        analyze_result["raw_ocr"] = {
            "nutrition": {k: v[0] for k, v in nutrition_result.items()} if nutrition_result else {},
            "materials": detected_materials
        }
        
        # ============================================
        # 최종 결과 요약 출력
        # ============================================
        print("\n" + "="*60)
        print("📊 최종 분석 결과 요약")
        print("="*60)
        print(f"📦 제품명: {analyze_result.get('product_name', product_name)}")
        print(f"🚦 위험도: {analyze_result.get('risk_level', 'N/A')} (점수: {analyze_result.get('risk_score', 'N/A')})")
        print(f"🤖 RAG 사용: {'예' if analyze_result.get('rag_enabled') else '아니오 (규칙 기반)'}")
        print(f"💡 권장사항: {analyze_result.get('recommendation', 'N/A')}")
        print("="*60 + "\n")
        
        # 안전하게 접근
        logger.info(f"📊 분석 완료: {product_name} → {analyze_result.get('risk_level', 'unknown')}")
        
        return analyze_result

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
                "raw_ocr": {"nutrition": {}, "materials": []}
            }
        )


def _print_fallback_result(result: dict):
    """폴백 분석 결과 출력"""
    print("\n" + "="*60)
    print("🔄 규칙 기반 폴백 분석 결과")
    print("="*60)
    print(f"🚦 위험도: {result.get('risk_level', 'N/A')}")
    print(f"📊 위험 점수: {result.get('risk_score', 'N/A')}")
    print(f"📝 위험 사유: {result.get('risk_reason', 'N/A')}")
    print(f"💡 권장사항: {result.get('recommendation', 'N/A')}")
    
    if result.get('analysis', {}).get('allergen_warnings'):
        print("-"*60)
        print("⚠️ 알레르기 경고:")
        for warning in result['analysis']['allergen_warnings']:
            print(f"   • {warning.get('message', warning)}")
    
    if result.get('analysis', {}).get('diet_warnings'):
        print("-"*60)
        print("🥗 식단 경고:")
        for warning in result['analysis']['diet_warnings']:
            print(f"   • {warning.get('reason', warning)}")
    
    print("="*60 + "\n")


async def _fallback_analyze(
    product_name: str,
    nutrition_data: dict,
    detected_materials: list,
    user_data: dict
) -> dict:
    """RAG API 실패 시 규칙 기반 폴백 분석"""
    allergies = user_data.get("allergies", [])
    diet_type = user_data.get("diet_type", "none")
    
    allergen_warnings = check_allergen_match(detected_materials, allergies)
    diet_warnings = check_diet_warnings(detected_materials, diet_type)
    
    if len(allergen_warnings) > 0:
        risk_level = "red"
        risk_score = 90
        risk_reason = f"알레르기 성분 감지: {', '.join([w['detected'] for w in allergen_warnings])}"
        recommendation = f"⚠️ 주의! {', '.join(allergies)} 알레르기 성분이 포함되어 있습니다."
    elif len(diet_warnings) > 0:
        risk_level = "yellow"
        risk_score = 50
        risk_reason = f"식단 주의: {', '.join([w['reason'] for w in diet_warnings])}"
        recommendation = "식단 타입에 맞지 않는 성분이 포함되어 있습니다."
    else:
        risk_level = "green"
        risk_score = 10
        risk_reason = "알레르기 및 식단 위험 요소 없음"
        recommendation = "✅ 안전합니다."
    
    return {
        "status": "success",
        "product_name": product_name,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "analysis": {
            "detected_ingredients": detected_materials,
            "allergen_warnings": allergen_warnings,
            "diet_warnings": diet_warnings,
            "nutrition": nutrition_data,
            "alternatives": []
        },
        "recommendation": recommendation,
        "risk_reason": risk_reason,
        "rag_enabled": False
    }


if __name__ == "__main__":
    import uvicorn
    import sys
    import io
    
    # Windows 콘솔 인코딩 설정
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
