@echo off
chcp 65001 >nul
title AI 주식 매매 가이드 앱 — 시작

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   AI 주식 매매 가이드 앱 시작 중...   ║
echo  ╚══════════════════════════════════════╝
echo.

:: Docker Desktop 실행 여부 확인
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  ❌ Docker Desktop이 실행되지 않았습니다.
    echo.
    echo  해결방법:
    echo  1. 바탕화면의 Docker Desktop 아이콘을 더블클릭하세요
    echo  2. 하단 작업표시줄에 고래 아이콘이 뜰 때까지 기다리세요
    echo  3. 이 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)

echo  ✅ Docker Desktop 확인 완료
echo.

:: .env 파일 존재 여부 확인
if not exist ".env" (
    echo  ❌ .env 파일이 없습니다.
    echo.
    echo  해결방법:
    echo  1. 이 폴더에서 ".env.example" 파일을 찾으세요
    echo  2. 복사해서 이름을 ".env" 로 바꾸세요
    echo  3. 메모장으로 열어서 API 키를 입력하세요
    echo  4. 이 파일을 다시 실행하세요
    echo.
    pause
    exit /b 1
)

echo  ✅ 설정 파일 확인 완료
echo.
echo  서버를 시작합니다... (처음에는 3~5분 소요)
echo.

:: 전체 서버 시작
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo  ╔══════════════════════════════════════════════╗
    echo  ║  ✅ 앱 서버 시작 완료!                        ║
    echo  ║                                              ║
    echo  ║  브라우저에서 아래 주소로 접속하세요:           ║
    echo  ║  • API 서버: http://localhost:8000            ║
    echo  ║  • API 문서: http://localhost:8000/docs       ║
    echo  ║  • 작업 현황: http://localhost:5555           ║
    echo  ║                                              ║
    echo  ║  📱 앱은 폰에 APK 설치 후 사용하세요           ║
    echo  ╚══════════════════════════════════════════════╝
    echo.
    start http://localhost:8000/docs
) else (
    echo.
    echo  ❌ 시작 중 오류가 발생했습니다.
    echo  docker-compose logs 명령어로 오류 내용을 확인하세요.
    echo.
)

pause
