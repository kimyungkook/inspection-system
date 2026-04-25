# =============================================================
# 기술적 지표 신호 테이블
#
# TechSignal   — 매수/매도 신호 발생 이력 (알림 발송 근거)
# TechIndicator — 각 종목의 최신 지표 값 (RSI, MACD 등)
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum, JSON, Boolean
from app.core.database import Base


class SignalType(str, enum.Enum):
    BUY = "BUY"     # 매수 신호
    SELL = "SELL"   # 매도 신호


class SignalGrade(str, enum.Enum):
    S = "S"   # 강력매수 — 5개+ 지표 동시 발생
    A = "A"   # 매수적기 — 3~4개 지표
    B = "B"   # 매수검토 — 2개 지표
    C = "C"   # 관찰필요 — 1개 지표


# -------------------------------------------------------
# 신호 발생 이력
# -------------------------------------------------------
class TechSignal(Base):
    __tablename__ = "tech_signals"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    signal_type = Column(Enum(SignalType), nullable=False)
    grade = Column(Enum(SignalGrade), nullable=False)

    # 발동된 지표 목록 (JSON)
    # 예: {"RSI": "28(과매도)", "MACD": "골든크로스", "거래량": "320%급증"}
    indicators_triggered = Column(JSON, nullable=False)
    indicator_count = Column(Integer, nullable=False)              # 발동 지표 개수

    price_at_signal = Column(Numeric(15, 2), nullable=False)       # 신호 발생 당시 가격

    # 알림 발송 여부 추적
    alert_sent = Column(Boolean, default=False)
    alerted_at = Column(DateTime(timezone=True), nullable=True)

    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<TechSignal stock={self.stock_id} {self.signal_type} {self.grade}등급>"


# -------------------------------------------------------
# 각 종목의 최신 기술적 지표 값
# 1분/5분마다 Celery Worker가 업데이트
# -------------------------------------------------------
class TechIndicator(Base):
    __tablename__ = "tech_indicators"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    timeframe = Column(String(5), nullable=False)                  # "1m", "5m", "1h"

    # 현재가 / 거래량
    current_price = Column(Numeric(15, 2), nullable=True)
    volume = Column(Numeric(20, 0), nullable=True)
    volume_ratio = Column(Numeric(8, 2), nullable=True)            # 평균 대비 거래량 비율 (%)

    # RSI (과매수/과매도 판단 — 30이하: 과매도 매수기회, 70이상: 과매수 매도기회)
    rsi = Column(Numeric(8, 4), nullable=True)

    # MACD (추세 방향 판단 — 골든크로스: 매수, 데드크로스: 매도)
    macd_line = Column(Numeric(15, 6), nullable=True)
    macd_signal = Column(Numeric(15, 6), nullable=True)
    macd_hist = Column(Numeric(15, 6), nullable=True)

    # 볼린저밴드 (가격 범위 판단 — 하단 터치: 매수, 상단 터치: 매도)
    bb_upper = Column(Numeric(15, 2), nullable=True)
    bb_middle = Column(Numeric(15, 2), nullable=True)
    bb_lower = Column(Numeric(15, 2), nullable=True)

    # 이동평균선 (추세 방향 — 5>20>60 정배열: 상승추세)
    ma5 = Column(Numeric(15, 2), nullable=True)
    ma20 = Column(Numeric(15, 2), nullable=True)
    ma60 = Column(Numeric(15, 2), nullable=True)
    ma120 = Column(Numeric(15, 2), nullable=True)

    # 스토캐스틱 (단기 과매수/과매도)
    stoch_k = Column(Numeric(8, 4), nullable=True)
    stoch_d = Column(Numeric(8, 4), nullable=True)

    # OBV (거래량으로 추세 확인)
    obv = Column(Numeric(20, 2), nullable=True)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<TechIndicator stock={self.stock_id} {self.timeframe} RSI={self.rsi}>"
