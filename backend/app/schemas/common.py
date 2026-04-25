# =============================================================
# 공통 응답 형식
# 모든 API 응답을 동일한 구조로 통일합니다.
# =============================================================

from pydantic import BaseModel
from typing import Any, Optional


class SuccessResponse(BaseModel):
    """성공 응답"""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """오류 응답"""
    success: bool = False
    message: str
    detail: Optional[str] = None
