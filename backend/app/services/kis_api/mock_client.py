"""
데모 모드용 Mock KIS API 클라이언트
DEMO_MODE=true 일 때 실제 KIS API 대신 이 모듈이 사용됩니다.
실제 API 키 없이도 앱의 모든 기능을 확인할 수 있습니다.
"""

import random
import math
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional

# ─────────────────────────────────────────────────────────────
# 데모용 한국 대표 20종목 기본 데이터
# ─────────────────────────────────────────────────────────────
MOCK_STOCKS: dict[str, dict] = {
    "005930": {"name": "삼성전자",          "price": 55000,   "change":  1.24, "volume": 12500000, "sector": "반도체/전자"},
    "000660": {"name": "SK하이닉스",         "price": 185000,  "change":  2.08, "volume":  3800000, "sector": "반도체"},
    "035420": {"name": "NAVER",             "price": 195000,  "change": -0.51, "volume":   820000, "sector": "IT/인터넷"},
    "035720": {"name": "카카오",             "price": 42000,   "change": -1.17, "volume":  2100000, "sector": "IT/플랫폼"},
    "005380": {"name": "현대차",             "price": 195000,  "change":  0.77, "volume":   650000, "sector": "자동차"},
    "000270": {"name": "기아",               "price": 93000,   "change":  1.42, "volume":  1200000, "sector": "자동차"},
    "373220": {"name": "LG에너지솔루션",     "price": 295000,  "change":  3.21, "volume":   380000, "sector": "2차전지"},
    "207940": {"name": "삼성바이오로직스",   "price": 880000,  "change":  0.34, "volume":    95000, "sector": "바이오"},
    "068270": {"name": "셀트리온",           "price": 155000,  "change": -0.64, "volume":   720000, "sector": "바이오"},
    "005490": {"name": "POSCO홀딩스",       "price": 290000,  "change":  1.05, "volume":   310000, "sector": "철강/소재"},
    "105560": {"name": "KB금융",             "price": 85000,   "change":  0.59, "volume":   480000, "sector": "금융"},
    "055550": {"name": "신한지주",           "price": 52000,   "change":  0.39, "volume":   620000, "sector": "금융"},
    "006400": {"name": "삼성SDI",            "price": 220000,  "change": -1.35, "volume":   290000, "sector": "2차전지"},
    "051910": {"name": "LG화학",             "price": 265000,  "change": -0.75, "volume":   350000, "sector": "화학/소재"},
    "012330": {"name": "현대모비스",         "price": 235000,  "change":  0.43, "volume":   230000, "sector": "자동차부품"},
    "323410": {"name": "카카오뱅크",         "price": 22000,   "change": -2.22, "volume":  3200000, "sector": "핀테크"},
    "259960": {"name": "크래프톤",           "price": 250000,  "change":  2.84, "volume":   180000, "sector": "게임"},
    "086520": {"name": "에코프로",           "price": 95000,   "change":  4.95, "volume":  1800000, "sector": "2차전지 소재"},
    "034020": {"name": "두산에너빌리티",     "price": 26000,   "change":  1.57, "volume":  5500000, "sector": "원전/에너지"},
    "267260": {"name": "HD현대일렉트릭",     "price": 235000,  "change":  3.48, "volume":   420000, "sector": "전력기기"},
}


def _jitter(base: float, pct: float = 0.005) -> float:
    """기본값에 ±pct 범위의 랜덤 변동을 추가해 실시간처럼 보이게 합니다."""
    return base * (1 + random.uniform(-pct, pct))


async def get_current_price(ticker: str) -> Optional[dict]:
    """현재가 조회 Mock — 실제 KIS API와 동일한 반환 형식"""
    stock = MOCK_STOCKS.get(ticker)
    if not stock:
        return None

    base  = stock["price"]
    price = round(_jitter(base, 0.008))
    change = stock["change"] + random.uniform(-0.2, 0.2)

    return {
        "ticker":        ticker,
        "current_price": price,
        "change_rate":   round(change, 2),
        "volume":        int(stock["volume"] * random.uniform(0.85, 1.15)),
        "open_price":    round(base * random.uniform(0.995, 1.005)),
        "high_price":    round(max(price, base) * random.uniform(1.003, 1.015)),
        "low_price":     round(min(price, base) * random.uniform(0.985, 0.997)),
        "market_cap":    round(base * 5_970_000 / 100),
    }


