# =============================================================
# 가상투자 시뮬레이션 테이블
#
# 핵심 원칙:
#   돈 = 가상 / 종목 = 실제 / 시세 = 실시간 연동 / 수익률 = 실제와 동일
#
# 테이블 3개:
#   SimAccount  — 가상계좌 (잔고, 수익률 관리)
#   SimPosition — 현재 보유 중인 가상 포지션
#   SimTrade    — 전체 가상 체결 이력
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Enum, Text
from app.core.database import Base


class TradeType(str, enum.Enum):
    BUY = "BUY"     # 매수
    SELL = "SELL"   # 매도


class TradeTrigger(str, enum.Enum):
    AI_SIGNAL = "AI_SIGNAL"         # AI 추천 신호로 매수/매도
    TECH_SIGNAL = "TECH_SIGNAL"     # 기술적 지표 신호로 매수/매도
    MANUAL = "MANUAL"               # 사용자 직접 판단
    STOP_LOSS = "STOP_LOSS"         # 손절 자동 실행
    TAKE_PROFIT = "TAKE_PROFIT"     # 목표가 도달 자동 매도


# -------------------------------------------------------
# 가상계좌
# -------------------------------------------------------
class SimAccount(Base):
    __tablename__ = "sim_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), default="내 가상계좌")

    virtual_balance = Column(Numeric(20, 2), nullable=False)     # 현재 가상 현금 잔고
    initial_balance = Column(Numeric(20, 2), nullable=False)     # 최초 설정 금액
    total_invested = Column(Numeric(20, 2), default=0)           # 현재 투자 중인 금액 합계
    total_profit_loss = Column(Numeric(20, 2), default=0)        # 누적 확정 손익
    profit_rate = Column(Numeric(8, 4), default=0)               # 전체 수익률 (%)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SimAccount user={self.user_id} balance={self.virtual_balance}>"


# -------------------------------------------------------
# 가상 보유 포지션 (현재 매수 중인 종목)
# -------------------------------------------------------
class SimPosition(Base):
    __tablename__ = "sim_positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("sim_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)

    quantity = Column(Integer, nullable=False)                    # 보유 수량
    avg_buy_price = Column(Numeric(15, 2), nullable=False)        # 평균 매수가 (체결 당시 실제 시세)
    current_price = Column(Numeric(15, 2), nullable=True)         # 현재가 (실시간 업데이트)
    unrealized_pnl = Column(Numeric(15, 2), default=0)           # 평가 손익 (미확정)
    unrealized_pnl_rate = Column(Numeric(8, 4), default=0)       # 평가 손익률 (%)

    # 매수 당시 AI/기술적 신호 정보
    ai_signal_grade = Column(String(2), nullable=True)            # S/A/B/C
    ai_buy_probability = Column(Integer, nullable=True)           # AI 매수 확률 (%)
    tech_signals = Column(Text, nullable=True)                    # 발동된 기술적 지표 목록 (JSON)

    # 손절/목표가 자동 설정
    stop_loss_price = Column(Numeric(15, 2), nullable=True)       # 손절가
    take_profit_price = Column(Numeric(15, 2), nullable=True)     # 목표가

    bought_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SimPosition account={self.account_id} stock={self.stock_id} qty={self.quantity}>"


# -------------------------------------------------------
# 가상 체결 이력 (전체 매수/매도 기록)
# -------------------------------------------------------
class SimTrade(Base):
    __tablename__ = "sim_trades"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("sim_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)

    trade_type = Column(Enum(TradeType), nullable=False)          # 매수/매도
    quantity = Column(Integer, nullable=False)                    # 체결 수량
    price = Column(Numeric(15, 2), nullable=False)                # 체결가 (실제 현재 시세)
    total_amount = Column(Numeric(20, 2), nullable=False)         # 총 금액

    # 매도 시 확정 손익
    realized_pnl = Column(Numeric(15, 2), nullable=True)          # 확정 손익 금액
    realized_pnl_rate = Column(Numeric(8, 4), nullable=True)      # 확정 손익률 (%)

    trigger = Column(Enum(TradeTrigger), default=TradeTrigger.MANUAL)  # 매매 이유

    traded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<SimTrade {self.trade_type} stock={self.stock_id} price={self.price}>"
