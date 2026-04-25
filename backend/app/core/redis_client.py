# =============================================================
# Redis 클라이언트
# Redis = 빠른 임시 저장소 (알림큐, 초대코드, 시세 캐시 담당)
# =============================================================

import json
from typing import Optional, Any
import redis.asyncio as aioredis
from app.core.config import settings

# Redis 연결 풀 (연결을 재사용해서 속도 향상)
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Redis 연결을 반환합니다. 연결이 없으면 새로 만듭니다."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def close_redis():
    """앱 종료 시 Redis 연결을 닫습니다."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


# -------------------------------------------------------
# 초대코드 관련 함수
# Redis에 저장 시 1시간 후 자동 삭제 (TTL)
# -------------------------------------------------------

async def save_invite_code(code: str, user_id: int) -> None:
    """초대코드를 Redis에 저장합니다. 1시간 후 자동 삭제."""
    redis = await get_redis()
    key = f"invite:{code}"
    await redis.setex(
        key,
        settings.INVITE_CODE_EXPIRE_HOURS * 3600,  # 초 단위
        str(user_id)
    )


async def get_invite_code_owner(code: str) -> Optional[int]:
    """초대코드가 유효한지 확인하고 생성자 ID를 반환합니다."""
    redis = await get_redis()
    key = f"invite:{code}"
    value = await redis.get(key)
    return int(value) if value else None


async def delete_invite_code(code: str) -> None:
    """사용된 초대코드를 즉시 삭제합니다 (1회용)."""
    redis = await get_redis()
    await redis.delete(f"invite:{code}")


# -------------------------------------------------------
# Refresh Token 블랙리스트 (로그아웃 처리)
# 로그아웃 시 해당 토큰을 블랙리스트에 올려서 재사용 차단
# -------------------------------------------------------

async def blacklist_token(token: str, expire_seconds: int) -> None:
    """로그아웃된 토큰을 블랙리스트에 추가합니다."""
    redis = await get_redis()
    await redis.setex(f"blacklist:{token}", expire_seconds, "1")


async def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인합니다."""
    redis = await get_redis()
    return await redis.exists(f"blacklist:{token}") > 0


# -------------------------------------------------------
# 시세 캐시 (한국투자증권 API Rate Limit 대응)
# 같은 종목을 1분 안에 여러 번 요청하면 캐시에서 반환
# -------------------------------------------------------

async def cache_stock_price(ticker: str, price_data: dict, ttl_seconds: int = 60) -> None:
    """주식 현재가를 캐시에 저장합니다."""
    redis = await get_redis()
    await redis.setex(f"price:{ticker}", ttl_seconds, json.dumps(price_data))


async def get_cached_stock_price(ticker: str) -> Optional[dict]:
    """캐시된 주식 현재가를 반환합니다."""
    redis = await get_redis()
    data = await redis.get(f"price:{ticker}")
    return json.loads(data) if data else None


# -------------------------------------------------------
# 기술적 신호 중복 알림 방지
# 같은 신호가 1시간 안에 다시 발생해도 알림을 보내지 않음
# -------------------------------------------------------

async def mark_signal_alerted(stock_id: int, signal_type: str, grade: str) -> None:
    """신호 알림을 발송했다고 표시합니다. 1시간 동안 중복 알림 차단."""
    redis = await get_redis()
    key = f"signal_sent:{stock_id}:{signal_type}:{grade}"
    await redis.setex(key, 3600, "1")


async def is_signal_already_alerted(stock_id: int, signal_type: str, grade: str) -> bool:
    """이미 알림을 보낸 신호인지 확인합니다."""
    redis = await get_redis()
    key = f"signal_sent:{stock_id}:{signal_type}:{grade}"
    return await redis.exists(key) > 0
