import logging
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import OpenAIEmbeddings

from ..config.settings import get_settings
from ..database.models import KnowledgeDocument, AnalysisRule, async_session_maker

logger = logging.getLogger(__name__)
settings = get_settings()

# 개인화 규칙 로드
PERSONALIZATION_RULES_PATH = Path(__file__).parent.parent.parent / "scripts" / "data" / "personalization_rules.json"


def load_personalization_rules() -> Dict[str, Any]:
    """개인화 규칙 JSON 로드"""
    try:
        if PERSONALIZATION_RULES_PATH.exists():
            with open(PERSONALIZATION_RULES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f).get("personalization_rules", {})
    except Exception as e:
        logger.error(f"개인화 규칙 로드 실패: {e}")
    return {}


class RAGService:
    """PostgreSQL + pgvector 기반 RAG 서비스"""
    
    def __init__(self):
        # OpenAI 임베딩 초기화
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        # 개인화 규칙 로드
        self.personalization_rules = load_personalization_rules()
    
    def calculate_bmi(self, weight: float, height: float) -> Dict[str, Any]:
        """
        BMI 계산 및 카테고리 분류
        
        Args:
            weight: 체중 (kg)
            height: 신장 (cm)
            
        Returns:
            BMI 정보 및 카테고리
        """
        if not weight or not height or height <= 0:
            return {"bmi": None, "category": None, "label": "정보 없음"}
        
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        bmi = round(bmi, 1)
        
        bmi_categories = self.personalization_rules.get("bmi_categories", {})
        
        for category_key, category_info in bmi_categories.items():
            range_min, range_max = category_info.get("range", [0, 100])
            if range_min <= bmi < range_max:
                return {
                    "bmi": bmi,
                    "category": category_key,
                    "label": category_info.get("label", ""),
                    "calorie_adjustment": category_info.get("calorie_adjustment", 1.0),
                    "advice": category_info.get("advice", ""),
                    "score_bonus": category_info.get("score_bonus", 0),
                    "nutrient_limits": category_info.get("nutrient_limits", {})
                }
        
        return {"bmi": bmi, "category": "normal", "label": "정상"}
    
    def get_age_group_rules(self, age_range: str) -> Dict[str, Any]:
        """
        나이대별 규칙 조회
        
        Args:
            age_range: 나이대 (예: "20대", "30대")
            
        Returns:
            해당 나이대 규칙
        """
        age_groups = self.personalization_rules.get("age_groups", {})
        return age_groups.get(age_range, age_groups.get("20대", {}))
    
    def get_gender_rules(self, gender: str) -> Dict[str, Any]:
        """
        성별 규칙 조회
        
        Args:
            gender: 성별 ("male" 또는 "female")
            
        Returns:
            성별 규칙
        """
        gender_adjustments = self.personalization_rules.get("gender_adjustments", {})
        return gender_adjustments.get(gender, gender_adjustments.get("male", {}))
    
    def get_special_condition_rules(self, conditions: List[str]) -> List[Dict[str, Any]]:
        """
        특이사항 규칙 조회
        
        Args:
            conditions: 특이사항 목록 (예: ["임산부", "다이어트중"])
            
        Returns:
            해당 특이사항 규칙 목록
        """
        special_conditions = self.personalization_rules.get("special_conditions", {})
        result = []
        
        for condition in conditions:
            if condition in special_conditions:
                result.append({
                    "condition": condition,
                    **special_conditions[condition]
                })
        
        return result
    
    def calculate_personalized_limits(
        self,
        weight: float,
        height: float,
        age_range: str,
        gender: str,
        special_conditions: List[str] = None
    ) -> Dict[str, Any]:
        """
        개인화된 영양소 제한 계산
        
        Args:
            weight: 체중 (kg)
            height: 신장 (cm)
            age_range: 나이대
            gender: 성별
            special_conditions: 특이사항 목록
            
        Returns:
            개인화된 영양소 제한 및 권장량
        """
        result = {
            "daily_calories": 2000,
            "nutrient_limits": {},
            "adjustments": [],
            "warnings": [],
            "score_modifier": 0
        }
        
        # 1. BMI 기반 조정
        bmi_info = self.calculate_bmi(weight, height)
        if bmi_info.get("bmi"):
            result["bmi"] = bmi_info
            result["score_modifier"] += bmi_info.get("score_bonus", 0)
            
            if bmi_info.get("advice"):
                result["adjustments"].append(f"[체중] {bmi_info['advice']}")
            
            # BMI 기반 영양소 제한 적용
            bmi_limits = bmi_info.get("nutrient_limits", {})
            for nutrient, limit_info in bmi_limits.items():
                result["nutrient_limits"][nutrient] = limit_info
        
        # 2. 나이대 기반 조정
        age_rules = self.get_age_group_rules(age_range)
        if age_rules:
            gender_key = "male" if gender in ["male", "남성", "남"] else "female"
            daily_cal = age_rules.get("daily_calories", {}).get(gender_key, 2000)
            result["daily_calories"] = daily_cal
            
            # 나이대 경고 추가
            for warning in age_rules.get("warnings", []):
                result["warnings"].append(f"[{age_range}] {warning}")
            
            # 나이대별 영양소 조정
            for nutrient, adj in age_rules.get("nutrient_adjustments", {}).items():
                result["adjustments"].append(
                    f"[{age_range}] {nutrient}: {adj.get('reason', '')}"
                )
        
        # 3. 성별 기반 조정
        gender_rules = self.get_gender_rules(gender)
        if gender_rules:
            base_cal = gender_rules.get("base_calories", 2000)
            # 나이대 칼로리가 없으면 성별 기본값 사용
            if not age_rules:
                result["daily_calories"] = base_cal
        
        # 4. 특이사항 기반 조정
        if special_conditions:
            special_rules = self.get_special_condition_rules(special_conditions)
            for rule in special_rules:
                condition_name = rule.get("condition", "")
                
                # 점수 조정
                result["score_modifier"] += rule.get("score_impact", 0)
                
                # 금지 식품
                for forbidden in rule.get("forbidden", []):
                    result["warnings"].append(f"[{condition_name}] {forbidden} 섭취 금지")
                
                # 경고
                for warning in rule.get("warnings", []):
                    result["warnings"].append(f"[{condition_name}] {warning}")
                
                # 영양소 조정
                for nutrient, adj in rule.get("nutrient_adjustments", {}).items():
                    if "add" in adj:
                        result["daily_calories"] += adj["add"]
                        result["adjustments"].append(
                            f"[{condition_name}] 열량 +{adj['add']}kcal: {adj.get('reason', '')}"
                        )
        
        return result
    
    async def _get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성"""
        try:
            return await self.embeddings.aembed_query(text)
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return []
    
    async def search_knowledge(
        self,
        query: str,
        k: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        지식 베이스에서 유사 문서 검색 (pgvector 코사인 유사도)
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            category: 카테고리 필터 (allergies, diseases, nutrition)
            
        Returns:
            검색된 문서 리스트
        """
        try:
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                return []
            
            async with async_session_maker() as session:
                # pgvector 코사인 거리 검색
                if category:
                    sql = text("""
                        SELECT id, content, category, title, keywords,
                               1 - (embedding <=> :embedding::vector) as similarity
                        FROM knowledge_documents
                        WHERE category = :category
                        ORDER BY embedding <=> :embedding::vector
                        LIMIT :k
                    """)
                    result = await session.execute(
                        sql,
                        {"embedding": str(query_embedding), "category": category, "k": k}
                    )
                else:
                    sql = text("""
                        SELECT id, content, category, title, keywords,
                               1 - (embedding <=> :embedding::vector) as similarity
                        FROM knowledge_documents
                        ORDER BY embedding <=> :embedding::vector
                        LIMIT :k
                    """)
                    result = await session.execute(
                        sql,
                        {"embedding": str(query_embedding), "k": k}
                    )
                
                rows = result.fetchall()
                return [
                    {
                        "id": row.id,
                        "content": row.content,
                        "category": row.category,
                        "title": row.title,
                        "similarity": float(row.similarity) if row.similarity else 0
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"지식 검색 실패: {e}")
            return []
    
    async def get_matching_rules(
        self,
        user_allergies: List[str],
        user_diseases: List[str]
    ) -> List[Dict[str, Any]]:
        """
        사용자 조건에 맞는 규칙 조회
        
        Args:
            user_allergies: 사용자 알레르기 목록
            user_diseases: 사용자 질병 목록
            
        Returns:
            매칭되는 규칙 리스트
        """
        try:
            async with async_session_maker() as session:
                conditions = []
                
                # 알레르기 규칙 조회
                for allergy in user_allergies:
                    conditions.append(allergy.lower())
                
                # 질병 규칙 조회
                for disease in user_diseases:
                    conditions.append(disease.lower())
                
                if not conditions:
                    return []
                
                # 매칭되는 규칙 조회
                sql = text("""
                    SELECT id, rule_type, condition_key, nutrient_limits,
                           warning_message, severity, score_impact, description
                    FROM analysis_rules
                    WHERE LOWER(condition_key) = ANY(:conditions)
                """)
                
                result = await session.execute(sql, {"conditions": conditions})
                rows = result.fetchall()
                
                return [
                    {
                        "id": row.id,
                        "rule_type": row.rule_type,
                        "condition_key": row.condition_key,
                        "nutrient_limits": json.loads(row.nutrient_limits) if row.nutrient_limits else {},
                        "warning_message": row.warning_message,
                        "severity": row.severity,
                        "score_impact": row.score_impact,
                        "description": row.description
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"규칙 조회 실패: {e}")
            return []
    
    async def apply_rules(
        self,
        rules: List[Dict[str, Any]],
        product_allergens: List[str],
        nutritional_info: Dict[str, Any],
        personalized_limits: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        규칙 기반 분석 적용 (개인화 포함)
        
        Args:
            rules: 적용할 규칙 목록
            product_allergens: 제품 알레르기 성분
            nutritional_info: 제품 영양 정보
            personalized_limits: 개인화된 영양소 제한
            
        Returns:
            규칙 적용 결과 (점수 조정, 경고 메시지 등)
        """
        result = {
            "score_adjustments": [],
            "warnings": [],
            "dangers": [],
            "personalized_warnings": [],
            "total_score_impact": 0
        }
        
        # 개인화 정보 적용
        if personalized_limits:
            result["bmi_info"] = personalized_limits.get("bmi")
            result["daily_calories"] = personalized_limits.get("daily_calories", 2000)
            result["personalized_warnings"] = personalized_limits.get("warnings", [])
            result["total_score_impact"] += personalized_limits.get("score_modifier", 0)
        
        product_allergens_lower = [a.lower() for a in product_allergens]
        
        for rule in rules:
            rule_type = rule["rule_type"]
            condition_key = rule["condition_key"].lower()
            
            # 알레르기 규칙 체크
            if rule_type == "allergy":
                # 제품에 해당 알레르기 성분이 있는지 확인
                if any(condition_key in allergen or allergen in condition_key 
                       for allergen in product_allergens_lower):
                    if rule["severity"] == "danger":
                        result["dangers"].append({
                            "allergen": condition_key,
                            "message": rule["warning_message"]
                        })
                    else:
                        result["warnings"].append(rule["warning_message"])
                    result["total_score_impact"] += rule["score_impact"]
            
            # 질병 규칙 체크 (영양소 제한)
            elif rule_type == "disease" and rule["nutrient_limits"]:
                limits = rule["nutrient_limits"]
                
                # 개인화된 제한이 있으면 조정
                personalized_nutrient_limits = {}
                if personalized_limits:
                    personalized_nutrient_limits = personalized_limits.get("nutrient_limits", {})
                
                for nutrient, limit_info in limits.items():
                    nutrient_value = nutritional_info.get(nutrient)
                    if nutrient_value is not None:
                        max_limit = limit_info.get("max")
                        
                        # 개인화 조정 적용
                        if nutrient in personalized_nutrient_limits:
                            multiplier = personalized_nutrient_limits[nutrient].get("max_multiplier", 1.0)
                            max_limit = max_limit * multiplier if max_limit else None
                        
                        if max_limit and nutrient_value > max_limit:
                            result["warnings"].append(
                                f"{rule['warning_message']} (현재: {nutrient_value}, 개인 권장 최대: {max_limit:.0f})"
                            )
                            result["total_score_impact"] += rule["score_impact"]
        
        return result
    
    async def get_context_for_analysis(
        self,
        allergies: List[str],
        diseases: List[str],
        product_allergens: List[str]
    ) -> str:
        """
        분석에 필요한 컨텍스트 검색
        
        Args:
            allergies: 사용자 알레르기 목록
            diseases: 사용자 질병 목록
            product_allergens: 제품 알레르기 유발 성분
            
        Returns:
            분석에 사용할 컨텍스트 문자열
        """
        context_parts = []
        
        # 알레르기 관련 지식 검색
        if allergies or product_allergens:
            allergy_query = f"알레르기 {' '.join(allergies + product_allergens)}"
            allergy_docs = await self.search_knowledge(allergy_query, k=2, category="allergies")
            context_parts.extend([doc["content"] for doc in allergy_docs])
        
        # 질병 관련 지식 검색
        for disease in diseases:
            disease_docs = await self.search_knowledge(f"{disease} 식이 관리", k=2, category="diseases")
            context_parts.extend([doc["content"] for doc in disease_docs])
        
        # 영양 정보 기본 지식
        nutrition_docs = await self.search_knowledge("일일 권장 영양소", k=1, category="nutrition")
        context_parts.extend([doc["content"] for doc in nutrition_docs])
        
        return "\n\n".join(context_parts)
    
    async def add_knowledge(
        self,
        content: str,
        category: str,
        title: str,
        keywords: List[str] = None
    ) -> bool:
        """
        새로운 지식 추가
        
        Args:
            content: 지식 내용
            category: 카테고리
            title: 제목
            keywords: 키워드 목록
            
        Returns:
            성공 여부
        """
        try:
            embedding = await self._get_embedding(content)
            if not embedding:
                return False
            
            async with async_session_maker() as session:
                doc = KnowledgeDocument(
                    content=content,
                    category=category,
                    title=title,
                    keywords=keywords or [],
                    embedding=embedding
                )
                session.add(doc)
                await session.commit()
                
            logger.info(f"지식 추가 완료: {title}")
            return True
            
        except Exception as e:
            logger.error(f"지식 추가 실패: {e}")
            return False
    
    async def add_rule(
        self,
        rule_type: str,
        condition_key: str,
        warning_message: str,
        nutrient_limits: Dict[str, Any] = None,
        severity: str = "warning",
        score_impact: int = -10,
        description: str = None
    ) -> bool:
        """
        새로운 분석 규칙 추가
        
        Args:
            rule_type: 규칙 타입 (allergy, disease, nutrition)
            condition_key: 조건 키 (예: "당뇨", "땅콩")
            warning_message: 경고 메시지
            nutrient_limits: 영양소 제한 조건
            severity: 심각도 (safe, warning, danger)
            score_impact: 점수 영향도
            description: 규칙 설명
            
        Returns:
            성공 여부
        """
        try:
            embedding = None
            if description:
                embedding = await self._get_embedding(description)
            
            async with async_session_maker() as session:
                rule = AnalysisRule(
                    rule_type=rule_type,
                    condition_key=condition_key,
                    nutrient_limits=json.dumps(nutrient_limits) if nutrient_limits else None,
                    warning_message=warning_message,
                    severity=severity,
                    score_impact=score_impact,
                    description=description,
                    embedding=embedding
                )
                session.add(rule)
                await session.commit()
                
            logger.info(f"규칙 추가 완료: {condition_key}")
            return True
            
        except Exception as e:
            logger.error(f"규칙 추가 실패: {e}")
            return False


# 싱글톤 인스턴스
rag_service = RAGService()


# 모듈 레벨 헬퍼 함수들 (gpt_service에서 사용)
def calculate_bmi(weight: float, height: float) -> float:
    """BMI 계산"""
    if not weight or not height or height <= 0:
        return 0.0
    height_m = height / 100
    return round(weight / (height_m ** 2), 1)


def get_personalized_recommendations(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """개인화된 권장사항 반환"""
    return rag_service.calculate_personalized_limits(
        weight=user_profile.get("weight", 70),
        height=user_profile.get("height", 170),
        age_range=user_profile.get("age_range", "20대"),
        gender=user_profile.get("gender", "male"),
        special_conditions=user_profile.get("special_conditions", [])
    )
