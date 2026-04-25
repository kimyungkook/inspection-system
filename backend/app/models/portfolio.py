# =============================================================
# 실투자 포트폴리오 테이블 — 실제 보유 종목 관리
# (자산평가 탭에서 사용 — KB증권에서 실제 매매한 종목 기록)
# =============================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)

    quantity = Column(Integer, nullable=False)                  # 보유 수량
    avg_buy_price = Column(Numeric(15, 2), nullable=False)      # 평균 매수가

    # 매수 당시 AI 신호 정보 (나중에 AI 성과 분석에 활용)
    ai_signal_grade = Column(String(2), nullable=True)          # S/A/B/C
    ai_buy_probability = Column(Integer, nullable=True)         # 매수 확률 (%)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Portfolio user={self.user_id} stock={self.stock_id} qty={self.quantity}>"
