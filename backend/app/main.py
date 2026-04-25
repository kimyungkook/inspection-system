# =============================================================
# FastAPI 메인 서버
# 이 파일이 앱의 시작점입니다.
# docker-compose up 실행 시 이 파일이 가장 먼저 실행됩니다.
# =============================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis_client import close_redis

# 각 기능별 라우터 불러오기
from app.api.v1.auth.router import router as auth_router

logger = logging.getLogger(__name__)


# -------------------------------------------------------
# 앱 시작/종료 시 자동 실행되는 작업
# -------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === 앱 시작 시 ===
    logger.info("AI 주식 매매 가이드 앱 서버 시작 중...")

    # 데이터베이스 테이블 자동 생성 (없는 테이블만 새로 만듦)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("데이터베이스 테이블 준비 완료")

    yield   # 앱이 실행되는 동안 여기서 대기

    # === 앱 종료 시 ===
    await close_redis()
    logger.info("서버 종료")


# -------------------------------------------------------
# FastAPI 앱 생성
# -------------------------------------------------------
app = FastAPI(
    title="AI 주식 매매 가이드 앱",
    description="AI가 실제 주식을 분석하고 매수/매도 타이밍을 알려주는 서비스",
    version="1.0.0",
    docs_url="/docs",        # API 문서: localhost:8000/docs
    redoc_url="/redoc",
    lifespan=lifespan,
)


# -------------------------------------------------------
# CORS 설정 (Flutter 앱과 통신 허용)
# CORS = 다른 주소에서 이 서버에 요청하는 것을 허용하는 설정
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------
# API 라우터 등록
# 각 기능별 API를 /api/v1/ 하위에 등록
# -------------------------------------------------------
app.include_router(auth_router, prefix="/api/v1")
# 이후 Phase에서 추가될 라우터들:
# app.include_router(stocks_router, prefix="/api/v1")
# app.include_router(ai_router, prefix="/api/v1")
# app.include_router(simulation_router, prefix="/api/v1")
# app.include_router(signals_router, prefix="/api/v1")
# app.include_router(alerts_router, prefix="/api/v1")
# app.include_router(admin_router, prefix="/api/v1")


# -------------------------------------------------------
# 기본 응답
# -------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "AI 주식 매매 가이드 앱 서버가 정상 실행 중입니다.", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """서버 상태 확인용 엔드포인트"""
    return {"status": "healthy", "env": settings.APP_ENV}


# -------------------------------------------------------
# 전역 오류 처리
# -------------------------------------------------------
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"success": False, "message": "요청한 경로를 찾을 수 없습니다."})


@app.exception_handler(500)
async def server_error_handler(request, exc):
    logger.error(f"서버 오류: {exc}")
    return JSONResponse(status_code=500, content={"success": False, "message": "서버 내부 오류가 발생했습니다."})
