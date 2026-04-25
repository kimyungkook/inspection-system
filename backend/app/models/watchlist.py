# =============================================================
# 관심종목 테이블 — 사용자가 저장한 종목 목록
# =============================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Numeric
from app.core.database import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)

    # 알림 설정
    alert_on_target_price = Column(Boolean, default=False)    # 목표가 도달 시 알림
    target_price = Column(Numeric(15, 2), nullable=True)       # 목표가

    alert_on_low_price = Column(Boolean, default=False)        # 저점 접근 시 알림
    low_price = Column(Numeric(15, 2), nullable=True)          # 저점 기준가

    alert_on_signal = Column(Boolean, default=True)            # 기술적 신호 알림 (기본 ON)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Watchlist user={self.user_id} stock={self.stock_id}>"