async def get_minute_candles(ticker: str, time_div: str = "1") -> pd.DataFrame:
    """분봉 Mock — 랜덤 워크로 현실적인 캔들 생성 (기술적 지표 계산 가능)"""
    stock = MOCK_STOCKS.get(ticker)
    base_price = stock["price"] if stock else 50_000

    n_candles = 120
    prices    = [float(base_price)]
    vols      = []

    for _ in range(n_candles - 1):
        # 랜덤 워크: 이전 종가 기준 ±0.3%
        change = random.gauss(0.0002, 0.003)
        prices.append(round(prices[-1] * (1 + change)))

    now   = datetime.now(timezone.utc)
    rows  = []
    mins  = int(time_div) if time_div.isdigit() else 1

    for i, close in enumerate(reversed(prices)):
        dt   = now - timedelta(minutes=i * mins)
        spread = close * 0.004
        open_  = round(close + random.uniform(-spread, spread))
        high   = round(max(close, open_) * (1 + random.uniform(0, 0.005)))
        low    = round(min(close, open_) * (1 - random.uniform(0, 0.005)))
        vol    = int(random.uniform(50_000, 500_000))

        rows.append({
            "date":   dt.strftime("%Y%m%d"),
            "time":   dt.strftime("%H%M%S"),
            "open":   float(open_),
            "high":   float(high),
            "low":    float(low),
            "close":  float(close),
            "volume": float(vol),
        })

    df = pd.DataFrame(rows)
    return df[["date", "time", "open", "high", "low", "close", "volume"]]


async def get_daily_candles(ticker: str, period: int = 90) -> pd.DataFrame:
    """일봉 Mock"""
    stock = MOCK_STOCKS.get(ticker)
    base_price = stock["price"] if stock else 50_000

    prices = [float(base_price)]
    for _ in range(period - 1):
        change = random.gauss(0.0005, 0.015)
        prices.append(round(prices[-1] * (1 + change)))

    now  = datetime.now(timezone.utc)
    rows = []
    for i, close in enumerate(reversed(prices)):
        dt     = now - timedelta(days=i)
        spread = close * 0.02
        open_  = round(close + random.uniform(-spread, spread))
        high   = round(max(close, open_) * (1 + random.uniform(0, 0.02)))
        low    = round(min(close, open_) * (1 - random.uniform(0, 0.02)))
        vol    = int(random.uniform(500_000, 15_000_000))
        rows.append({
            "date": dt.strftime("%Y%m%d"),
            "open": float(open_), "high": float(high),
            "low": float(low), "close": float(close), "volume": float(vol),
        })

    df = pd.DataFrame(rows)
    return df[["date", "open", "high", "low", "close", "volume"]]


async def get_financial_data(ticker: str) -> dict:
    """재무 데이터 Mock"""
    return {
        "per":              round(random.uniform(8, 25), 1),
        "pbr":              round(random.uniform(0.5, 3.5), 2),
        "roe":              round(random.uniform(5, 25), 1),
        "eps":              round(random.uniform(1000, 15000)),
        "debt_ratio":       round(random.uniform(30, 150), 1),
        "revenue_growth":   round(random.uniform(-5, 30), 1),
        "operating_margin": round(random.uniform(3, 20), 1),
    }


async def get_top_stocks_by_volume(market: str = "J", limit: int = 100) -> list[dict]:
    """거래량 상위 종목 Mock — 등록된 20종목 전부 반환"""
    result = []
    for ticker, info in list(MOCK_STOCKS.items())[:limit]:
        result.append({
            "ticker":        ticker,
            "name":          info["name"],
            "current_price": round(_jitter(info["price"])),
            "volume":        int(info["volume"] * random.uniform(0.9, 1.1)),
            "change_rate":   round(info["change"] + random.uniform(-0.1, 0.1), 2),
        })
    return result
