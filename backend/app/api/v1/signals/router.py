"""
기술적 신호 조회 API — 앱에서 신호 이력 확인용

GET /signals/recent        : 내 관심종목 최근 신호 목록
GET /signals/{ticker}      : 특정 종목의 신호 이력
GET /signals/grades/count  : 등급별 신호 발생 통계
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.stock import Stock
from app.models.tech_signal import TechSignal
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/signals", tags=["기술적 신호"])


@router.get("/recent")
async def get_recent_signals(
    limit: int = Query(default=20, ge=1, le=100),
    days: int  = Query(default=7,  ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    내 관심종목에서 발생한 최근 신호 목록을 반환합니다.

    limit : 최대 조회 건수 (1~100, 기본 20)
    days  : 조회 기간 (1~30일, 기본 7일)
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # 내 관심종목 stock_id 목록
    wl_r = await db.execute(
        select(Watchlist.stock_id).where(Watchlist.user_id == current_user.id)
    )
    stock_ids = [row[0] for row in wl_r.all()]

    if not stock_ids:
        return []

    r = await db.execute(
        select(TechSignal, Stock)
        .join(Stock, TechSignal.stock_id == Stock.id)
        .where(
            TechSignal.stock_id.in_(stock_ids),
            TechSignal.detected_at >= since,
        )
        .order_by(desc(TechSignal.detected_at))
        .limit(limit)
    )
    rows = r.all()

    return [
        {
            "id":          ts.id,
            "ticker":      s.ticker,
            "name":        s.name,
            "signal_type": ts.signal_type.value,
            "grade":       ts.grade.value,
            "price":       float(ts.price_at_signal),
            "indicators":  ts.indicators_triggered,
            "alert_sent":  ts.alert_sent,
            "detected_at": ts.detected_at.isoformat(),
        }
        for ts, s in rows
    ]


@router.get("/{ticker}")
async def get_ticker_signals(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """특정 종목의 기술적 신호 이력을 반환합니다."""
    ticker = ticker.upper().strip()

    stock_r = await db.execute(
        select(Stock).where(Stock.ticker == ticker)
    )
    stock = stock_r.scalar_one_or_none()
    if not stock:
        return []

    r = await db.execute(
        select(TechSignal)
        .where(TechSignal.stock_id == stock.id)
        .order_by(desc(TechSignal.detected_at))
        .limit(limit)
    )
    signals = r.scalars().all()

    return [
        {
            "id":          ts.id,
            "signal_type": ts.signal_type.value,
            "grade":       ts.grade.value,
            "price":       float(ts.price_at_signal),
            "indicators":  ts.indicators_triggered,
            "alert_sent":  ts.alert_sent,
            "detected_at": ts.detected_at.isoformat(),
        }
        for ts in signals
    ]
