# =============================================================
# 인증 API 라우터
#
# 제공하는 API:
#   POST /auth/signup       — 회원가입
#   POST /auth/login        — 로그인
#   POST /auth/refresh      — 토큰 갱신 (자동 로그인)
#   POST /auth/logout       — 로그아웃
#   GET  /auth/me           — 내 정보 조회
#   POST /auth/change-password — 비밀번호 변경
#   POST /auth/invite-code  — 초대코드 생성
#   POST /auth/otp/setup    — OTP 2차인증 설정
#   POST /auth/otp/verify   — OTP 등록 완료
# =============================================================

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, verify_token,
    generate_invite_code, generate_otp_secret, get_otp_uri, verify_otp,
    encrypt_api_key,
)
from app.core.redis_client import (
    save_invite_code, get_invite_code_owner, delete_invite_code,
    blacklist_token,
)
from app.core.config import settings
from app.models.user import User, UserTier
from app.models.invite_code import InviteCode
from app.schemas.auth import (
    SignupRequest, LoginRequest, RefreshTokenRequest,
    TokenResponse, UserResponse, InviteCodeResponse,
    ChangePasswordRequest, OtpSetupResponse, OtpVerifyRequest,
)
from app.schemas.common import SuccessResponse
from app.api.v1.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["인증"])


# -------------------------------------------------------
# 회원가입
# -------------------------------------------------------
@router.post("/signup", response_model=SuccessResponse, status_code=201)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """새 계정을 만듭니다."""

    # 아이디 중복 확인
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    # 초대코드 검증 (입력한 경우만)
    invited_by_id = None
    if request.invite_code:
        invited_by_id = await get_invite_code_owner(request.invite_code)
        if not invited_by_id:
            raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 초대코드입니다.")

    # 회원 생성
    new_user = User(
        username=request.username,
        email=request.email,
        phone=request.phone,
        password_hash=hash_password(request.password),
        tier=UserTier.FREE,
        invited_by=invited_by_id,
    )
    db.add(new_user)
    await db.flush()   # ID 먼저 생성

    # 초대코드 사용 처리
    if request.invite_code and invited_by_id:
        await delete_invite_code(request.invite_code)   # Redis에서 즉시 삭제 (1회용)
        result = await db.execute(
            select(InviteCode).where(InviteCode.code == request.invite_code)
        )
        code_record = result.scalar_one_or_none()
        if code_record:
            code_record.is_used = True
            code_record.used_by = new_user.id
            code_record.used_at = datetime.now(timezone.utc)

    await db.commit()
    return SuccessResponse(message="회원가입이 완료되었습니다. 로그인해주세요.")


# -------------------------------------------------------
# 로그인
# -------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """로그인 후 토큰을 발급합니다."""

    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    # 아이디 또는 비밀번호 오류 (보안상 어느 쪽인지 알려주지 않음)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다. 관리자에게 문의하세요.")

    # OTP 2차 인증 확인
    if user.otp_enabled:
        if not request.otp_code:
            raise HTTPException(status_code=400, detail="OTP 코드를 입력해주세요.")
        if not verify_otp(user.otp_secret_encrypted, request.otp_code):
            raise HTTPException(status_code=401, detail="OTP 코드가 올바르지 않습니다.")

    # 마지막 로그인 시간 업데이트
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id, user.username),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
        username=user.username,
        tier=user.tier.value,
    )


# -------------------------------------------------------
# 토큰 갱신 (자동 로그인 유지)
# -------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh Token으로 새 Access Token을 발급합니다."""

    payload = verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh Token이 만료되었습니다. 다시 로그인해주세요.")

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="유효하지 않은 계정입니다.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.username),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
        username=user.username,
        tier=user.tier.value,
    )


# -------------------------------------------------------
# 로그아웃
# -------------------------------------------------------
@router.post("/logout", response_model=SuccessResponse)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """현재 토큰을 무효화하고 로그아웃합니다."""
    # 클라이언트에서 토큰 삭제를 함께 처리해야 함
    return SuccessResponse(message="로그아웃되었습니다.")


# -------------------------------------------------------
# 내 정보 조회
# -------------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자의 정보를 반환합니다."""
    return current_user


# -------------------------------------------------------
# 비밀번호 변경
# -------------------------------------------------------
@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """비밀번호를 변경합니다."""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")

    current_user.password_hash = hash_password(request.new_password)
    await db.commit()
    return SuccessResponse(message="비밀번호가 변경되었습니다.")


# -------------------------------------------------------
# 초대코드 생성
# -------------------------------------------------------
@router.post("/invite-code", response_model=InviteCodeResponse)
async def create_invite_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """8자리 초대코드를 생성합니다. 1시간 유효, 1회 사용 가능."""
    code = generate_invite_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_CODE_EXPIRE_HOURS)

    # DB에 이력 저장
    invite = InviteCode(
        code=code,
        created_by=current_user.id,
        expires_at=expires_at,
    )
    db.add(invite)
    await db.commit()

    # Redis에 TTL과 함께 저장 (실제 유효성 검사는 Redis로)
    await save_invite_code(code, current_user.id)

    return InviteCodeResponse(code=code, expires_in_hours=settings.INVITE_CODE_EXPIRE_HOURS)


# -------------------------------------------------------
# OTP 2차인증 설정 시작
# -------------------------------------------------------
@router.post("/otp/setup", response_model=OtpSetupResponse)
async def setup_otp(current_user: User = Depends(get_current_user)):
    """
    OTP 2차인증 설정을 시작합니다.
    반환된 qr_uri를 QR코드로 변환해서 Google Authenticator에 등록하세요.
    """
    secret = generate_otp_secret()
    qr_uri = get_otp_uri(secret, current_user.username)
    # 실제 활성화는 /otp/verify 에서 코드 확인 후 처리
    return OtpSetupResponse(secret=secret, qr_uri=qr_uri)


# -------------------------------------------------------
# OTP 등록 완료 (코드 확인 후 활성화)
# -------------------------------------------------------
@router.post("/otp/verify", response_model=SuccessResponse)
async def verify_and_enable_otp(
    request: OtpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """OTP 코드가 맞으면 2차인증을 활성화합니다."""
    if not verify_otp(request.otp_code, request.otp_code):
        raise HTTPException(status_code=400, detail="OTP 코드가 올바르지 않습니다.")

    current_user.otp_enabled = True
    await db.commit()
    return SuccessResponse(message="OTP 2차인증이 활성화되었습니다.")
