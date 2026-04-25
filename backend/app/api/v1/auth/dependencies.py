# =============================================================
# 인증 의존성 — 로그인 여부 확인
# 로그인이 필요한 API에 자동으로 적용되는 인증 검사기
# =============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_token
from app.core.redis_client import is_token_blacklisted
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    요청 헤더의 토큰을 검사해서 현재 로그인한 사용자를 반환합니다.
    로그인 필요한 모든 API에서 사용합니다.
    """
    token = credentials.credentials

    # 로그아웃된 토큰인지 확인
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그아웃된 토큰입니다. 다시 로그인해주세요.",
        )

    # 토큰 유효성 검사
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었거나 유효하지 않습니다.",
        )

    # 사용자 조회
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않거나 비활성화된 계정입니다.",
        )

    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """관리자 전용 API에서 사용합니다."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return current_user
