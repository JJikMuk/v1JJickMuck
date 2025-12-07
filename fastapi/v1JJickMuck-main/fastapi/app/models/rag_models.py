from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any


class NutritionalInfo(BaseModel):
    """영양 정보 모델 (OCR에서 파싱된 데이터)"""
    calories: Optional[float] = Field(None, description="열량 (kcal)")
    carbohydrates: Optional[float] = Field(None, description="탄수화물 (g)")
    protein: Optional[float] = Field(None, description="단백질 (g)")
    fat: Optional[float] = Field(None, description="지방 (g)")
    sodium: Optional[float] = Field(None, description="나트륨 (mg)")
    sugar: Optional[float] = Field(None, description="당류 (g)")
    fiber: Optional[float] = Field(None, description="식이섬유 (g)")
    cholesterol: Optional[float] = Field(None, description="콜레스테롤 (mg)")
    saturated_fat: Optional[float] = Field(None, alias="saturatedFat", description="포화지방 (g)")
    trans_fat: Optional[float] = Field(None, alias="transFat", description="트랜스지방 (g)")

    class Config:
        populate_by_name = True


class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    height: Optional[float] = Field(None, description="키 (cm)")
    weight: Optional[float] = Field(None, description="체중 (kg)")
    age_range: Optional[str] = Field(None, alias="ageRange", description="연령대 (예: 20대, 30대)")
    gender: Optional[Literal["male", "female", "other"]] = Field(None, description="성별 (male/female/other)")
    allergies: List[str] = Field(default_factory=list, description="알레르기 목록")
    diseases: List[str] = Field(default_factory=list, description="질병/건강상태 목록")
    special_conditions: Optional[List[str]] = Field(
        default_factory=list, 
        alias="specialConditions",
        description="특수 상태 (임신, 수유중, 채식주의자 등)"
    )

    class Config:
        populate_by_name = True


class ProductData(BaseModel):
    """제품 데이터 모델 (OCR 파싱 결과)"""
    product_name: Optional[str] = Field(None, alias="productName", description="제품명")
    nutritional_info: Optional[NutritionalInfo] = Field(None, alias="nutritionalInfo", description="영양 정보")
    ingredients: Optional[List[str]] = Field(None, description="원재료 목록")
    allergens: Optional[List[str]] = Field(None, description="알레르기 유발 성분")

    class Config:
        populate_by_name = True


class AlternativeProduct(BaseModel):
    """대안 제품 모델"""
    product_name: str = Field(..., alias="productName", description="대안 제품명")
    reason: str = Field(..., description="추천 이유")

    class Config:
        populate_by_name = True


class RAGAnalysis(BaseModel):
    """RAG 분석 결과 모델"""
    suitability: Literal["safe", "warning", "danger"] = Field(..., description="적합성 수준")
    score: int = Field(..., ge=0, le=100, description="적합성 점수 (0-100)")
    recommendations: List[str] = Field(default_factory=list, description="권장 사항 목록")
    alternatives: List[AlternativeProduct] = Field(default_factory=list, description="대안 제품 목록")
    nutritional_advice: str = Field("", alias="nutritionalAdvice", description="영양 관련 조언")

    class Config:
        populate_by_name = True


class RAGAnalysisRequest(BaseModel):
    """RAG 분석 요청 모델 - Node.js에서 전달받는 형식"""
    user_id: str = Field(..., alias="userId", description="사용자 ID")
    product_data: ProductData = Field(..., alias="productData", description="제품 데이터 (OCR 파싱 결과)")
    user_profile: UserProfile = Field(..., alias="userProfile", description="사용자 프로필")

    class Config:
        populate_by_name = True


class RAGAnalysisResponse(BaseModel):
    """RAG 분석 응답 모델 - Node.js가 기대하는 형식"""
    success: bool = Field(..., description="처리 성공 여부")
    analysis: Optional[RAGAnalysis] = Field(None, description="분석 결과")
    error: Optional[str] = Field(None, description="에러 메시지")

    class Config:
        populate_by_name = True
        by_alias = True  # 응답 시 camelCase로 반환
