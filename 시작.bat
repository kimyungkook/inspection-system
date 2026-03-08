@echo off
chcp 65001 >nul 2>&1
title 검사기록관리 시스템 v01

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║       검사기록관리 시스템 v01  시작 중...         ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: Node.js 설치 확인
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ⚠️  Node.js 가 설치되어 있지 않습니다.
    echo.
    echo  지금 Node.js 다운로드 페이지를 열겠습니다.
    echo  ───────────────────────────────────────────────────
    echo  [설치 방법]
    echo  1. 열리는 페이지에서 왼쪽 초록색 버튼 클릭하여 다운로드
    echo  2. 다운받은 파일 더블클릭 → Next → Next → Install → Finish
    echo  3. 설치 완료 후 이 파일(시작.bat)을 다시 더블클릭
    echo  ───────────────────────────────────────────────────
    echo.
    pause
    start https://nodejs.org/ko
    exit /b
)

echo  ✅ Node.js 확인 완료
echo.

:: 처음 실행 시 패키지 설치
if not exist "node_modules" (
    echo  📦 처음 실행 시 필요한 파일을 설치합니다. (1-2분 소요)
    echo     인터넷 연결을 확인해주세요...
    echo.
    npm install --quiet
    if %errorlevel% neq 0 (
        echo.
        echo  ❌ 설치 중 오류가 발생했습니다.
        echo     인터넷 연결을 확인하고 다시 시도해주세요.
        pause
        exit /b
    )
    echo  ✅ 설치 완료
    echo.
)

:: 데이터 폴더 생성
if not exist "data" mkdir data

echo  🚀 서버를 시작합니다...
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   브라우저에서 자동으로 열립니다.                 ║
echo  ║                                                  ║
echo  ║   수동 접속: http://localhost:3000               ║
echo  ║                                                  ║
echo  ║   기본 계정: admin / admin1234 (관리자)           ║
echo  ║             inspector01 / inspector1234 (검사원)  ║
echo  ║                                                  ║
echo  ║   ⚠️  이 창을 닫으면 프로그램이 종료됩니다.       ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: 3초 후 브라우저 자동 열기
timeout /t 3 /nobreak >nul
start http://localhost:3000

:: 서버 실행
node server.js

echo.
echo  서버가 종료되었습니다.
pause
