# =============================================================
# 알림 테이블
#
# AlertSetting — 사용자별 알림 채널/조건 설정
# AlertLog     — 실제 발송된 알림 이력
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from app.core.database import Base


class AlertChannel(str, enum.Enum):
    PUSH = "push"           # 앱 푸시 알림 (FCM)
    TELEGRAM = "telegram"   # 텔레그램 봇
    KAKAO = "kakao"         # 카카오톡 알림톡


class AlertType(str, enum.Enum):
    BUY_SIGNAL = "buy_signal"           # 매수 신호
    SELL_SIGNAL = "sell_signal"         # 매도 신호
    TARGET_PRICE = "target_price"       # 목표가 도달
    STOP_LOSS = "stop_loss"             # 손절가 도달
    AI_RECOMMEND = "ai_recommend"       # AI 일일 추천
    PORTFOLIO = "portfolio"             # 포트폴리오 리밸런싱


# -------------------------------------------------------
# 사용자 알림 설정
# -------------------------------------------------------
class AlertSetting(Base):
    __tablename__ = "alert_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 사용할 알림 채널
    channel = Column(Enum(AlertChannel), nullable=False, default=AlertChannel.TELEGRAM)

    # 어떤 알림을 받을지
    receive_buy_signal = Column(Boolean, default=True)
    receive_sell_signal = Column(Boolean, default=True)
    receive_target_price = Column(Boolean, default=True)
    receive_stop_loss = Column(Boolean, default=True)
    receive_ai_recommend = Column(Boolean, default=True)

    # 최소 등급 설정 (S만 받기 / A이상 받기 등)
    min_signal_grade = Column(String(2), default="A")   # S / A / B / C

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# -------------------------------------------------------
# 알림 발송 이력
# -------------------------------------------------------
class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=True)

    alert_type = Column(Enum(AlertType), nullable=False)
    channel = Column(Enum(AlertChannel), nullable=False)
    grade = Column(String(2), nullable=True)          # 신호 등급 S/A/B/C

    message = Column(Text, nullable=False)            # 실제 발송된 메시지 내용
    is_sent = Column(Boolean, default=False)          # 발송 성공 여부
    error_message = Column(Text, nullable=True)       # 실패 시 오류 내용

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
