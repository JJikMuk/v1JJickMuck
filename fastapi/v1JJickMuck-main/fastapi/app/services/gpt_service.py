from openai import OpenAI
from typing import Optional, Dict, Any, List
import logging
import json

from ..config.settings import get_settings
from ..models.rag_models import (
    RAGAnalysisRequest,
    RAGAnalysis,
    AlternativeProduct
)
from .rag_service import calculate_bmi, get_personalized_recommendations

logger = logging.getLogger(__name__)


class GPTService:
    """OpenAI GPT API를 사용한 분석 서비스"""
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    def _build_system_prompt(self, personalization: Dict[str, Any] = None) -> str:
        """시스템 프롬프트 생성"""
        base_prompt = """당신은 식품 영양 분석 전문가입니다. 
사용자의 건강 프로필(알레르기, 질병, 신체 정보)과 식품의 영양 정보를 분석하여 
해당 식품이 사용자에게 적합한지 평가합니다.

분석 결과는 반드시 다음 JSON 형식으로만 응답하세요:
{
    "suitability": "safe" | "warning" | "danger",
    "score": 0-100 사이의 정수,
    "recommendations": ["권장사항1", "권장사항2", ...],
    "alternatives": [{"product_name": "대안제품명", "reason": "추천이유"}, ...],
    "nutritional_advice": "영양 관련 종합 조언"
}

평가 기준:
- "danger": 알레르기 유발 성분 포함, 질병에 치명적인 성분 (점수 0-30)
- "warning": 주의가 필요한 성분 포함, 과다 섭취 주의 (점수 31-70)
- "safe": 안전하게 섭취 가능 (점수 71-100)"""

        # 개인화 정보 추가
        if personalization:
            base_prompt += f"""

## 개인화된 영양 권장 기준
- 1일 권장 칼로리: {personalization.get('daily_calories', 2000)}kcal
"""
            adjustments = personalization.get('nutrient_adjustments', {})
            if adjustments:
                base_prompt += "- 영양소 조절 권장사항:\n"
                for nutrient, adjustment in adjustments.items():
                    base_prompt += f"  • {nutrient}: {adjustment}\n"
            
            warnings = personalization.get('warnings', [])
            if warnings:
                base_prompt += "- 특별 주의사항:\n"
                for warning in warnings:
                    base_prompt += f"  • {warning}\n"
            
            base_prompt += "\n위 개인화된 기준을 반영하여 평가해주세요."
        
        base_prompt += "\n\n반드시 JSON 형식으로만 응답하고, 다른 텍스트는 포함하지 마세요."
        
        return base_prompt

    def _build_user_prompt(
        self, 
        request: RAGAnalysisRequest, 
        context: str = "",
        rule_result: Dict[str, Any] = None,
        personalization: Dict[str, Any] = None
    ) -> str:
        """사용자 프롬프트 생성"""
        profile = request.user_profile
        product = request.product_data
        
        # BMI 계산
        bmi = calculate_bmi(profile.weight, profile.height)
        bmi_status = "저체중" if bmi < 18.5 else "정상" if bmi < 25 else "과체중" if bmi < 30 else "비만"
        
        prompt = f"""## 사용자 건강 프로필
- 키: {profile.height}cm
- 체중: {profile.weight}kg
- BMI: {bmi:.1f} ({bmi_status})
- 성별: {profile.gender if hasattr(profile, 'gender') and profile.gender else '미지정'}
- 연령대: {profile.age_range}
- 알레르기: {', '.join(profile.allergies) if profile.allergies else '없음'}
- 질병/건강상태: {', '.join(profile.diseases) if profile.diseases else '없음'}
- 특수상태: {profile.special_conditions if hasattr(profile, 'special_conditions') and profile.special_conditions else '없음'}
"""

        # 개인화된 1일 권장량 추가
        if personalization:
            prompt += f"""
## 개인화된 1일 권장량
- 권장 칼로리: {personalization.get('daily_calories', 2000)}kcal
"""
        
        prompt += f"""
## 제품 정보
- 제품명: {product.product_name or '알 수 없음'}
- 원재료: {', '.join(product.ingredients) if product.ingredients else '정보 없음'}
- 알레르기 유발 성분: {', '.join(product.allergens) if product.allergens else '정보 없음'}
"""
        
        if product.nutritional_info:
            info = product.nutritional_info
            prompt += f"""
## 영양 정보
- 열량: {info.calories}kcal
- 탄수화물: {info.carbohydrates}g
- 단백질: {info.protein}g
- 지방: {info.fat}g
- 나트륨: {info.sodium}mg
- 당류: {info.sugar}g
"""
        
        # 규칙 기반 분석 결과 포함
        if rule_result:
            if rule_result.get("dangers"):
                prompt += "\n## ⚠️ 위험 감지 (규칙 기반)\n"
                for danger in rule_result["dangers"]:
                    prompt += f"- {danger['allergen']}: {danger['message']}\n"
            
            if rule_result.get("warnings"):
                prompt += "\n## 주의 사항 (규칙 기반)\n"
                for warning in rule_result["warnings"]:
                    prompt += f"- {warning}\n"
        
        if context:
            prompt += f"\n## 참고 지식 (RAG 검색 결과)\n{context}\n"
        
        prompt += "\n위 정보를 바탕으로 이 제품이 사용자에게 적합한지 분석해주세요."
        
        return prompt

    async def analyze(
        self, 
        request: RAGAnalysisRequest,
        context: str = "",
        rule_result: Dict[str, Any] = None
    ) -> RAGAnalysis:
        """
        GPT를 사용한 제품 분석
        
        Args:
            request: RAG 분석 요청
            context: RAG에서 검색된 관련 지식
            rule_result: 규칙 기반 분석 결과
            
        Returns:
            RAGAnalysis: 분석 결과
        """
        try:
            # 개인화 정보 계산
            profile = request.user_profile
            user_profile_dict = {
                "height": profile.height,
                "weight": profile.weight,
                "age_range": profile.age_range,
                "gender": getattr(profile, 'gender', None),
                "diseases": profile.diseases,
                "allergies": profile.allergies,
                "special_conditions": getattr(profile, 'special_conditions', None)
            }
            personalization = get_personalized_recommendations(user_profile_dict)
            
            system_prompt = self._build_system_prompt(personalization)
            user_prompt = self._build_user_prompt(request, context, rule_result, personalization)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            # 결과 파싱
            alternatives = [
                AlternativeProduct(
                    product_name=alt.get("product_name", ""),
                    reason=alt.get("reason", "")
                )
                for alt in result_json.get("alternatives", [])
            ]
            
            return RAGAnalysis(
                suitability=result_json.get("suitability", "warning"),
                score=int(result_json.get("score", 50)),
                recommendations=result_json.get("recommendations", []),
                alternatives=alternatives,
                nutritional_advice=result_json.get("nutritional_advice", "")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"GPT 응답 JSON 파싱 실패: {e}")
            return self._get_fallback_analysis(request, rule_result)
        except Exception as e:
            logger.error(f"GPT API 호출 실패: {e}")
            return self._get_fallback_analysis(request, rule_result)
    
    def _get_fallback_analysis(
        self, 
        request: RAGAnalysisRequest,
        rule_result: Dict[str, Any] = None
    ) -> RAGAnalysis:
        """
        GPT 호출 실패 시 규칙 기반 분석 수행
        """
        product = request.product_data
        profile = request.user_profile
        
        recommendations = []
        score = 80
        
        # 규칙 결과가 있으면 적용
        if rule_result:
            # 위험 요소
            if rule_result.get("dangers"):
                for danger in rule_result["dangers"]:
                    recommendations.append(f"⚠️ {danger['message']}")
                return RAGAnalysis(
                    suitability="danger",
                    score=10,
                    recommendations=recommendations,
                    alternatives=[],
                    nutritional_advice="알레르기 반응을 일으킬 수 있는 성분이 포함되어 있습니다."
                )
            
            # 경고 요소
            if rule_result.get("warnings"):
                recommendations.extend(rule_result["warnings"])
                score += rule_result.get("total_score_impact", 0)
        
        # 추가 알레르기 체크
        product_allergens = set(a.lower() for a in (product.allergens or []))
        user_allergies = set(a.lower() for a in profile.allergies)
        allergen_match = product_allergens & user_allergies
        
        if allergen_match:
            return RAGAnalysis(
                suitability="danger",
                score=10,
                recommendations=[
                    f"⚠️ 알레르기 유발 성분 감지: {', '.join(allergen_match)}",
                    "이 제품은 섭취하지 않는 것이 좋습니다."
                ],
                alternatives=[],
                nutritional_advice="알레르기 반응을 일으킬 수 있는 성분이 포함되어 있습니다."
            )
        
        # 영양 정보 기반 체크
        if product.nutritional_info:
            info = product.nutritional_info
            diseases_lower = [d.lower() for d in profile.diseases]
            
            if "당뇨" in profile.diseases or "diabetes" in diseases_lower:
                if info.sugar and info.sugar > 10:
                    recommendations.append("당류 함량이 높아 당뇨 환자는 주의가 필요합니다.")
                    score -= 20
            
            if "고혈압" in profile.diseases or "hypertension" in diseases_lower:
                if info.sodium and info.sodium > 500:
                    recommendations.append("나트륨 함량이 높아 고혈압 환자는 주의가 필요합니다.")
                    score -= 15
            
            if "고지혈증" in profile.diseases:
                if info.saturated_fat and info.saturated_fat > 3:
                    recommendations.append("포화지방 함량이 높아 고지혈증 환자는 주의가 필요합니다.")
                    score -= 15
        
        if not recommendations:
            recommendations.append("분석 가능한 위험 요소가 발견되지 않았습니다.")
        
        score = max(0, min(100, score))
        suitability = "safe" if score >= 70 else "warning" if score >= 40 else "danger"
        
        return RAGAnalysis(
            suitability=suitability,
            score=score,
            recommendations=recommendations,
            alternatives=[],
            nutritional_advice="균형 잡힌 식단을 유지하시기 바랍니다."
        )


# 싱글톤 인스턴스
gpt_service = GPTService()
