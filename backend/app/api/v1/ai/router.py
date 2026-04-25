# AI 분석 API
# GET  /ai/recommendations        — 오늘의 AI 추천 5종목
# GET  /ai/recommendations/top30  — 1차 필터 30종목
# GET  /ai/analyze/{ticker}       — 단일 종목 즉시 분석 (premium+)
# GET  /ai/performance            — AI 추천 성과 통계

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.api.v1.auth.dependencies import get_current_user
from app.models.user import User, UserTier
from app.models.stock import Stock
from app.models.ai_analysis import AiAnalysis
from app.services.ai_engine.llm_client import analyze_stock
from app.services.kis_api.client import get_current_price, get_financial_data, get_daily_candles
from app.services.tech_engine.indicator_calculator import calculate

router = APIRouter(prefix="/ai", tags=["AI 분석"])


@router.get("/recommendations")
async def get_top5(db: AsyncSession = Depends(get_db)):
    """오늘의 AI 추천 5종목 반환."""
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(AiAnalysis, Stock)
        .join(Stock, AiAnalysis.stock_id == Stock.id)
        .where(
            AiAnalysis.is_top5 == 1,
            AiAnalysis.analyzed_at >= datetime.combine(today, datetime.min.time()),
        )
        .order_by(desc(AiAnalysis.buy_probability))
        .limit(5)
    )
    rows = result.all()

    return [
        {
            "rank": i + 1,
            "ticker": s.ticker,
            "name": s.name,
            "current_price": s.last_price,
            "recommendation": a.recommendation.value,
            "buy_probability": a.buy_probability,
            "target_price": a.target_price,
            "stop_loss_price": a.stop_loss_price,
            "one_line_summary": a.one_line_summary,
            "buy_reason": a.buy_reason,
            "risk_reason": a.risk_reason,
            "analyzed_at": a.analyzed_at,
        }
        for i, (a, s) in enumerate(rows)
    ]


@router.get("/recommendations/top30")
async def get_top30(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """1차 필터 통과 30종목 반환 (로그인 필요)."""
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(AiAnalysis, Stock)
        .join(Stock, AiAnalysis.stock_id == Stock.id)
        .where(
            AiAnalysis.is_top30 == 1,
            AiAnalysis.analyzed_at >= datetime.combine(today, datetime.min.time()),
        )
        .order_by(desc(AiAnalysis.buy_probability))
        .limit(30)
    )
    rows = result.all()
    return [
        {
            "ticker": s.ticker, "name": s.name,
            "current_price": s.last_price,
            "buy_probability": a.buy_probability,
            "factor_scores": a.factor_scores,
        }
        for a, s in rows
    ]


@router.get("/analyze/{ticker}")
async def analyze_single(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """단일 종목 즉시 AI 분석 (Premium 이상만 가능)."""
    if current_user.tier == UserTier.FREE:
        raise HTTPException(403, detail="단일 종목 즉시 분석은 Premium 이상 기능입니다.")

    result = await db.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(404, detail="종목을 찾을 수 없습니다.")

    # 병렬로 데이터 수집
    import asyncio
    price_data, fin_data, df = await asyncio.gather(
        get_current_price(ticker),
        get_financial_data(ticker),
        get_daily_candles(ticker, 90),
        return_exceptions=True,
    )

    ind = calculate(df, ticker) if isinstance(df, object) and df is not None else None
    stock_data = {
        "종목코드": ticker,
        "종목명": stock.name,
        "현재가": price_data.get("current_price", 0) if isinstance(price_data, dict) else 0,
        "재무지표": fin_data if isinstance(fin_data, dict) else {},
        "기술적지표": {
            "rsi": ind.rsi if ind else None,
            "macd_hist": ind.macd_hist if ind else None,
            "ma_aligned": ind.ma_aligned if ind else False,
            "volume_ratio": ind.volume_ratio if ind else 0,
        },
    }

    analysis = await analyze_stock(stock_data)
    if not analysis:
        raise HTTPException(500, detail="AI 분석 중 오류가 발생했습니다.")

    return {"ticker": ticker, "name": stock.name, **analysis}


@router.get("/performance")
async def get_performance(
    days: int = Query(30, description="조회 기간(일)"),
    db: AsyncSession = Depends(get_db),
):
    """AI 추천 성과 통계 반환."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(AiAnalysis.id).label("total"),
            func.avg(AiAnalysis.buy_probability).label("avg_probability"),
            func.count().filter(AiAnalysis.is_top5 == 1).label("top5_count"),
        )
        .where(AiAnalysis.analyzed_at >= since)
    )
    stats = result.one()
    return {
        "period_days": days,
        "total_analyzed": stats.total or 0,
        "avg_buy_probability": round(float(stats.avg_probability or 0), 1),
        "top5_recommendations": stats.top5_count or 0,
    }
