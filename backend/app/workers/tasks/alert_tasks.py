"""
알림 발송 태스크 — 신호 발생 즉시 / 매일 07:30 자동 실행

send_signal_alert    : 신호 발생 즉시 호출 (목표: 60초 이내)
send_daily_recommendation : 매일 07:30 AI top5 텔레그램 발송
"""

import asyncio
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 태스크 1: 기술적 신호 즉시 알림
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, queue="alerts")
def send_signal_alert(
    self,
    stock_id: int,
    signal_type: str,
    grade: str,
    indicators: dict,
    price: float,
):
    """
    [즉시 실행] 기술적 신호 발생 → 텔레그램 알림

    queue="alerts": 별도 높은-우선순위 큐 (일반 작업과 분리)
    """
    try:
        result = asyncio.run(
            _send_signal_async(stock_id, signal_type, grade, indicators, price)
        )
        logger.info(
            "신호알림 발송 | stock_id=%d grade=%s sent=%s",
            stock_id, grade, result,
        )
        return result
    except Exception as exc:
        logger.error("신호알림 발송 오류: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=10)


async def _send_signal_async(
    stock_id: int,
    signal_type: str,
    grade: str,
    indicators: dict,
    price: float,
) -> bool:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.stock import Stock
    from app.models.ai_analysis import AiAnalysis
    from app.services.notification.telegram import send_signal_alert

    async with AsyncSessionLocal() as db:
        # 종목 정보 조회
        stock_r = await db.execute(
            select(Stock).where(Stock.id == stock_id)
        )
        stock = stock_r.scalar_one_or_none()
        if not stock:
            logger.warning("신호알림: stock_id=%d 종목 없음", stock_id)
            return False

        # AI 분석에서 목표가/손절가 조회 (없어도 알림은 발송)
        ai_r = await db.execute(
            select(AiAnalysis)
            .where(
                AiAnalysis.stock_id == stock_id,
                AiAnalysis.is_top5 == 1,
            )
            .order_by(AiAnalysis.analyzed_at.desc())
            .limit(1)
        )
        ai = ai_r.scalar_one_or_none()
        target    = float(ai.target_price)    if (ai and ai.target_price)    else None
        stop_loss = float(ai.stop_loss_price) if (ai and ai.stop_loss_price) else None

    return await send_signal_alert(
        ticker=stock.ticker,
        name=stock.name,
        price=price,
        signal_type=signal_type,
        grade=grade,
        triggers=indicators,
        target_price=target,
        stop_loss=stop_loss,
    )


# ─────────────────────────────────────────────────────────────
# 태스크 2: 일일 AI 추천 발송
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def send_daily_recommendation(self):
    """[매일 07:30] AI top5 추천 종목을 텔레그램으로 발송"""
    try:
        result = asyncio.run(_send_daily_async())
        logger.info("일일추천 알림 완료 | sent=%s", result.get("sent"))
        return result
    except Exception as exc:
        logger.error("일일추천 알림 오류: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=60)


async def _send_daily_async() -> dict:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.stock import Stock
    from app.models.ai_analysis import AiAnalysis
    from app.services.notification.telegram import send_daily_recommendations

    async with AsyncSessionLocal() as db:
        # 가장 최근 분석된 top5 조회
        r = await db.execute(
            select(AiAnalysis, Stock)
            .join(Stock, AiAnalysis.stock_id == Stock.id)
            .where(AiAnalysis.is_top5 == 1)
            .order_by(AiAnalysis.analyzed_at.desc())
            .limit(5)
        )
        rows = r.all()

    if not rows:
        logger.warning("일일추천: top5 데이터 없음 (AI 분석을 먼저 실행하세요)")
        return {"sent": False, "reason": "no_data"}

    top5 = [
        {
            "ticker":           s.ticker,
            "name":             s.name,
            "buy_probability":  a.buy_probability,
            "one_line_summary": a.one_line_summary or "",
            "target_price":     float(a.target_price) if a.target_price else None,
            "stop_loss_price":  float(a.stop_loss_price) if a.stop_loss_price else None,
        }
        for a, s in rows
    ]

    ok = await send_daily_recommendations(top5)
    return {"sent": ok, "count": len(top5)}
