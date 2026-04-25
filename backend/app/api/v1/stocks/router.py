# 주식 데이터 API
# GET /stocks/{ticker}/price      — 현재가 조회
# GET /stocks/{ticker}/indicators — 기술적 지표 조회
# GET /stocks/{ticker}/candles    — 분봉/일봉 조회
# POST /stocks/watchlist          — 관심종목 추가
# DELETE /stocks/watchlist/{id}   — 관심종목 삭제
# GET /stocks/watchlist           — 관심종목 목록

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from typing import Optional

from app.core.database import get_db
from app.api.v1.auth.dependencies import get_current_user
from app.models.user import User
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.models.tech_signal import TechIndicator
from app.services.kis_api.client import get_current_price, get_minute_candles, get_daily_candles
from app.services.tech_engine.indicator_calculator import calculate
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/stocks", tags=["주식"])


@router.get("/{ticker}/price")
async def get_price(ticker: str):
    """실시간 현재가 조회."""
    data = await get_current_price(ticker)
    if not data:
        raise HTTPException(404, detail=f"{ticker} 시세를 가져올 수 없습니다.")
    return data


@router.get("/{ticker}/indicators")
async def get_indicators(
    ticker: str,
    timeframe: str = Query("5", description="분봉 단위: 1, 5, 30"),
    db: AsyncSession = Depends(get_db),
):
    """기술적 지표 조회 (실시간 계산)."""
    # DB 캐시 먼저 확인
    result = await db.execute(
        select(TechIndicator).where(
            TechIndicator.stock_id == select(Stock.id).where(Stock.ticker == ticker).scalar_subquery(),
            TechIndicator.timeframe == f"{timeframe}m",
        ).order_by(TechIndicator.updated_at.desc()).limit(1)
    )
    cached = result.scalar_one_or_none()
    if cached:
        return {
            "ticker": ticker,
            "timeframe": f"{timeframe}m",
            "rsi": cached.rsi,
            "macd_hist": cached.macd_hist,
            "bb_position": _calc_bb_position(cached),
            "ma5": cached.ma5, "ma20": cached.ma20,
            "volume_ratio": cached.volume_ratio,
            "updated_at": cached.updated_at,
        }

    # 캐시 없으면 실시간 계산
    df = await get_minute_candles(ticker, timeframe)
    if df is None or df.empty:
        raise HTTPException(404, detail="지표 데이터를 가져올 수 없습니다.")
    ind = calculate(df, ticker)
    if not ind:
        raise HTTPException(500, detail="지표 계산 실패")

    return {
        "ticker": ticker,
        "timeframe": f"{timeframe}m",
        "rsi": ind.rsi,
        "macd_hist": ind.macd_hist,
        "bb_upper": ind.bb_upper,
        "bb_lower": ind.bb_lower,
        "bb_position": ind.bb_position,
        "ma5": ind.ma5, "ma20": ind.ma20, "ma60": ind.ma60,
        "volume_ratio": ind.volume_ratio,
        "stoch_k": ind.stoch_k,
        "ma_aligned": ind.ma_aligned,
    }


@router.get("/{ticker}/candles")
async def get_candles(
    ticker: str,
    type: str = Query("daily", description="daily | minute"),
    period: int = Query(90, description="조회 기간(일)"),
    timeframe: str = Query("5", description="분봉 단위 (minute 선택 시)"),
):
    """캔들 차트 데이터 조회."""
    if type == "daily":
        df = await get_daily_candles(ticker, period)
    else:
        df = await get_minute_candles(ticker, timeframe)

    if df is None or df.empty:
        raise HTTPException(404, detail="차트 데이터를 가져올 수 없습니다.")
    return {"ticker": ticker, "type": type, "data": df.to_dict(orient="records")}


@router.get("/watchlist", summary="관심종목 목록")
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 관심종목 목록 반환."""
    result = await db.execute(
        select(Watchlist, Stock)
        .join(Stock, Watchlist.stock_id == Stock.id)
        .where(Watchlist.user_id == current_user.id)
    )
    rows = result.all()
    return [
        {
            "watchlist_id": w.id,
            "ticker": s.ticker,
            "name": s.name,
            "target_price": w.target_price,
            "alert_on_signal": w.alert_on_signal,
        }
        for w, s in rows
    ]


@router.post("/watchlist/{ticker}", response_model=SuccessResponse)
async def add_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """관심종목 추가."""
    result = await db.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(404, detail="존재하지 않는 종목코드입니다.")

    exists = await db.execute(
        select(Watchlist).where(Watchlist.user_id == current_user.id, Watchlist.stock_id == stock.id)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(400, detail="이미 관심종목에 추가된 종목입니다.")

    db.add(Watchlist(user_id=current_user.id, stock_id=stock.id))
    await db.commit()
    return SuccessResponse(message=f"{stock.name}이 관심종목에 추가되었습니다.")


@router.delete("/watchlist/{watchlist_id}", response_model=SuccessResponse)
async def remove_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """관심종목 삭제."""
    await db.execute(
        sql_delete(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    await db.commit()
    return SuccessResponse(message="관심종목에서 삭제되었습니다.")


def _calc_bb_position(ind: TechIndicator) -> Optional[float]:
    if ind.bb_upper and ind.bb_lower and ind.bb_upper > ind.bb_lower:
        current = ind.current_price or 0
        return round((current - float(ind.bb_lower)) / (float(ind.bb_upper) - float(ind.bb_lower)), 3)
    return None
