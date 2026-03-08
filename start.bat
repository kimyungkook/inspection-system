@echo off
:: ═══════════════════════════════════════════════════════
:: 검사기록관리 시스템 v01 - Windows 시작 스크립트
:: ═══════════════════════════════════════════════════════

title 검사기록관리 시스템 v01

cd /d "%~dp0"

where node >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js가 설치되어 있지 않습니다.
    echo    https://nodejs.org 에서 LTS 버전을 다운로드하세요.
    pause
    exit /b 1
)

if not exist "node_modules\" (
    echo 📦 패키지 설치 중...
    npm install
)

if not exist "data\" mkdir data

echo.
echo ════════════════════════════════════════════════════
echo   검사기록관리 시스템 v01 시작 중...
echo ════════════════════════════════════════════════════
echo.
echo   브라우저에서 접속: http://localhost:3000
echo   기본 계정: admin / admin1234
echo.
echo   시스템을 종료하려면 이 창을 닫으세요.
echo ════════════════════════════════════════════════════
echo.

node server.js

pause
