"""
JJikMuk RAG 시드 데이터 스크립트
- JSON 파일에서 데이터 로드
- PostgreSQL + pgvector에 저장
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# 경로 설정
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from app.database import async_session_maker, init_database
from app.services.rag_service import RAGService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 데이터 디렉토리
DATA_DIR = SCRIPT_DIR / "data"


def load_json(filename: str) -> dict:
    """JSON 파일 로드"""
    filepath = DATA_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


async def clear_existing_data():
    """기존 데이터 삭제"""
    logger.info("🗑️ 기존 데이터 삭제 중...")
    
    async with async_session_maker() as session:
        await session.execute(text("TRUNCATE TABLE knowledge_documents RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE TABLE analysis_rules RESTART IDENTITY CASCADE"))
        await session.commit()
    
    logger.info("✅ 기존 데이터 삭제 완료")


async def seed_allergy_rules(rag_service: RAGService):
    """알레르기 규칙 시드"""
    logger.info("🥜 알레르기 규칙 추가 중...")
    
    data = load_json("allergy_rules.json")
    count = 0
    
    for rule in data["allergy_rules"]:
        try:
            # nutrient_limits를 JSON 문자열로 변환
            nutrient_limits = json.dumps(rule.get("nutrient_limits")) if rule.get("nutrient_limits") else None
            
            await rag_service.add_rule(
                rule_type=rule["rule_type"],
                condition_key=rule["condition_key"],
                warning_message=rule["warning_message"],
                severity=rule["severity"],
                score_impact=rule["score_impact"],
                nutrient_limits=nutrient_limits,
                description=rule.get("description")
            )
            count += 1
            logger.info(f"  ✅ {rule['condition_key']}")
        except Exception as e:
            logger.error(f"  ❌ {rule['condition_key']}: {e}")
    
    logger.info(f"🥜 알레르기 규칙 {count}개 추가 완료")
    return count


async def seed_disease_rules(rag_service: RAGService):
    """질환 규칙 시드"""
    logger.info("🏥 질환 규칙 추가 중...")
    
    data = load_json("disease_rules.json")
    count = 0
    
    for rule in data["disease_rules"]:
        try:
            nutrient_limits = json.dumps(rule.get("nutrient_limits")) if rule.get("nutrient_limits") else None
            
            await rag_service.add_rule(
                rule_type=rule["rule_type"],
                condition_key=rule["condition_key"],
                warning_message=rule["warning_message"],
                severity=rule["severity"],
                score_impact=rule["score_impact"],
                nutrient_limits=nutrient_limits,
                description=rule.get("description")
            )
            count += 1
            logger.info(f"  ✅ {rule['condition_key']}")
        except Exception as e:
            logger.error(f"  ❌ {rule['condition_key']}: {e}")
    
    logger.info(f"🏥 질환 규칙 {count}개 추가 완료")
    return count


async def seed_nutrition_rules(rag_service: RAGService):
    """영양 규칙 시드"""
    logger.info("🍎 영양 규칙 추가 중...")
    
    data = load_json("nutrition_rules.json")
    count = 0
    
    for rule in data["nutrition_rules"]:
        try:
            nutrient_limits = json.dumps(rule.get("nutrient_limits")) if rule.get("nutrient_limits") else None
            
            await rag_service.add_rule(
                rule_type=rule["rule_type"],
                condition_key=rule["condition_key"],
                warning_message=rule["warning_message"],
                severity=rule["severity"],
                score_impact=rule["score_impact"],
                nutrient_limits=nutrient_limits,
                description=rule.get("description")
            )
            count += 1
            logger.info(f"  ✅ {rule['condition_key']}")
        except Exception as e:
            logger.error(f"  ❌ {rule['condition_key']}: {e}")
    
    logger.info(f"🍎 영양 규칙 {count}개 추가 완료")
    return count


async def seed_knowledge_base(rag_service: RAGService):
    """지식 베이스 시드"""
    logger.info("📚 지식 베이스 추가 중...")
    
    data = load_json("knowledge_base.json")
    count = 0
    
    for doc in data["knowledge_documents"]:
        try:
            await rag_service.add_knowledge(
                content=doc["content"],
                category=doc["category"],
                title=doc["title"],
                keywords=doc.get("keywords", [])
            )
            count += 1
            logger.info(f"  ✅ {doc['title']}")
        except Exception as e:
            logger.error(f"  ❌ {doc['title']}: {e}")
    
    logger.info(f"📚 지식 베이스 {count}개 추가 완료")
    return count


async def main():
    """메인 시드 함수"""
    print("=" * 60)
    print("🌱 JJikMuk RAG 시드 데이터 스크립트")
    print("=" * 60)
    
    # 1. 데이터베이스 초기화
    logger.info("🔧 데이터베이스 연결 및 초기화 중...")
    try:
        await init_database()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        return
    
    # 2. 기존 데이터 삭제 확인
    clear_input = input("\n기존 데이터를 삭제하시겠습니까? (y/N): ").strip().lower()
    if clear_input == 'y':
        await clear_existing_data()
    
    # 3. RAG 서비스 초기화
    logger.info("🔧 RAG 서비스 초기화 중...")
    rag_service = RAGService()
    
    # 4. 시드 데이터 추가
    print("\n" + "-" * 60)
    
    allergy_count = await seed_allergy_rules(rag_service)
    disease_count = await seed_disease_rules(rag_service)
    nutrition_count = await seed_nutrition_rules(rag_service)
    knowledge_count = await seed_knowledge_base(rag_service)
    
    # 5. 결과 요약
    print("\n" + "=" * 60)
    print("📊 시드 데이터 요약")
    print("=" * 60)
    print(f"  알레르기 규칙: {allergy_count}개")
    print(f"  질환 규칙: {disease_count}개")
    print(f"  영양 규칙: {nutrition_count}개")
    print(f"  지식 베이스: {knowledge_count}개")
    print(f"  ─────────────────")
    print(f"  총 규칙: {allergy_count + disease_count + nutrition_count}개")
    print(f"  총 문서: {knowledge_count}개")
    print("=" * 60)
    print("✅ 시드 데이터 추가 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
