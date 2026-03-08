#!/bin/bash
# ═══════════════════════════════════════════════════════
# 검사기록관리 시스템 v01 - 시작 스크립트
# ═══════════════════════════════════════════════════════

cd "$(dirname "$0")"

# Node.js 확인
if ! command -v node &> /dev/null; then
    echo "❌ Node.js가 설치되어 있지 않습니다."
    echo "   https://nodejs.org 에서 다운로드하세요."
    exit 1
fi

# 패키지 설치 확인
if [ ! -d "node_modules" ]; then
    echo "📦 패키지 설치 중..."
    npm install
fi

# data 폴더 생성
mkdir -p data

echo "🚀 검사기록관리 시스템 v01 시작 중..."
node server.js
