# =============================================================
# Docker 빌드 설정 — 백엔드 서버 실행 환경
# 이 파일은 자동으로 사용됩니다. 건드리지 않아도 됩니다.
# =============================================================

FROM python:3.11-slim

# 시스템 기본 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 폴더 설정
WORKDIR /app

# 패키지 목록 먼저 복사 후 설치 (캐시 활용으로 빌드 속도 향상)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 전체 코드 복사
COPY . .

# 포트 열기
EXPOSE 8000

# 서버 시작 명령어
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
