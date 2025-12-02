from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ...models.rag_models import (
    RAGAnalysisRequest,
    RAGAnalysisResponse,
    RAGAnalysis
)
from ...services.gpt_service import gpt_service
from ...services.rag_service import rag_service
from ...config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """API 키 검증"""
    settings = get_settings()
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    if token != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return token


@router.post("/analyze", response_model=RAGAnalysisResponse)
async def analyze_product(
    request: RAGAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    RAG + LLM 기반 제품 분석 엔드포인트
    
    Node.js에서 OCR 파싱된 제품 정보와 사용자 프로필을 받아 분석합니다.
    
    **플로우**:
    1. Node.js에서 OCR 파싱된 productData 수신
    2. 사용자 프로필 기반 규칙 조회 (pgvector)
    3. 관련 지식 검색 (RAG)
    4. GPT로 맞춤형 분석 생성
    
    **요청 데이터**:
    - **user_id**: 사용자 ID
    - **product_data**: OCR로 파싱된 제품 정보 (영양정보, 원재료, 알레르기 성분)
    - **user_profile**: 사용자 건강 프로필 (알레르기, 질병, 신체 정보)
    
    **응답 데이터**:
    - **suitability**: 적합성 수준 (safe/warning/danger)
    - **score**: 적합성 점수 (0-100)
    - **recommendations**: 권장 사항 목록
    - **alternatives**: 대안 제품 추천
    - **nutritional_advice**: 영양 관련 조언
    """
    try:
        logger.info(f"RAG 분석 요청: user_id={request.user_id}")
        
        # 1. 규칙 기반 분석 (PostgreSQL에서 규칙 조회)
        rules = await rag_service.get_matching_rules(
            user_allergies=request.user_profile.allergies,
            user_diseases=request.user_profile.diseases
        )
        
        # 2. 영양 정보 딕셔너리 변환
        nutritional_dict = {}
        if request.product_data.nutritional_info:
            info = request.product_data.nutritional_info
            nutritional_dict = {
                "calories": info.calories,
                "carbohydrates": info.carbohydrates,
                "protein": info.protein,
                "fat": info.fat,
                "sodium": info.sodium,
                "sugar": info.sugar,
                "fiber": info.fiber,
                "cholesterol": info.cholesterol,
                "saturated_fat": info.saturated_fat,
                "trans_fat": info.trans_fat
            }
        
        # 3. 규칙 적용
        rule_result = await rag_service.apply_rules(
            rules=rules,
            product_allergens=request.product_data.allergens or [],
            nutritional_info=nutritional_dict
        )
        
        logger.info(f"규칙 적용 결과: {len(rule_result['warnings'])} 경고, {len(rule_result['dangers'])} 위험")
        
        # 4. RAG를 통해 관련 지식 검색
        context = await rag_service.get_context_for_analysis(
            allergies=request.user_profile.allergies,
            diseases=request.user_profile.diseases,
            product_allergens=request.product_data.allergens or []
        )
        
        logger.info(f"RAG 컨텍스트 검색 완료: {len(context)} 문자")
        
        # 5. GPT를 통한 분석 (규칙 결과 + 컨텍스트 포함)
        analysis = await gpt_service.analyze(request, context, rule_result)
        
        logger.info(f"GPT 분석 완료: suitability={analysis.suitability}, score={analysis.score}")
        
        response = RAGAnalysisResponse(
            success=True,
            analysis=analysis
        )
        # camelCase로 응답 반환
        return JSONResponse(content=response.model_dump(by_alias=True))
        
    except Exception as e:
        logger.error(f"RAG 분석 실패: {e}")
        response = RAGAnalysisResponse(
            success=False,
            error=str(e)
        )
        return JSONResponse(content=response.model_dump(by_alias=True))


@router.post("/analyze-rule-only", response_model=RAGAnalysisResponse)
async def analyze_product_rule_only(
    request: RAGAnalysisRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    규칙 기반 분석만 수행 (GPT 없이)
    
    GPT API를 사용하지 않고 PostgreSQL 규칙 기반으로 빠르게 분석합니다.
    테스트 또는 GPT 사용량 제한 시 사용할 수 있습니다.
    """
    try:
        logger.info(f"Rule-only 분석 요청: user_id={request.user_id}")
        
        # 규칙 조회 및 적용
        rules = await rag_service.get_matching_rules(
            user_allergies=request.user_profile.allergies,
            user_diseases=request.user_profile.diseases
        )
        
        nutritional_dict = {}
        if request.product_data.nutritional_info:
            info = request.product_data.nutritional_info
            nutritional_dict = {
                "calories": info.calories,
                "sodium": info.sodium,
                "sugar": info.sugar,
                "saturated_fat": info.saturated_fat
            }
        
        rule_result = await rag_service.apply_rules(
            rules=rules,
            product_allergens=request.product_data.allergens or [],
            nutritional_info=nutritional_dict
        )
        
        # GPT 서비스의 fallback 분석 사용
        analysis = gpt_service._get_fallback_analysis(request, rule_result)
        
        response = RAGAnalysisResponse(
            success=True,
            analysis=analysis
        )
        return JSONResponse(content=response.model_dump(by_alias=True))
        
    except Exception as e:
        logger.error(f"Rule-only 분석 실패: {e}")
        response = RAGAnalysisResponse(
            success=False,
            error=str(e)
        )
        return JSONResponse(content=response.model_dump(by_alias=True))


@router.get("/health")
async def health_check():
    """RAG 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "RAG + LLM Analysis",
        "version": "1.0.0",
        "database": "PostgreSQL + pgvector"
    }
