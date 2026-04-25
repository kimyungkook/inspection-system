# AI 1차 필터 — 전체 종목 → 30개 선정
# 재무지표 + 기술적 점수 정량 스코어링

import logging
from app.services.kis_api.client import get_top_stocks_by_volume, get_financial_data, get_daily_candles
from app.services.tech_engine.indicator_calculator import calculate

logger = logging.getLogger(__name__)

# 각 팩터 가중치 (합계 100)
WEIGHT = {"financial": 35, "technical": 35, "valuation": 30}


async def run_first_filter(limit: int = 30) -> list[dict]:
    """
    거래량 상위 100개 → 정량 스코어링 → 상위 30개 반환.
    각 종목에 대해 재무 + 기술적 + 밸류에이션 점수를 합산.
    """
    logger.info("1차 AI 필터 시작 (100개 → 30개)")

    candidates = await get_top_stocks_by_volume(limit=100)
    scored = []

    for stock in candidates:
        ticker = stock["ticker"]
        try:
            score_data = await _score_stock(ticker, stock)
            if score_data:
                scored.append(score_data)
        except Exception as e:
            logger.warning(f"{ticker} 스코어링 실패: {e}")

    # 총점 내림차순 정렬 → 상위 30개
    scored.sort(key=lambda x: x["total_score"], reverse=True)
    result = scored[:limit]
    logger.info(f"1차 필터 완료: {len(result)}개 선정")
    return result


async def _score_stock(ticker: str, base_info: dict) -> dict | None:
    """개별 종목 스코어링."""
    # 재무 데이터
    fin = await get_financial_data(ticker)
    # 기술적 지표 (일봉 90일)
    df = await get_daily_candles(ticker, period=90)
    ind = calculate(df, ticker) if df is not None and len(df) > 30 else None

    # [재무 점수] 35점
    fin_score = _calc_financial_score(fin)

    # [기술적 점수] 35점
    tech_score = _calc_technical_score(ind) if ind else 0

    # [밸류에이션 점수] 30점 (PER, PBR 기반)
    val_score = _calc_valuation_score(fin)

    total = round(fin_score + tech_score + val_score, 1)

    # 최소 기준 미달 종목 제외 (총점 40점 미만)
    if total < 40:
        return None

    return {
        "ticker": ticker,
        "name": base_info.get("name", ""),
        "current_price": base_info.get("current_price", 0),
        "total_score": total,
        "scores": {"재무": fin_score, "기술적": tech_score, "밸류에이션": val_score},
        "financial": fin,
        "indicators": {
            "rsi": ind.rsi if ind else None,
            "macd_hist": ind.macd_hist if ind else None,
            "volume_ratio": ind.volume_ratio if ind else 0,
            "ma_aligned": ind.ma_aligned if ind else False,
        },
    }


def _calc_financial_score(fin: dict) -> float:
    """재무 점수 계산 (0~35)."""
    score = 0.0
    # ROE ≥ 15% → 10점, ≥ 10% → 6점
    roe = fin.get("roe", 0)
    score += 10 if roe >= 15 else 6 if roe >= 10 else 3 if roe >= 5 else 0
    # 매출성장률 ≥ 20% → 10점
    rev = fin.get("revenue_growth", 0)
    score += 10 if rev >= 20 else 6 if rev >= 10 else 2 if rev >= 0 else 0
    # 부채비율 ≤ 100% → 8점
    debt = fin.get("debt_ratio", 999)
    score += 8 if debt <= 100 else 4 if debt <= 200 else 0
    # 영업이익률 ≥ 10% → 7점
    margin = fin.get("operating_margin", 0)
    score += 7 if margin >= 10 else 4 if margin >= 5 else 1 if margin > 0 else 0
    return min(score, WEIGHT["financial"])


def _calc_technical_score(ind) -> float:
    """기술적 점수 계산 (0~35)."""
    score = 0.0
    if ind.rsi and 30 <= ind.rsi <= 60:   score += 8   # 적정 RSI 구간
    if ind.macd_hist and ind.macd_hist > 0: score += 8  # MACD 양전환
    if ind.ma_aligned:                     score += 8   # 정배열
    if ind.volume_ratio >= 150:            score += 6   # 거래량 150%+
    if ind.obv_rising:                     score += 5   # OBV 상승
    return min(score, WEIGHT["technical"])


def _calc_valuation_score(fin: dict) -> float:
    """밸류에이션 점수 계산 (0~30)."""
    score = 0.0
    per = fin.get("per", 0)
    pbr = fin.get("pbr", 0)
    # PER 8~20 적정 구간
    if 0 < per <= 10:   score += 15
    elif per <= 20:     score += 12
    elif per <= 30:     score += 6
    # PBR 1~3 적정
    if 0 < pbr <= 1:    score += 15
    elif pbr <= 2:      score += 10
    elif pbr <= 3:      score += 5
    return min(score, WEIGHT["valuation"])
