from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ARRAY, text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from typing import AsyncGenerator
import logging

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Base(DeclarativeBase):
    pass


class KnowledgeDocument(Base):
    """RAG 지식 베이스 문서 테이블"""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 문서 내용
    content = Column(Text, nullable=False)
    
    # 메타데이터
    category = Column(String(50), nullable=False, index=True)  # allergies, diseases, nutrition
    title = Column(String(200), nullable=False)
    keywords = Column(ARRAY(String), default=[])
    
    # 임베딩 벡터
    embedding = Column(Vector(settings.embedding_dimension))
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AnalysisRule(Base):
    """규칙 기반 분석을 위한 규칙 테이블"""
    __tablename__ = "analysis_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 규칙 정보
    rule_type = Column(String(50), nullable=False, index=True)  # allergy, disease, nutrition
    condition_key = Column(String(100), nullable=False, index=True)  # 예: "당뇨", "고혈압", "땅콩"
    
    # 규칙 내용
    nutrient_limits = Column(Text)  # JSON: {"sodium": {"max": 500}, "sugar": {"max": 10}}
    warning_message = Column(Text, nullable=False)
    severity = Column(String(20), default="warning")  # safe, warning, danger
    score_impact = Column(Integer, default=-10)  # 점수 영향도
    
    # 임베딩 (규칙 설명용)
    description = Column(Text)
    embedding = Column(Vector(settings.embedding_dimension))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# 비동기 엔진 및 세션
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """DB 세션 의존성"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_database():
    """데이터베이스 초기화 (테이블 생성)"""
    async with engine.begin() as conn:
        # pgvector 확장 활성화
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # 테이블 생성
        await conn.run_sync(Base.metadata.create_all)
    logger.info("데이터베이스 초기화 완료")
