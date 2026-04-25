@echo off
chcp 65001 >nul
title AI 주식 앱 — 중지

echo.
echo  서버를 안전하게 중지합니다...
echo.

docker-compose down

echo.
echo  ✅ 서버가 중지되었습니다. (데이터는 보존됩니다)
echo.
pause
