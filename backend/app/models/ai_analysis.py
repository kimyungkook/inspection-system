# =============================================================
# AI 분석 결과 테이블 — AI가 종목을 분석한 결과를 저장합니다.
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, Enum, JSON
from app.core.database import Base


class Recommendation(str, enum.Enum):
    STRONG_BUY = "strong_buy"   # 강력 매수
    BUY = "buy"                 # 매수
    HOLD = "hold"               # 관망
    SELL = "sell"               # 매도


class AiAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # AI 분석 결과
    recommendation = Column(Enum(Recommendation), nullable=False)
    buy_probability = Column(Integer, nullable=False)           # 매수 확률 0~100
    target_price = Column(Numeric(15, 2), nullable=True)        # AI 예측 목표가
    stop_loss_price = Column(Numeric(15, 2), nullable=True)     # 권장 손절가
    expected_period_days = Column(Integer, nullable=True)       # 예상 도달 기간 (일)

    # AI 설명 (한글)
    buy_reason = Column(Text, nullable=True)                    # 매수 이유 3문장
    risk_reason = Column(Text, nullable=True)                   # 주요 리스크 2문장
    one_line_summary = Column(String(200), nullable=True)       # 초보자용 한 줄 요약

    # 4대 Factor 점수 (각 0~100)
    factor_scores = Column(JSON, nullable=True)
    # 예시: {"재무성장성": 85, "경쟁우위": 72, "밸류에이션": 68, "투자자프로필": 90}

    # 사용된 AI 모델
    llm_model = Column(String(50), nullable=True)               # 예: claude-sonnet-4-6

    # 1차 필터 30종목에 포함됐는지, 최종 5종목인지
    is_top30 = Column(Integer, default=0)                       # 1차 필터 통과
    is_top5 = Column(Integer, default=0)                        # 최종 추천 5종목

    analyzed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self):
        return f"<AiAnalysis stock={self.stock_id} rec={self.recommendation} prob={self.buy_probability}%>"
