# 한국투자증권 API 접근 토큰 관리
# 토큰 유효시간 24시간 → Redis 캐싱으로 불필요한 재발급 방지

import httpx
import logging
from datetime import datetime, timezone
from app.core.config import settings
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

REDIS_KEY = "kis:access_token"


async def get_access_token() -> str:
    """
    KIS API 접근 토큰 반환.
    Redis에 캐싱된 토큰이 있으면 재사용, 없으면 새로 발급.
    """
    redis = await get_redis()
    cached = await redis.get(REDIS_KEY)
    if cached:
        return cached

    return await _issue_new_token()


async def _issue_new_token() -> str:
    """한국투자증권 서버에서 새 접근 토큰 발급."""
    url = f"{settings.KIS_BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": settings.KIS_APP_KEY,
        "appsecret": settings.KIS_APP_SECRET,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    token = data["access_token"]
    expires_in = int(data.get("expires_in", 86400)) - 300  # 만료 5분 전�� 갱신

    redis = await get_redis()
    await redis.setex(REDIS_KEY, expires_in, token)

    logger.info("KIS 접근 토큰 발급 완료")
    return token


async def get_headers(tr_id: str = "") -> dict:
    """API 요청에 공통으로 사용되는 헤더 반환."""
    token = await get_access_token()
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": settings.KIS_APP_KEY,
        "appsecret": settings.KIS_APP_SECRET,
    }
    if tr_id:
        headers["tr_id"] = tr_id
    return headers
