"""
AI 분석 태스크 — 매일 07:00 / 매주 월요일 09:00 자동 실행

run_daily_ai_analysis : 매일 07:00 전체 종목 → top30 → top5 선정
generate_weekly_report: 매주 월요일 09:00 지난 주 AI 추천 성과 리포트
"""

import asyncio
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 태스크 1: 매일 AI 종목 분석
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2)
def run_daily_ai_analysis(self):
    """
    [매일 07:00] AI 2단계 종목 필터링 실행

    처리 순서:
      1. KIS API → 전체 거래량 상위 종목 수집
      2. 1차 필터 (first_filter): 재무·기술·밸류에이션 점수로 30개 선별
      3. 2차 필터 (second_filter): LLM 병렬 호출로 최종 5개 선별
      4. 결과 DB 저장
      5. 일일 추천 알림 발송 태스크 실행
    """
    try:
        result = asyncio.run(_daily_analysis_async())
        logger.info(
            "AI분석 완료 | top30:%d top5:%d",
            result.get("top30_count", 0),
            len(result.get("top5", [])),
        )
        return result
    except Exception as exc:
        logger.error("AI분석 태스크 오류: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=300)   # 5분 후 재시도


async def _daily_analysis_async() -> dict:
    from app.services.ai_engine.daily_analyzer import run_daily_analysis
    from app.workers.tasks.alert_tasks import send_daily_recommendation

    result = await run_daily_analysis()

    # 분석 완료 후 일일 추천 알림 30분 뒤 발송 (07:30)
    send_daily_recommendation.apply_async(countdown=1800)

    return result


# ─────────────────────────────────────────────────────────────
# 태스크 2: 주간 AI 성과 리포트
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2)
def generate_weekly_report(self):
    """
    [매주 월요일 09:00] 지난 주 AI 추천 성과 리포트 생성 + 텔레그램 발송

    분석 항목:
      - 지난 주 top5 각 종목의 현재 수익률
      - 이번 주 발생한 기술적 신호 건수
      - 가상투자 평균 성과
    """
    try:
        result = asyncio.run(_weekly_report_async())
        logger.info("주간리포트 완료 | avg_return=%.2f%%", result.get("avg_return", 0))
        return result
    except Exception as exc:
        logger.error("주간리포트 태스크 오류: %s", exc, exc_info=True)
        # 주간 리포트는 실패해도 재시도 1회만
        raise self.retry(exc=exc, countdown=600)


async def _weekly_report_async() -> dict:
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select, func
    from app.core.database import AsyncSessionLocal
    from app.models.ai_analysis import AiAnalysis
    from app.models.stock import Stock
    from app.models.tech_signal import TechSignal
    from app.services.kis_api.client import get_current_price
    from app.services.notification.telegram import send_message

    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    async with AsyncSessionLocal() as db:
        # 지난 주 top5 추천 종목 조회
        r = await db.execute(
            select(AiAnalysis, Stock)
            .join(Stock, AiAnalysis.stock_id == Stock.id)
            .where(
                AiAnalysis.is_top5 == 1,
                AiAnalysis.analyzed_at >= one_week_ago,
            )
            .order_by(AiAnalysis.buy_probability.desc())
            .limit(5)
        )
        rows = r.all()

        # 이번 주 신호 발생 건수
        signal_cnt_r = await db.execute(
            select(func.count(TechSignal.id)).where(
                TechSignal.detected_at >= one_week_ago
            )
        )
        total_signals = signal_cnt_r.scalar() or 0

    if not rows:
        msg = "📊 이번 주 AI 추천 데이터가 없습니다.\n(AI 분석이 아직 실행되지 않았습니다.)"
        await send_message(msg)
        return {"sent": False, "reason": "no_data"}

    # 현재가 기준 수익률 계산
    lines = ["📊 <b>AI 주간 성과 리포트</b>\n"]
    total_return = 0.0
    valid_count  = 0

    for ai, stock in rows:
        try:
            price_data = await get_current_price(stock.ticker)
            if not price_data:
                continue

            curr = float(price_data.get("stck_prpr", 0))
            if curr <= 0:
                continue

            # AI 분석 당시 손절가를 진입가 근사값으로 사용
            # (실제 진입가 기록이 없으므로 근사)
            entry = float(ai.stop_loss_price) if ai.stop_loss_price else curr
            ret   = (curr - entry) / entry * 100 if entry > 0 else 0.0

            total_return += ret
            valid_count  += 1

            emoji = "📈" if ret >= 0 else "📉"
            lines.append(
                f"{emoji} <b>{stock.name}</b> ({stock.ticker})\n"
                f"   수익률: <b>{ret:+.1f}%</b>"
                + (f" | 목표가: {float(ai.target_price):,.0f}원"
                   if ai.target_price else "")
            )
        except Exception as e:
            logger.warning("주간리포트 종목 오류 [%s]: %s", stock.ticker, e)

    avg_ret = total_return / valid_count if valid_count else 0.0

    lines.append(f"\n📌 평균 수익률: <b>{avg_ret:+.1f}%</b>")
    lines.append(f"📡 이번 주 신호 발생: <b>{total_signals}건</b>")
    lines.append("\n⚠️ <i>투자 결정 및 손익 책임은 투자자 본인에게 있습니다.</i>")

    await send_message("\n".join(lines))
    return {
        "sent":         True,
        "avg_return":   round(avg_ret, 2),
        "total_signals": total_signals,
        "stocks_checked": valid_count,
    }
