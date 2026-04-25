"""
가상투자 포지션 평가 태스크 — 매일 16:00 자동 실행

evaluate_positions:
  - 모든 가상 보유 포지션의 현재가로 평가손익 재계산
  - 손절가 도달 → 자동 매도 처리
  - 목표가 도달 → 자동 매도 처리
  - 계좌 전체 수익률 업데이트
"""

import asyncio
import logging
from decimal import Decimal
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def evaluate_positions(self):
    """[매일 16:00, 평일] 전체 가상 포지션 평가 + 자동 청산 처리"""
    try:
        result = asyncio.run(_evaluate_async())
        logger.info(
            "포지션평가 완료 | 평가:%d 자동청산:%d 오류:%d",
            result["evaluated"],
            result["auto_closed"],
            result["errors"],
        )
        return result
    except Exception as exc:
        logger.error("포지션평가 태스크 오류: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=120)


async def _evaluate_async() -> dict:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.simulation import SimAccount, SimPosition, SimTrade, TradeType, TradeTrigger
    from app.models.stock import Stock
    from app.services.kis_api.client import get_current_price

    evaluated  = 0
    auto_closed = 0
    errors     = 0

    async with AsyncSessionLocal() as db:
        # 활성 계좌의 전체 보유 포지션 조회
        r = await db.execute(
            select(SimPosition, Stock, SimAccount)
            .join(Stock,      SimPosition.stock_id    == Stock.id)
            .join(SimAccount, SimPosition.account_id  == SimAccount.id)
            .where(
                SimPosition.quantity  >  0,
                SimAccount.is_active.is_(True),
            )
        )
        rows = r.all()

        for pos, stock, acct in rows:
            try:
                # 실제 현재가 조회
                price_data = await get_current_price(stock.ticker)
                if not price_data:
                    continue

                curr = Decimal(str(price_data.get("stck_prpr", 0)))
                if curr <= 0:
                    continue

                # 평가손익 갱신
                pnl  = (curr - pos.avg_buy_price) * pos.quantity
                rate = float(
                    (curr - pos.avg_buy_price) / pos.avg_buy_price * 100
                )
                pos.current_price       = curr
                pos.unrealized_pnl      = pnl
                pos.unrealized_pnl_rate = Decimal(str(round(rate, 4)))
                evaluated += 1

                # 손절가 도달 → 자동 청산
                if pos.stop_loss_price and curr <= pos.stop_loss_price:
                    await _auto_close(
                        db, pos, acct, stock, curr, TradeTrigger.STOP_LOSS
                    )
                    auto_closed += 1
                    continue

                # 목표가 도달 → 자동 청산
                if pos.take_profit_price and curr >= pos.take_profit_price:
                    await _auto_close(
                        db, pos, acct, stock, curr, TradeTrigger.TAKE_PROFIT
                    )
                    auto_closed += 1
                    continue

            except Exception as e:
                logger.error(
                    "[%s] 포지션 평가 오류: %s", stock.ticker, e, exc_info=True
                )
                errors += 1

        await db.commit()

    return {
        "evaluated":  evaluated,
        "auto_closed": auto_closed,
        "errors":     errors,
    }


async def _auto_close(
    db,
    pos:     "SimPosition",
    acct:    "SimAccount",
    stock:   "Stock",
    curr:    Decimal,
    trigger: "TradeTrigger",
) -> None:
    """손절가 또는 목표가 도달 시 자동 전량 매도 처리"""
    from app.models.simulation import SimTrade, TradeType

    total    = curr * pos.quantity
    realized = (curr - pos.avg_buy_price) * pos.quantity
    rate     = Decimal(str(
        float((curr - pos.avg_buy_price) / pos.avg_buy_price * 100)
    ))

    # 1. 잔고 증가
    acct.virtual_balance  = (acct.virtual_balance or Decimal(0)) + total

    # 2. 누적 확정 손익 갱신
    acct.total_profit_loss = (acct.total_profit_loss or Decimal(0)) + realized

    # 3. 전체 수익률 갱신 (초기 자금 대비)
    if acct.initial_balance and acct.initial_balance > 0:
        acct.profit_rate = Decimal(str(
            float(acct.total_profit_loss / acct.initial_balance * 100)
        ))

    # 4. 체결 이력 저장
    trade = SimTrade(
        account_id    = acct.id,
        stock_id      = pos.stock_id,
        trade_type    = TradeType.SELL,
        quantity      = pos.quantity,
        price         = curr,
        total_amount  = total,
        realized_pnl  = realized,
        realized_pnl_rate = rate,
        trigger       = trigger,
    )
    db.add(trade)

    # 5. 포지션 제거
    await db.delete(pos)

    label = "손절가" if trigger == trigger.STOP_LOSS else "목표가"
    logger.info(
        "자동청산: %s %s 도달 | 가격:%s 손익:%+.0f원",
        stock.ticker, label, curr, float(realized),
    )
