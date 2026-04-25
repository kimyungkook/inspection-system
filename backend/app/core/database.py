# =============================================================
# 데이터베이스 연결 설정
# PostgreSQL(정보 저장소)에 연결하는 코드입니다.
# =============================================================

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# 데이터베이스 연결 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,      # 개발중에는 SQL 쿼리 로그 출력
    pool_size=10,             # 동시 연결 수
    max_overflow=20,
)

# 세션 팩토리 (데이터베이스와 대화하는 통로)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 모든 테이블의 기반이 되는 클래스
class Base(DeclarativeBase):
    pass


# API 요청마다 데이터베이스 세션을 자동으로 열고 닫는 함수
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
