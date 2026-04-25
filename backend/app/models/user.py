# =============================================================
# 회원 테이블 — 사용자 정보를 저장합니다.
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from app.core.database import Base


class UserTier(str, enum.Enum):
    FREE = "free"           # 무료 회원 — 일 1회 AI 추천
    PREMIUM = "premium"     # 프리미엄 — 실시간 + 무제한 알림
    VIP = "vip"             # VIP — 전담 분석


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)

    # 비밀번호는 bcrypt로 암호화해서 저장 (원본 저장 절대 금지)
    password_hash = Column(String(255), nullable=False)

    # OTP 2차 인증 비밀키 (AES256으로 암호화해서 저장)
    otp_secret_encrypted = Column(String(500), nullable=True)
    otp_secret_iv = Column(String(100), nullable=True)
    otp_enabled = Column(Boolean, default=False)

    # 회원 등급
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)

    # 초대코드로 가입한 경우
    invited_by = Column(Integer, nullable=True)   # 초대한 사람의 user_id

    # 계정 상태
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # 시간 기록
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.tier})>"
