"""
기술적 신호 감지 작업 — 1분/5분마다 Celery 자동 실행

detect_all_signals : 1분마다 신호 감지 → 알림 태스크 큐 등록
update_tech_indicators : 5분마다 지표 값 DB 저장 (앱 차트 표시용)

Celery ↔ async 연동 패턴:
    asyncio.run()으로 새 이벤트루프를 생성해서 실행
    (get_event_loop().run_until_complete는 Python 3.10+ 이후 권장하지 않음)
"""

import asyncio
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# 공통 헬퍼: 모니터링 대상 종목 수집
# ─────────────────────────────────────────────────────────────

async def _get_monitored_tickers(db) -> dict[str, int]:
    """
    모니터링 대상 종목 수집 → {ticker: stock_id}

    수집 대상:
      ① 전체 사용자 관심종목 (watchlist)
      ② 가상투자 보유 중인 종목 (sim_positions, quantity > 0)
      ③ AI 최근 추천 top5
    """
    from sqlalchemy import select
    from app.models.stock import Stock
    from app.models.watchlist import Watchlist
    from app.models.simulation import SimPosition, SimAccount
    from app.models.ai_analysis import AiAnalysis

    ticker_map: dict[str, int] = {}

    # ① 관심종목
    r = await db.execute(
        select(Stock.ticker, Stock.id)
        .join(Watchlist, Watchlist.stock_id == Stock.id)
    )
    for ticker, sid in r.all():
        ticker_map[ticker] = sid

    # ② 가상투자 보유 종목
    r = await db.execute(
        select(Stock.ticker, Stock.id)
        .join(SimPosition, SimPosition.stock_id == Stock.id)
        .join(SimAccount, SimPosition.account_id == SimAccount.id)
        .where(SimPosition.quantity > 0, SimAccount.is_active.is_(True))
    )
    for ticker, sid in r.all():
        ticker_map[ticker] = sid

    # ③ AI 최근 top5
    r = await db.execute(
        select(Stock.ticker, Stock.id)
        .join(AiAnalysis, AiAnalysis.stock_id == Stock.id)
        .where(AiAnalysis.is_top5 == 1)
        .order_by(AiAnalysis.analyzed_at.desc())
        .limit(5)
    )
    for ticker, sid in r.all():
        ticker_map[ticker] = sid

    return ticker_map


