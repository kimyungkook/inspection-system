# =============================================================
# 주식 종목 테이블 — 국내/해외 종목 기본 정보를 저장합니다.
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, BigInteger, Numeric
from app.core.database import Base


class StockMarket(str, enum.Enum):
    KR = "KR"    # 국내 (코스피/코스닥)
    US = "US"    # 미국 (나스닥/뉴욕증권거래소)


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)  # 예: 005930, AAPL
    name = Column(String(100), nullable=False)                             # 예: 삼성전자, Apple Inc.
    name_en = Column(String(100), nullable=True)                           # 영문명
    market = Column(Enum(StockMarket), nullable=False)                     # 국내/해외 구분
    sector = Column(String(100), nullable=True)                            # 업종 (예: 반도체, IT)
    market_cap = Column(BigInteger, nullable=True)                         # 시가총액 (원 단위)
    is_active = Column(Boolean, default=True)                              # 상장 여부

    # 최근 시세 (빠른 조회용 캐시)
    last_price = Column(Numeric(15, 2), nullable=True)                     # 최근 종가
    last_updated = Column(DateTime(timezone=True), nullable=True)          # 마지막 업데이트

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Stock {self.ticker} {self.name}>"
