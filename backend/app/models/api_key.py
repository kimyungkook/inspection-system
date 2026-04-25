# =============================================================
# API 키 저장 테이블 — 사용자의 API 키를 AES256으로 암호화해 저장
# =============================================================

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from app.core.database import Base


class ApiProvider(str, enum.Enum):
    KIS = "kis"           # 한국투자증권
    CLAUDE = "claude"     # Claude AI
    OPENAI = "openai"     # OpenAI
    GEMINI = "gemini"     # Google Gemini


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(Enum(ApiProvider), nullable=False)

    # API 키 원본은 절대 저장하지 않음 — AES256 암호화 후 저장
    encrypted_key = Column(String(1000), nullable=False)   # 암호화된 API 키
    iv = Column(String(100), nullable=False)               # 복호화에 필요한 초기벡터

    # 한국투자증권 전용 추가 필드
    encrypted_secret = Column(String(1000), nullable=True)   # 앱시크릿 암호화
    iv_secret = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ApiKey user={self.user_id} provider={self.provider}>"
