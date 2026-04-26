@echo off
chcp 65001 >nul
title 데모 서버 중지

echo.
echo 데모 서버를 안전하게 중지합니다... (데이터는 보존됩니다)
echo.

docker-compose -f docker-compose.demo.yml down

echo.
echo 데모 서버가 중지되었습니다.
echo 다시 시작하려면 데모시작.bat 을 실행하세요.
echo.
pause
