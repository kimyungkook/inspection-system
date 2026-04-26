@echo off
chcp 65001 >nul
title AI 주식 매매 가이드 — 데모 실행

echo.
echo ============================================
echo   AI 주식 매매 가이드 앱 — 데모 모드 시작
echo   실제 API 키 없이 샘플 데이터로 실행됩니다
echo ============================================
echo.

:: Docker Desktop 실행 확인
docker info >nul 2>&1
if errorlevel 1 (
    echo [오류] Docker Desktop이 실행되지 않았습니다.
    echo.
    echo 해결 방법:
    echo   1. 바탕화면의 Docker Desktop 아이콘을 더블클릭하세요
    echo   2. 오른쪽 하단 트레이에 Docker 고래 아이콘이 보이면 준비된 것입니다
    echo   3. 이 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)

echo [1/3] Docker Desktop 정상 실행 중 확인 완료
echo.

:: 데모 실행 (기존 데모 컨테이너가 있으면 재사용)
echo [2/3] 데모 서버를 시작합니다... (처음 실행 시 3~5분 소요)
echo.
docker-compose -f docker-compose.demo.yml up -d --build

if errorlevel 1 (
    echo.
    echo [오류] 서버 시작에 실패했습니다.
    echo 위의 오류 메시지를 확인하고 다시 시도해 주세요.
    pause
    exit /b 1
)

echo.
echo [3/3] 서버 준비 완료를 기다리는 중...
timeout /t 5 /nobreak >nul

echo.
echo ============================================
echo   데모 서버가 시작되었습니다!
echo ============================================
echo.
echo   API 문서   : http://localhost:8000/docs
echo   서버 상태  : http://localhost:8000/health
echo.
echo   데모 로그인 정보:
echo   ┌─────────────────────────────────────┐
echo   │  관리자  아이디: admin              │
echo   │          비밀번호: demo1234!         │
echo   │                                     │
echo   │  일반    아이디: demo               │
echo   │          비밀번호: demo1234!         │
echo   └─────────────────────────────────────┘
echo.
echo   종료하려면: 데모중지.bat 실행
echo.

:: 브라우저 자동 열기 (5초 대기 후)
timeout /t 5 /nobreak >nul
start http://localhost:8000/docs

pause
