"""
가상투자 시뮬레이션 API
- 실제 KIS API 현재가로 가상 매수/매도 처리
- 잔고, 포지션, 거래 이력 관리
"""
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.simulation import SimAccount, SimPosition, SimTrade, TradeType, TradeTrigger
from app.models.stock import Stock
from app.models.user import User
from app.services.kis_api.client import get_current_price

router = APIRouter(prefix="/simulation", tags=["가상투자 시뮬레이션"])


# ── 요청 스키마 ─────────────────────────────────────────────────
class CreateAccountReq(BaseModel):
    name: str = "내 가상계좌"
    initial_balance: float

class TradeReq(BaseModel):
    ticker: str
    trade_type: str          # "buy" or "sell"
    quantity: int
    trigger: str = "MANUAL"  # MANUAL / AI_SIGNAL / TECH_SIGNAL


# ── 응답 직렬화 헬퍼 ────────────────────────────────────────────
def _acct_out(a: SimAccount) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "virtual_balance":  float(a.virtual_balance),
        "initial_balance":  float(a.initial_balance),
        "total_invested":   float(a.total_invested or 0),
        "total_profit_loss":float(a.total_profit_loss or 0),
        "profit_rate":      float(a.profit_rate or 0),
    }

def _pos_out(p: SimPosition, ticker: str, name: str) -> dict:
    return {
        "id": p.id,
        "account_id":         p.account_id,
        "ticker":             ticker,
        "name":               name,
        "quantity":           p.quantity,
        "avg_buy_price":      float(p.avg_buy_price),
        "current_price":      float(p.current_price) if p.current_price else None,
        "unrealized_pnl":     float(p.unrealized_pnl or 0),
        "unrealized_pnl_rate":float(p.unrealized_pnl_rate or 0),
        "ai_signal_grade":    p.ai_signal_grade,
        "ai_buy_probability": p.ai_buy_probability,
        "stop_loss_price":    float(p.stop_loss_price) if p.stop_loss_price else None,
        "take_profit_price":  float(p.take_profit_price) if p.take_profit_price else None,
    }


# ── 계좌 조회 ───────────────────────────────────────────────────
@router.get("/accounts")
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SimAccount).where(SimAccount.user_id == current_user.id,
                                 SimAccount.is_active == True))
    accounts = result.scalars().all()
    return [_acct_out(a) for a in accounts]


