# 일일 AI 분석 실행기 — 매일 07:00 Celery가 호출
# 전체 파이프라인: 수집 → 1차필터 → 2차필터 → DB저장 → 알림

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select, delete

from app.core.database import AsyncSessionLocal
from app.models.stock import Stock
from app.models.ai_analysis import AiAnalysis, Recommendation
from app.services.ai_engine.first_filter import run_first_filter
from app.services.ai_engine.second_filter import run_second_filter

logger = logging.getLogger(__name__)


async def run_daily_analysis() -> dict:
    """
    일일 AI 분석 전체 파이프라인 실행.
    반환: {top5: [...], top30_count: 30, analyzed_at: ...}
    """
    logger.info("=== 일일 AI 분석 시작 ===")
    start = datetime.now(timezone.utc)

    # 1차 필터
    top30 = await run_first_filter(limit=30)
    if not top30:
        logger.error("1차 필터 결과 없음")
        return {"error": "1차 필터 결과 없음"}

    # 2차 필터
    top5 = await run_second_filter(top30)
    if not top5:
        logger.error("2차 필터 결과 없음")
        return {"error": "2차 필터 결과 없음"}

    # DB 저장
    await _save_results(top30, top5)

    elapsed = (datetime.now(timezone.utc) - start).seconds
    logger.info(f"=== 일일 AI 분석 완료 ({elapsed}초) ===")

    return {
        "top5": [{"ticker": s["ticker"], "name": s["name"],
                  "buy_probability": s.get("buy_probability", 0)} for s in top5],
        "top30_count": len(top30),
        "analyzed_at": start.isoformat(),
    }


async def _save_results(top30: list[dict], top5: list[dict]) -> None:
    """분석 결과를 DB에 저장. 오늘 기존 결과는 덮어씀."""
    top5_tickers = {s["ticker"] for s in top5}

    async with AsyncSessionLocal() as db:
        try:
            # 오늘 분석 결과 삭제 후 재저장
            today = datetime.now(timezone.utc).date()
            await db.execute(
                delete(AiAnalysis).where(
                    AiAnalysis.analyzed_at >= datetime.combine(today, datetime.min.time())
                )
            )

            # 30개 저장
            for stock in top30:
                ticker = stock["ticker"]
                is_top5 = ticker in top5_tickers

                # top5 종목은 LLM 분석 결과 사용
                llm = next((s for s in top5 if s["ticker"] == ticker), {})

                result = await db.execute(select(Stock).where(Stock.ticker == ticker))
                stock_obj = result.scalar_one_or_none()
                if not stock_obj:
                    continue

                rec_map = {
                    "strong_buy": Recommendation.STRONG_BUY,
                    "buy": Recommendation.BUY,
                    "hold": Recommendation.HOLD,
                    "sell": Recommendation.SELL,
                }
                rec_str = llm.get("recommendation", "hold") if is_top5 else "hold"

                analysis = AiAnalysis(
                    stock_id=stock_obj.id,
                    recommendation=rec_map.get(rec_str, Recommendation.HOLD),
                    buy_probability=llm.get("buy_probability", int(stock["total_score"])) if is_top5 else int(stock["total_score"] * 0.6),
                    target_price=llm.get("target_price") if is_top5 else None,
                    stop_loss_price=llm.get("stop_loss_price") if is_top5 else None,
                    expected_period_days=llm.get("expected_period_days") if is_top5 else None,
                    buy_reason=llm.get("buy_reason") if is_top5 else None,
                    risk_reason=llm.get("risk_reason") if is_top5 else None,
                    one_line_summary=llm.get("one_line_summary") if is_top5 else None,
                    factor_scores=llm.get("factor_scores", stock["scores"]),
                    llm_model=llm.get("model", "quant_only"),
                    is_top30=1,
                    is_top5=1 if is_top5 else 0,
                )
                db.add(analysis)

            await db.commit()
            logger.info(f"DB 저장 완료: {len(top30)}개 (top5: {len(top5)}개)")
        except Exception as e:
            await db.rollback()
            logger.error(f"DB 저장 실패: {e}")
            raise
