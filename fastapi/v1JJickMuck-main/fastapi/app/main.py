from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from .config.settings import get_settings
from .api.v1 import rag_router
from .database import init_database

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시
    logger.info("🚀 FastAPI 서버 시작")
    settings = get_settings()
    logger.info(f"환경: DEBUG={settings.debug}")
    
    # 데이터베이스 초기화
    try:
        await init_database()
        logger.info("✅ PostgreSQL + pgvector 연결 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
    
    yield
    
    # 종료 시
    logger.info("👋 FastAPI 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="JJikMuk RAG + LLM API",
    description="""
    ## 식품 영양 분석 RAG + LLM API
    
    사용자의 건강 프로필을 기반으로 식품의 적합성을 분석합니다.
    
    ### 아키텍처
    
    ```
    Front → Node.js → FastAPI(OCR) → Node.js → FastAPI(RAG+LLM) → Node.js → Front
    ```
    
    ### 주요 기능
    
    - **규칙 기반 분석**: PostgreSQL + pgvector를 활용한 규칙 매칭
    - **RAG 검색**: 관련 영양/건강 지식 검색
    - **GPT 분석**: OpenAI GPT를 활용한 개인화된 영양 조언
    
    ### 인증
    
    모든 API 요청에는 `Authorization: Bearer <API_KEY>` 헤더가 필요합니다.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if get_settings().debug else None
        }
    )


# 라우터 등록
app.include_router(rag_router)


# 헬스 체크
@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "service": "JJikMuk RAG + LLM API",
        "version": "1.0.0",
        "database": "PostgreSQL + pgvector"
    }


@app.get("/")
async def root():
    """API 루트"""
    return {
        "message": "JJikMuk RAG + LLM API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
