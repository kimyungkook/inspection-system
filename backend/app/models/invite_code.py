# =============================================================
# 초대코드 테이블 — DB 영구 이력 저장 (Redis는 TTL 관리용)
# =============================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(8), unique=True, nullable=False, index=True)   # 예: A7K2X9Q1
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False) # 생성한 사람
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)     # 사용한 사람

    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)          # 만료 시각 (1시간 후)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<InviteCode {self.code} used={self.is_used}>"
