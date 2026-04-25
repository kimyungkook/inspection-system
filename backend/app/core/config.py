# =============================================================
# 앱 전체 설정 파일
# .env 파일에 입력된 값들을 읽어서 앱 전체에서 사용합니다.
# =============================================================

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # 앱 기본 설정
    APP_ENV: Literal["development", "production"] = "development"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # 데이터베이스 (정보 저장소) 설정
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "stockapp"
    DB_USER: str = "stockuser"
    DB_PASSWORD: str = "stockpass123!"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 임시저장소 (Redis) 설정
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redispass123!"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # 보안 설정
    JWT_SECRET_KEY: str = "change-this-secret-key"
    AES_ENCRYPTION_KEY: str = "change-this-32-char-key-!!!!!!!!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 초대코드 설정
    INVITE_CODE_EXPIRE_HOURS: int = 1

    # AI 모델 설정 (claude / openai / gemini 중 선택)
    LLM_PROVIDER: Literal["claude", "openai", "gemini"] = "claude"
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # 한국투자증권 API 설정
    KIS_APP_KEY: str = ""
    KIS_APP_SECRET: str = ""
    KIS_ACCOUNT_NUMBER: str = ""
    KIS_IS_REAL: bool = False   # False = 모의투자, True = 실전투자

    @property
    def KIS_BASE_URL(self) -> str:
        if self.KIS_IS_REAL:
            return "https://openapi.koreainvestment.com:9443"
        return "https://openapivts.koreainvestment.com:29443"

    # 알림 설정
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    KAKAO_API_KEY: str = ""
    FCM_SERVER_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
