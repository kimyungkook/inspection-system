# =============================================================
# 보안 모듈 — 금융 앱 수준 보안 처리
#
# 이 파일이 하는 일:
#   1. 비밀번호 암호화 저장 (bcrypt — 복호화 불가능한 단방향 암호화)
#   2. 로그인 토큰 발급/검증 (JWT — 로그인 상태 유지)
#   3. API 키 암호화 저장 (AES256 — 양방향 암호화, 필요시 복호화 가능)
#   4. OTP 2차 인증 (시간 기반 6자리 코드)
# =============================================================

import base64
import os
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# -------------------------------------------------------
# 1. 비밀번호 암호화 (bcrypt)
# bcrypt = 비밀번호를 알아볼 수 없는 문자열로 변환
# 한 번 암호화하면 원래 비밀번호로 되돌릴 수 없음 (단방향)
# -------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호를 암호화합니다. DB에 저장할 때 사용."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력한 비밀번호가 저장된 암호화 비밀번호와 일치하는지 확인합니다."""
    return pwd_context.verify(plain_password, hashed_password)


# -------------------------------------------------------
# 2. JWT 로그인 토큰 (JSON Web Token)
# JWT = 로그인 성공 시 발급되는 임시 신분증
# 매 요청마다 이 토큰을 보여주면 로그인 상태로 인식
# Access Token: 15분 (짧음 — 보안용)
# Refresh Token: 7일 (긺 — 자동 로그인용)
# -------------------------------------------------------

def create_access_token(user_id: int, username: str) -> str:
    """로그인 성공 시 발급하는 단기 토큰 (15분 유효)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    """자동 로그인을 위한 장기 토큰 (7일 유효)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    토큰이 유효한지 확인합니다.
    유효하면 사용자 정보 반환, 아니면 None 반환.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


# -------------------------------------------------------
# 3. API 키 암호화 (AES256)
# AES256 = 군사급 암호화 방식
# API 키(한국투자증권 키, Claude 키 등)를 DB에 저장할 때 암호화
# 필요할 때는 복호화해서 사용 가능 (양방향)
# -------------------------------------------------------

def _get_aes_key() -> bytes:
    """AES 암호화에 사용할 32바이트(256비트) 키를 준비합니다."""
    key = settings.AES_ENCRYPTION_KEY.encode("utf-8")
    # 32바이트에 맞게 자르거나 늘림
    return key[:32].ljust(32, b"0")


def encrypt_api_key(plain_text: str) -> dict:
    """
    API 키를 AES256으로 암호화합니다.
    반환값: {"encrypted": "암호화된값", "iv": "초기벡터값"}
    두 값 모두 DB에 저장해야 복호화 가능합니다.
    """
    key = _get_aes_key()
    iv = os.urandom(16)   # 매번 다른 초기벡터 생성 (보안 강화)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # 16바이트 단위로 맞추기 (패딩)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode("utf-8")) + padder.finalize()

    encrypted = encryptor.update(padded_data) + encryptor.finalize()

    return {
        "encrypted": base64.b64encode(encrypted).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8"),
    }


def decrypt_api_key(encrypted_text: str, iv_text: str) -> str:
    """
    암호화된 API 키를 복호화합니다.
    실제 API 호출이 필요할 때만 사용합니다.
    """
    key = _get_aes_key()
    iv = base64.b64decode(iv_text)
    encrypted = base64.b64decode(encrypted_text)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    padded_data = decryptor.update(encrypted) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    plain_text = unpadder.update(padded_data) + unpadder.finalize()

    return plain_text.decode("utf-8")


# -------------------------------------------------------
# 4. OTP 2차 인증 (TOTP — Time-based One-Time Password)
# OTP = 30초마다 바뀌는 6자리 숫자 코드
# Google Authenticator 앱과 연동 가능
# -------------------------------------------------------

def generate_otp_secret() -> str:
    """OTP 설정용 비밀 키를 생성합니다. 최초 1회만 생성."""
    return pyotp.random_base32()


def get_otp_uri(secret: str, username: str) -> str:
    """
    QR코드로 변환할 OTP 등록 주소를 만듭니다.
    Google Authenticator에서 QR코드 스캔 시 자동 등록됩니다.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name="AI주식앱")


def verify_otp(secret: str, otp_code: str) -> bool:
    """사용자가 입력한 OTP 코드가 올바른지 확인합니다."""
    totp = pyotp.TOTP(secret)
    return totp.verify(otp_code, valid_window=1)   # 앞뒤 30초 허용


# -------------------------------------------------------
# 5. 초대코드 생성
# 8자리 랜덤 대문자+숫자 조합 (예: A7K2X9Q1)
# -------------------------------------------------------

def generate_invite_code() -> str:
    """8자리 초대코드를 생성합니다."""
    chars = string.ascii_uppercase + string.digits
    # 헷갈리기 쉬운 문자 제외 (O, 0, I, 1, L)
    chars = chars.translate(str.maketrans("", "", "O0I1L"))
    return "".join(secrets.choice(chars) for _ in range(8))


# -------------------------------------------------------
# 6. 비밀번호 강도 검증
# -------------------------------------------------------

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    비밀번호 강도를 확인합니다.
    반환값: (통과여부, 실패이유)
    """
    if len(password) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다."
    if not any(c.isupper() for c in password):
        return False, "대문자를 1개 이상 포함해야 합니다."
    if not any(c.islower() for c in password):
        return False, "소문자를 1개 이상 포함해야 합니다."
    if not any(c.isdigit() for c in password):
        return False, "숫자를 1개 이상 포함해야 합니다."
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "특수문자를 1개 이상 포함해야 합니다."
    return True, "OK"
