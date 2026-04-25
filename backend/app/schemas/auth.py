# =============================================================
# 인증 관련 API 요청/응답 형식 정의
# 스키마(Schema) = API가 받아야 할 데이터 형식을 미리 정의
# 형식이 맞지 않으면 자동으로 오류를 반환해줌
# =============================================================

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from app.core.security import validate_password_strength


# -------------------------------------------------------
# 회원가입 요청
# -------------------------------------------------------
class SignupRequest(BaseModel):
    username: str           # 아이디 (4~20자)
    email: EmailStr         # 이메일 (형식 자동 검증)
    phone: Optional[str]    # 전화번호 (선택)
    password: str           # 비밀번호
    invite_code: Optional[str] = None  # 초대코드 (없어도 가입 가능)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 4 or len(v) > 20:
            raise ValueError("아이디는 4~20자 사이여야 합니다.")
        if not v.replace("_", "").isalnum():
            raise ValueError("아이디는 영문, 숫자, 밑줄(_)만 사용 가능합니다.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v


# -------------------------------------------------------
# 로그인 요청
# -------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str
    otp_code: Optional[str] = None   # OTP 활성화 계정은 필수


# -------------------------------------------------------
# 토큰 갱신 요청 (자동 로그인 유지)
# -------------------------------------------------------
class RefreshTokenRequest(BaseModel):
    refresh_token: str


# -------------------------------------------------------
# 로그인 성공 응답
# -------------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str       # 15분짜리 단기 토큰
    refresh_token: str      # 7일짜리 장기 토큰
    token_type: str = "bearer"
    user_id: int
    username: str
    tier: str


# -------------------------------------------------------
# 회원 정보 응답
# -------------------------------------------------------
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: Optional[str]
    tier: str
    otp_enabled: bool
    is_active: bool

    model_config = {"from_attributes": True}


# -------------------------------------------------------
# 초대코드 생성 응답
# -------------------------------------------------------
class InviteCodeResponse(BaseModel):
    code: str               # 예: A7K2X9Q1
    expires_in_hours: int   # 만료까지 남은 시간


# -------------------------------------------------------
# 비밀번호 변경 요청
# -------------------------------------------------------
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        ok, msg = validate_password_strength(v)
        if not ok:
            raise ValueError(msg)
        return v


# -------------------------------------------------------
# OTP 설정 요청/응답
# -------------------------------------------------------
class OtpSetupResponse(BaseModel):
    secret: str         # OTP 비밀키
    qr_uri: str         # QR코드용 URI (Google Authenticator 등록용)


class OtpVerifyRequest(BaseModel):
    otp_code: str       # 6자리 숫자 코드