# ─────────────────────────────────────────────────────────────
# Celery 태스크 1: 기술적 신호 감지
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def detect_all_signals(self):
    """[1분마다, 평일 09~15시] 전체 모니터링 종목 기술적 신호 감지"""
    try:
        result = asyncio.run(_detect_async())
        logger.info(
            "신호감지 완료 | 종목:%d 신호:%d 오류:%d",
            result["tickers_checked"],
            result["signals_found"],
            result["errors"],
        )
        return result
    except Exception as exc:
        logger.error("신호감지 태스크 오류: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=30)


async def _detect_async() -> dict:
    from decimal import Decimal
    from app.core.database import AsyncSessionLocal
    from app.core.redis_client import (
        is_signal_already_alerted,
        mark_signal_alerted,
    )
    from app.services.kis_api.client import get_minute_candles, get_current_price
    from app.services.tech_engine.indicator_calculator import calculate
    from app.services.tech_engine.signal_detector import (
        detect_buy_signal,
        detect_sell_signal,
    )
    from app.models.tech_signal import TechSignal, SignalType, SignalGrade

    signals_found = 0
    tickers_checked = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        ticker_map = await _get_monitored_tickers(db)
        if not ticker_map:
            return {"signals_found": 0, "tickers_checked": 0, "errors": 0}

        for ticker, stock_id in ticker_map.items():
            tickers_checked += 1
            try:
                # 1분봉 데이터 (최소 30봉 필요)
                df = await get_minute_candles(ticker, time_div="1")
                if df is None or len(df) < 30:
                    continue

                # 지표 계산
                ind = calculate(df, ticker)
                if ind is None:
                    continue

                # 실제 현재가
                price_data = await get_current_price(ticker)
                if not price_data:
                    continue
                curr_price = float(price_data.get("stck_prpr", 0))
                if curr_price <= 0:
                    continue

                # 매수/매도 신호 순차 감지
                for detect_fn in (detect_buy_signal, detect_sell_signal):
                    signal = detect_fn(ind)
                    if signal is None:
                        continue

                    # 1시간 이내 동일 종목·타입·등급 중복 방지
                    if await is_signal_already_alerted(
                        stock_id, signal.type, signal.grade
                    ):
                        continue

                    # DB 저장
                    ts = TechSignal(
                        stock_id=stock_id,
                        signal_type=SignalType[signal.type],
                        grade=SignalGrade[signal.grade],
                        indicators_triggered=signal.triggers,
                        indicator_count=signal.count,
                        price_at_signal=Decimal(str(curr_price)),
                    )
                    db.add(ts)
                    await db.flush()  # id 확정

                    # B등급 이상만 알림 발송
                    if signal.grade in ("S", "A", "B"):
                        # 순환임포트 방지 — 함수 내부에서 import
                        from app.workers.tasks.alert_tasks import send_signal_alert

                        send_signal_alert.delay(
                            stock_id=stock_id,
                            signal_type=signal.type,
                            grade=signal.grade,
                            indicators=signal.triggers,
                            price=curr_price,
                        )
                        ts.alert_sent = True
                        await mark_signal_alerted(
                            stock_id, signal.type, signal.grade
                        )

                    signals_found += 1

            except Exception as e:
                logger.error("[%s] 신호 감지 오류: %s", ticker, e, exc_info=True)
                errors += 1

        await db.commit()

    return {
        "signals_found": signals_found,
        "tickers_checked": tickers_checked,
        "errors": errors,
    }


# ─────────────────────────────────────────────────────────────
# Celery 태스크 2: 기술적 지표 DB 저장 (5분마다)
# ─────────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3)
def update_tech_indicators(self):
    """[5분마다, 평일 09~15시] 전체 모니터링 종목 지표 값 DB 갱신"""
    try:
        result = asyncio.run(_update_indicators_async())
        logger.info(
            "지표업데이트 완료 | 업데이트:%d 오류:%d",
            result["updated"],
            result["errors"],
        )
        return result
    except Exception as exc:
        logger.error("지표업데이트 태스크 오류: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=60)


async def _update_indicators_async() -> dict:
    from decimal import Decimal
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.services.kis_api.client import get_minute_candles
    from app.services.tech_engine.indicator_calculator import calculate
    from app.models.tech_signal import TechIndicator

    updated = 0
    errors = 0

    def _dec(v):
        """float → Decimal 변환. None이면 None 반환."""
        return Decimal(str(round(v, 6))) if v is not None else None

    async with AsyncSessionLocal() as db:
        ticker_map = await _get_monitored_tickers(db)

        for ticker, stock_id in ticker_map.items():
            try:
                # 5분봉 데이터
                df = await get_minute_candles(ticker, time_div="5")
                if df is None or len(df) < 30:
                    continue

                ind = calculate(df, ticker)
                if ind is None:
                    continue

                # 기존 레코드 조회 (없으면 신규 생성 — upsert)
                r = await db.execute(
                    select(TechIndicator).where(
                        TechIndicator.stock_id == stock_id,
                        TechIndicator.timeframe == "5m",
                    )
                )
                ti = r.scalar_one_or_none()

                now = datetime.now(timezone.utc)
                field_values = dict(
                    rsi=_dec(ind.rsi),
                    macd_line=_dec(ind.macd_line),
                    macd_signal=_dec(ind.macd_signal),
                    macd_hist=_dec(ind.macd_hist),
                    bb_upper=_dec(ind.bb_upper),
                    bb_middle=_dec(ind.bb_middle),
                    bb_lower=_dec(ind.bb_lower),
                    ma5=_dec(ind.ma5),
                    ma20=_dec(ind.ma20),
                    ma60=_dec(ind.ma60),
                    ma120=_dec(ind.ma120),
                    stoch_k=_dec(ind.stoch_k),
                    stoch_d=_dec(ind.stoch_d),
                    obv=_dec(ind.obv),
                    volume_ratio=_dec(ind.volume_ratio),
                    updated_at=now,
                )

                if ti:
                    for k, v in field_values.items():
                        setattr(ti, k, v)
                else:
                    ti = TechIndicator(
                        stock_id=stock_id,
                        timeframe="5m",
                        **field_values,
                    )
                    db.add(ti)

                updated += 1

            except Exception as e:
                logger.error("[%s] 지표 업데이트 오류: %s", ticker, e, exc_info=True)
                errors += 1

        await db.commit()

    return {"updated": updated, "errors": errors}
