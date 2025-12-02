from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException
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
import httpx

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
    
    이미지에서 영양성분/원재료를 추출하고, 사용자 프로필 기반으로 위험도를 분석합니다.
    
    ### 아키텍처
    ```
    Front → Node.js → FastAPI(OCR + RAG + LLM) → Node.js → Front
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

def check_allergen_match(detected_allergens: List[str], user_allergies: List[str]) -> List[dict]:
    """
    감지된 알레르기 성분과 사용자 알레르기를 매칭
    """
    warnings = []
    
    for user_allergy in user_allergies:
        user_allergy_lower = user_allergy.lower()
        
        # 매핑에서 관련 키워드 찾기
        related_keywords = []
        for key, keywords in ALLERGEN_MAPPING.items():
            if user_allergy_lower in [k.lower() for k in keywords] or user_allergy == key:
                related_keywords = keywords
                break
        
        if not related_keywords:
            related_keywords = [user_allergy]
        
        # 감지된 알레르기에서 매칭 확인
        for detected in detected_allergens:
            detected_lower = detected.lower()
            for keyword in related_keywords:
                if keyword.lower() in detected_lower or detected_lower in keyword.lower():
                    warnings.append({
                        "allergen": user_allergy,
                        "detected": detected,
                        "severity": "high",
                        "message": f"⚠️ {user_allergy} 알레르기 주의: {detected} 성분이 포함되어 있습니다."
                    })
                    break
    
    return warnings


def check_diet_warnings(detected_ingredients: List[str], diet_type: str) -> List[dict]:
    """
    식단 타입에 따른 경고 생성
    """
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
        "ocr_model": "YOLO + EasyOCR",
        "rag_service": rag_service is not None,
        "gpt_service": gpt_service is not None
    }


def convert_ocr_to_product_data(
    nutrition_result: dict,
    material_result: list,
    product_name: str
) -> ProductData:
    """
    OCR 결과를 RAG의 ProductData 모델로 변환
    """
    # 영양성분 변환
    nutritional_info = None
    if nutrition_result:
        nutritional_info = NutritionalInfo(
            calories=nutrition_result.get("kcal", [None])[0] if "kcal" in nutrition_result else None,
            carbohydrates=nutrition_result.get("탄수화물", [None])[0] if "탄수화물" in nutrition_result else None,
            protein=nutrition_result.get("단백질", [None])[0] if "단백질" in nutrition_result else None,
            fat=nutrition_result.get("지방", [None])[0] if "지방" in nutrition_result else None,
            sodium=nutrition_result.get("나트륨", [None])[0] if "나트륨" in nutrition_result else None,
            sugar=nutrition_result.get("당류", [None])[0] if "당류" in nutrition_result else None,
            cholesterol=nutrition_result.get("콜레스테롤", [None])[0] if "콜레스테롤" in nutrition_result else None,
            saturated_fat=nutrition_result.get("포화지방", [None])[0] if "포화지방" in nutrition_result else None,
            trans_fat=nutrition_result.get("트랜스지방", [None])[0] if "트랜스지방" in nutrition_result else None,
        )
    
    return ProductData(
        product_name=product_name,
        nutritional_info=nutritional_info,
        ingredients=material_result if material_result else [],
        allergens=material_result if material_result else []  # 원재료에서 추출된 알레르기 성분
    )


def convert_user_info_to_profile(user_data: dict) -> UserProfile:
    """
    Node.js에서 받은 user_info를 RAG의 UserProfile 모델로 변환
    """
    return UserProfile(
        height=user_data.get("height"),
        weight=user_data.get("weight"),
        age_range=user_data.get("age_range", "20대"),
        gender=user_data.get("gender"),
        allergies=user_data.get("allergies", []),
        diseases=user_data.get("diseases", []),
        special_conditions=user_data.get("special_conditions", [])
    )


@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_info: str = Form(...)
):
    """
    이미지를 받아 YOLO + EasyOCR로 텍스트를 추출하고
    RAG + GPT로 사용자 맞춤 위험도 분석
    
    **파이프라인**:
    1. YOLO로 영양성분표/원재료 영역 감지
    2. EasyOCR로 텍스트 추출
    3. RAG로 관련 규칙/지식 검색
    4. GPT로 개인화된 분석 결과 생성
    """
    try:
        # user_info JSON 파싱
        user_data = json.loads(user_info)
        diet_type = user_data.get("diet_type", "none")
        allergies = user_data.get("allergies", [])
        user_id = user_data.get("user_id", "anonymous")

        # 이미지 읽기 및 OpenCV 형식으로 변환
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {
                "status": "error",
                "product_name": "이미지 오류",
                "risk_level": "yellow",
                "risk_score": 50,
                "analysis": {
                    "detected_ingredients": [],
                    "allergen_warnings": [],
                    "diet_warnings": [],
                    "nutrition": {}
                },
                "recommendation": "이미지를 읽을 수 없습니다. 다른 이미지를 시도해주세요.",
                "risk_reason": "이미지 디코딩 실패"
            }

        # ============================================
        # 1단계: YOLO + EasyOCR로 텍스트 추출
        # ============================================
        logger.info("📷 OCR 처리 시작...")
        nutrition_result, material_result = ocr_model.execute(image)
        logger.info(f"✅ OCR 완료 - 영양성분: {len(nutrition_result) if nutrition_result else 0}개, 원재료: {len(material_result) if material_result else 0}개")

        # 제품명 추출 (파일명에서)
        product_name = file.filename.rsplit('.', 1)[0] if file.filename else "제품명 미확인"

        # 영양성분 파싱 (Node.js 응답용)
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

        # 감지된 알레르기 성분
        detected_allergens = material_result if material_result else []

        # 기본 알레르기/식단 경고 (OCR 기반)
        allergen_warnings = check_allergen_match(detected_allergens, allergies)
        diet_warnings = check_diet_warnings(detected_allergens, diet_type)

        # ============================================
        # 2단계: RAG + GPT 분석 (서비스가 초기화된 경우)
        # ============================================
        rag_analysis = None
        
        if RAG_AVAILABLE and rag_service and gpt_service:
            try:
                logger.info("🔍 RAG + GPT 분석 시작...")
                
                # OCR 결과를 RAG 모델로 변환
                product_data = convert_ocr_to_product_data(
                    nutrition_result, 
                    material_result, 
                    product_name
                )
                user_profile = convert_user_info_to_profile(user_data)
                
                # RAG 요청 생성
                rag_request = RAGAnalysisRequest(
                    user_id=user_id,
                    product_data=product_data,
                    user_profile=user_profile
                )
                
                # 1. 규칙 기반 분석
                rules = await rag_service.get_matching_rules(
                    user_allergies=user_profile.allergies,
                    user_diseases=user_profile.diseases
                )
                
                # 2. 영양 정보 딕셔너리 변환
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
                
                # 3. 규칙 적용
                rule_result = await rag_service.apply_rules(
                    rules=rules,
                    product_allergens=product_data.allergens or [],
                    nutritional_info=nutritional_dict
                )
                
                # 4. RAG 컨텍스트 검색
                context = await rag_service.get_context_for_analysis(
                    allergies=user_profile.allergies,
                    diseases=user_profile.diseases,
                    product_allergens=product_data.allergens or []
                )
                
                # 5. GPT 분석
                rag_analysis = await gpt_service.analyze(rag_request, context, rule_result)
                
                logger.info(f"✅ RAG 분석 완료 - suitability: {rag_analysis.suitability}, score: {rag_analysis.score}")
                
            except Exception as e:
                logger.error(f"⚠️ RAG 분석 실패 (OCR 결과만 반환): {e}")
                import traceback
                traceback.print_exc()

        # ============================================
        # 3단계: 최종 응답 구성
        # ============================================
        
        # RAG 분석 결과가 있으면 사용, 없으면 OCR 기반 결과 사용
        if rag_analysis:
            # RAG 결과 기반 위험도
            suitability_to_level = {
                "danger": "red",
                "warning": "yellow", 
                "safe": "green"
            }
            risk_level = suitability_to_level.get(rag_analysis.suitability, "yellow")
            risk_score = rag_analysis.score
            recommendation = rag_analysis.nutritional_advice
            risk_reason = "; ".join(rag_analysis.recommendations) if rag_analysis.recommendations else "분석 완료"
            
            # 대안 제품
            alternatives = [
                {"product_name": alt.product_name, "reason": alt.reason}
                for alt in rag_analysis.alternatives
            ] if rag_analysis.alternatives else []
        else:
            # OCR 기반 위험도 (기존 로직)
            if len(allergen_warnings) > 0:
                risk_level = "red"
                risk_score = 90
                risk_reason = f"알레르기 성분 감지: {', '.join([w['detected'] for w in allergen_warnings])}"
            elif len(diet_warnings) > 0:
                risk_level = "yellow"
                risk_score = 50
                risk_reason = f"식단 주의: {', '.join([w['reason'] for w in diet_warnings])}"
            else:
                risk_level = "green"
                risk_score = 10
                risk_reason = "알레르기 및 식단 위험 요소 없음"
            
            if risk_level == "red":
                recommendation = f"⚠️ 주의! {', '.join(allergies)} 알레르기 성분이 포함되어 있습니다. 섭취를 피해주세요."
            elif risk_level == "yellow":
                recommendation = "식단 타입에 맞지 않는 성분이 포함되어 있습니다. 섭취 전 확인이 필요합니다."
            else:
                recommendation = "✅ 안전합니다. 알레르기 및 식단 위험 요소가 감지되지 않았습니다."
            
            alternatives = []

        # 최종 응답
        result = {
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
            "rag_enabled": rag_analysis is not None,
            "raw_ocr": {
                "nutrition": {k: v[0] for k, v in nutrition_result.items()} if nutrition_result else {},
                "materials": material_result
            }
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
            "recommendation": f"사용자 정보 파싱 오류: {str(e)}",
            "risk_reason": f"JSON 파싱 오류: {str(e)}"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
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
            "recommendation": f"OCR 처리 중 오류가 발생했습니다: {str(e)}",
            "risk_reason": f"처리 오류: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
