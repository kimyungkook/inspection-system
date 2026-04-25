# 한국투자증권 REST API 클라이언트
# Exponential Backoff: 실패 시 자동 재시도 (2s → 4s → 8s)

import asyncio
import httpx
import logging
import pandas as pd
from typing import Optional
from app.core.config import settings
from app.services.kis_api.auth import get_headers
from app.core.redis_client import cache_stock_price, get_cached_stock_price

logger = logging.getLogger(__name__)
BASE = settings.KIS_BASE_URL


async def _request(method: str, path: str, **kwargs) -> dict:
    """공통 HTTP 요청 — 최대 3회 재시도."""
    url = f"{BASE}{path}"
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await getattr(client, method)(url, **kwargs)
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if attempt == 2:
                raise
            wait = 2 ** (attempt + 1)
            logger.warning(f"KIS API 재시도 {attempt+1}/3 ({wait}s): {e}")
            await asyncio.sleep(wait)
    return {}


# -------------------------------------------------------
# 현재가 조회 (국내 주식)
# -------------------------------------------------------
async def get_current_price(ticker: str) -> Optional[dict]:
    """
    국내 주식 현재가 + 기본 시세 정보 반환.
    Redis 캐시(60초)를 먼저 확인해서 API 호출 횟수 절약.
    """
    cached = await get_cached_stock_price(ticker)
    if cached:
        return cached

    tr_id = "FHKST01010100" if settings.KIS_IS_REAL else "FHKST01010100"
    headers = await get_headers(tr_id)
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": ticker,
    }

    data = await _request("get", "/uapi/domestic-stock/v1/quotations/inquire-price",
                           headers=headers, params=params)
    output = data.get("output", {})
    if not output:
        return None

    result = {
        "ticker": ticker,
        "current_price": float(output.get("stck_prpr", 0)),
        "change_rate": float(output.get("prdy_ctrt", 0)),      # 전일 대비 등락률(%)
        "volume": int(output.get("acml_vol", 0)),              # 누적 거래량
        "open_price": float(output.get("stck_oprc", 0)),
        "high_price": float(output.get("stck_hgpr", 0)),
        "low_price": float(output.get("stck_lwpr", 0)),
        "market_cap": int(output.get("hts_avls", 0)),          # 시가총액(억)
    }
    await cache_stock_price(ticker, result, ttl_seconds=60)
    return result


# -------------------------------------------------------
# 분봉 데이터 조회 (기술적 지표 계산용)
# -------------------------------------------------------
async def get_minute_candles(ticker: str, time_div: str = "1") -> pd.DataFrame:
    """
    분봉 데이터 반환 (DataFrame).
    time_div: "1"=1분봉, "5"=5분봉, "30"=30분봉
    columns: open, high, low, close, volume
    """
    tr_id = "FHKST03010200"
    headers = await get_headers(tr_id)
    params = {
        "fid_etc_cls_code": "",
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": ticker,
        "fid_input_hour_1": time_div,
        "fid_pw_data_incu_yn": "N",
    }

    data = await _request("get", "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
                           headers=headers, params=params)
    rows = data.get("output2", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "stck_bsop_date": "date",
        "stck_cntg_hour": "time",
        "stck_prpr": "close",
        "stck_oprc": "open",
        "stck_hgpr": "high",
        "stck_lwpr": "low",
        "cntg_vol": "volume",
    })
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[["date", "time", "open", "high", "low", "close", "volume"]].dropna()


# -------------------------------------------------------
# 일봉 데이터 조회 (AI 분석용)
# -------------------------------------------------------
async def get_daily_candles(ticker: str, period: int = 90) -> pd.DataFrame:
    """최근 N일 일봉 데이터 반환. AI 분석 및 백테스트에 사용."""
    tr_id = "FHKST01010400"
    headers = await get_headers(tr_id)
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": ticker,
        "fid_input_date_1": "",
        "fid_input_date_2": "",
        "fid_period_div_code": "D",
        "fid_org_adj_prc": "0",
    }

    data = await _request("get", "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
                           headers=headers, params=params)
    rows = data.get("output2", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows[:period])
    df = df.rename(columns={
        "stck_bsop_date": "date",
        "stck_clpr": "close",
        "stck_oprc": "open",
        "stck_hgpr": "high",
        "stck_lwpr": "low",
        "acml_vol": "volume",
    })
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[["date", "open", "high", "low", "close", "volume"]].dropna()


# -------------------------------------------------------
# 재무 데이터 조회 (AI 분석 Factor 1, 2용)
# -------------------------------------------------------
async def get_financial_data(ticker: str) -> dict:
    """PER, PBR, ROE, EPS 등 주요 재무 지표 반환."""
    tr_id = "FHKST66430200"
    headers = await get_headers(tr_id)
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": ticker,
    }

    data = await _request("get", "/uapi/domestic-stock/v1/finance/financial-ratio",
                           headers=headers, params=params)
    output = data.get("output", [{}])
    item = output[0] if output else {}

    return {
        "per": _to_float(item.get("per")),        # 주가수익비율 (낮을수록 저평가)
        "pbr": _to_float(item.get("pbr")),        # 주가순자산비율
        "roe": _to_float(item.get("roe")),        # 자기자본이익률 (높을수록 우량)
        "eps": _to_float(item.get("eps")),        # 주당순이익
        "debt_ratio": _to_float(item.get("lblt_rate")),   # 부채비율
        "revenue_growth": _to_float(item.get("sls_gr")),  # 매출 성장률(%)
        "operating_margin": _to_float(item.get("bsop_prfi_inrt")),  # 영업이익률
    }


# -------------------------------------------------------
# 업종별 상위 종목 조회 (1차 필터 후보 수집용)
# -------------------------------------------------------
async def get_top_stocks_by_volume(market: str = "J", limit: int = 100) -> list[dict]:
    """거래량 상위 종목 목록 반환 (1차 AI 필터 입력 데이터)."""
    tr_id = "FHPST01710000"
    headers = await get_headers(tr_id)
    params = {
        "fid_cond_mrkt_div_code": market,
        "fid_cond_scr_div_code": "20171",
        "fid_input_iscd": "0000",
        "fid_div_cls_code": "0",
        "fid_blng_cls_code": "0",
        "fid_trgt_cls_code": "111111111",
        "fid_trgt_exls_cls_code": "0000000000",
        "fid_input_price_1": "",
        "fid_input_price_2": "",
        "fid_vol_cnt": "",
        "fid_input_date_1": "",
    }

    data = await _request("get", "/uapi/domestic-stock/v1/quotations/volume-rank",
                           headers=headers, params=params)
    rows = data.get("output", [])[:limit]

    return [
        {
            "ticker": r.get("mksc_shrn_iscd", ""),
            "name": r.get("hts_kor_isnm", ""),
            "current_price": _to_float(r.get("stck_prpr")),
            "volume": _to_int(r.get("acml_vol")),
            "change_rate": _to_float(r.get("prdy_ctrt")),
        }
        for r in rows if r.get("mksc_shrn_iscd")
    ]


def _to_float(v) -> float:
    try:
        return float(v) if v not in (None, "", "-") else 0.0
    except (ValueError, TypeError):
        return 0.0


def _to_int(v) -> int:
    try:
        return int(str(v).replace(",", "")) if v not in (None, "", "-") else 0
    except (ValueError, TypeError):
        return 0