# ── 계좌 개설 ───────────────────────────────────────────────────
@router.post("/accounts", status_code=status.HTTP_201_CREATED)
async def create_account(
    body: CreateAccountReq,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.initial_balance < 100_000:
        raise HTTPException(400, "최소 10만원 이상 설정해야 합니다.")
    if body.initial_balance > 1_000_000_000:
        raise HTTPException(400, "최대 10억원까지 설정 가능합니다.")

    acct = SimAccount(
        user_id=current_user.id,
        name=body.name,
        virtual_balance=Decimal(str(body.initial_balance)),
        initial_balance=Decimal(str(body.initial_balance)),
    )
    db.add(acct)
    await db.commit()
    await db.refresh(acct)
    return _acct_out(acct)


# ── 포지션 조회 ─────────────────────────────────────────────────
@router.get("/positions")
async def list_positions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 사용자 계좌 조회
    acct_result = await db.execute(
        select(SimAccount).where(SimAccount.user_id == current_user.id,
                                 SimAccount.is_active == True))
    acct = acct_result.scalars().first()
    if not acct:
        return []

    pos_result = await db.execute(
        select(SimPosition, Stock)
        .join(Stock, SimPosition.stock_id == Stock.id)
        .where(SimPosition.account_id == acct.id, SimPosition.quantity > 0))
    rows = pos_result.all()

    # 실시간 가격으로 평가손익 업데이트
    result = []
    for pos, stock in rows:
        price_data = await get_current_price(stock.ticker)
        if price_data:
            curr = Decimal(str(price_data.get("stck_prpr", 0)))
            pnl = (curr - pos.avg_buy_price) * pos.quantity
            rate = float((curr - pos.avg_buy_price) / pos.avg_buy_price * 100)
            await db.execute(
                update(SimPosition)
                .where(SimPosition.id == pos.id)
                .values(current_price=curr, unrealized_pnl=pnl,
                        unrealized_pnl_rate=Decimal(str(rate))))
            pos.current_price = curr
            pos.unrealized_pnl = pnl
            pos.unrealized_pnl_rate = Decimal(str(rate))
        result.append(_pos_out(pos, stock.ticker, stock.name))

    await db.commit()
    return result


# ── 매수/매도 체결 ───────────────────────────────────────────────
@router.post("/trades", status_code=status.HTTP_201_CREATED)
async def execute_trade(
    body: TradeReq,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.quantity <= 0:
        raise HTTPException(400, "수량은 1 이상이어야 합니다.")

    # 계좌 조회
    acct_result = await db.execute(
        select(SimAccount).where(SimAccount.user_id == current_user.id,
                                 SimAccount.is_active == True))
    acct = acct_result.scalars().first()
    if not acct:
        raise HTTPException(404, "가상계좌가 없습니다. 먼저 계좌를 개설하세요.")

    # 종목 조회 (없으면 자동 생성)
    stock_result = await db.execute(
        select(Stock).where(Stock.ticker == body.ticker))
    stock = stock_result.scalars().first()
    if not stock:
        stock = Stock(ticker=body.ticker, name=body.ticker, market="KR")
        db.add(stock)
        await db.flush()

    # 실제 현재가 조회
    price_data = await get_current_price(body.ticker)
    if not price_data:
        raise HTTPException(503, f"'{body.ticker}' 현재가를 조회할 수 없습니다. 종목 코드를 확인하세요.")

    curr_price = Decimal(str(price_data.get("stck_prpr", 0)))
    if curr_price <= 0:
        raise HTTPException(503, "현재가 조회 실패. 잠시 후 다시 시도하세요.")

    total = curr_price * body.quantity
    trade_type = body.trade_type.upper()

    if trade_type == "BUY":
        return await _buy(db, acct, stock, body.quantity, curr_price, total, body.trigger)
    elif trade_type == "SELL":
        return await _sell(db, acct, stock, body.quantity, curr_price, total, body.trigger)
    else:
        raise HTTPException(400, "trade_type은 'buy' 또는 'sell'만 가능합니다.")


async def _buy(db, acct, stock, quantity, price, total, trigger_str):
    if acct.virtual_balance < total:
        raise HTTPException(400,
            f"잔고 부족. 필요: {int(total):,}원 / 현재: {int(acct.virtual_balance):,}원")

    # 잔고 차감
    acct.virtual_balance -= total

    # 기존 포지션 확인 (평균단가 계산)
    pos_result = await db.execute(
        select(SimPosition).where(
            SimPosition.account_id == acct.id,
            SimPosition.stock_id == stock.id))
    pos = pos_result.scalars().first()

    if pos:
        # 추가 매수: 평균단가 재계산
        new_qty = pos.quantity + quantity
        new_avg = (pos.avg_buy_price * pos.quantity + price * quantity) / new_qty
        pos.quantity = new_qty
        pos.avg_buy_price = new_avg
    else:
        pos = SimPosition(
            account_id=acct.id,
            stock_id=stock.id,
            quantity=quantity,
            avg_buy_price=price,
            current_price=price,
        )
        db.add(pos)

    trade = SimTrade(
        account_id=acct.id,
        stock_id=stock.id,
        trade_type=TradeType.BUY,
        quantity=quantity,
        price=price,
        total_amount=total,
        trigger=TradeTrigger[trigger_str] if trigger_str in TradeTrigger.__members__ else TradeTrigger.MANUAL,
    )
    db.add(trade)
    await db.commit()
    return {"result": "매수 완료", "ticker": stock.ticker,
            "quantity": quantity, "price": float(price), "total": float(total)}


async def _sell(db, acct, stock, quantity, price, total, trigger_str):
    pos_result = await db.execute(
        select(SimPosition).where(
            SimPosition.account_id == acct.id,
            SimPosition.stock_id == stock.id))
    pos = pos_result.scalars().first()

    if not pos or pos.quantity < quantity:
        have = pos.quantity if pos else 0
        raise HTTPException(400, f"보유수량 부족. 보유: {have}주 / 매도 요청: {quantity}주")

    # 확정 손익 계산
    realized = (price - pos.avg_buy_price) * quantity
    rate = float((price - pos.avg_buy_price) / pos.avg_buy_price * 100)

    # 잔고 증가, 포지션 감소
    acct.virtual_balance += total
    acct.total_profit_loss = (acct.total_profit_loss or Decimal(0)) + realized
    init = acct.initial_balance
    acct.profit_rate = Decimal(str(
        float((acct.total_profit_loss) / init * 100)))

    pos.quantity -= quantity
    if pos.quantity == 0:
        await db.delete(pos)

    trade = SimTrade(
        account_id=acct.id,
        stock_id=stock.id,
        trade_type=TradeType.SELL,
        quantity=quantity,
        price=price,
        total_amount=total,
        realized_pnl=realized,
        realized_pnl_rate=Decimal(str(rate)),
        trigger=TradeTrigger[trigger_str] if trigger_str in TradeTrigger.__members__ else TradeTrigger.MANUAL,
    )
    db.add(trade)
    await db.commit()
    return {"result": "매도 완료", "ticker": stock.ticker,
            "quantity": quantity, "price": float(price),
            "realized_pnl": float(realized), "rate": round(rate, 2)}


# ── 거래 이력 조회 ───────────────────────────────────────────────
@router.get("/trades")
async def list_trades(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acct_result = await db.execute(
        select(SimAccount).where(SimAccount.user_id == current_user.id,
                                 SimAccount.is_active == True))
    acct = acct_result.scalars().first()
    if not acct:
        return []

    result = await db.execute(
        select(SimTrade, Stock)
        .join(Stock, SimTrade.stock_id == Stock.id)
        .where(SimTrade.account_id == acct.id)
        .order_by(SimTrade.traded_at.desc())
        .limit(limit))
    return [{
        "id":           t.id,
        "ticker":       s.ticker,
        "name":         s.name,
        "trade_type":   t.trade_type.value,
        "quantity":     t.quantity,
        "price":        float(t.price),
        "total_amount": float(t.total_amount),
        "realized_pnl": float(t.realized_pnl) if t.realized_pnl else None,
        "trigger":      t.trigger.value,
        "traded_at":    t.traded_at.isoformat(),
    } for t, s in result.all()]
