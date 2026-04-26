# 한국투자증권 REST API 클라이언트
# DEMO_MODE=true 이면 mock_client.py 로 자동 전환 (실제 API 키 불필요)

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# DEMO 모드 분기
# ─────────────────────────────────────────────────────────────
if settings.DEMO_MODE:
    # 실제 API 키 없이 동작하는 Mock 클라이언트
    from app.services.kis_api.mock_client import (          # noqa: F401
        get_current_price,
        get_minute_candles,
        get_daily_candles,
        get_financial_data,
        get_top_stocks_by_volume,
    )

else:
    # ── 실제 KIS API 클라이언트 ─────────────────────────────
    import asyncio
    import httpx
    import pandas as pd
    from typing import Optional
    from app.services.kis_api.auth import get_headers
    from app.core.redis_client import cache_stock_price, get_cached_stock_price

    BASE = settings.KIS_BASE_URL

    async def _request(method: str, path: str, **kwargs) -> dict:
        """공통 HTTP 요청 — 최대 3회 재시도 (Exponential Backoff)."""
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

    async def get_current_price(ticker: str) -> Optional[dict]:
        """현재가 조회 — Redis 캐시(60초) 우선 확인."""
        cached = await get_cached_stock_price(ticker)
        if cached:
            return cached

        headers = await get_headers("FHKST01010100")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
        }
        data = await _request(
            "get", "/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=headers, params=params
        )
        output = data.get("output", {})
        if not output:
            return None

        result = {
            "ticker":        ticker,
            "current_price": float(output.get("stck_prpr", 0)),
            "change_rate":   float(output.get("prdy_ctrt", 0)),
            "volume":        int(output.get("acml_vol", 0)),
            "open_price":    float(output.get("stck_oprc", 0)),
            "high_price":    float(output.get("stck_hgpr", 0)),
            "low_price":     float(output.get("stck_lwpr", 0)),
            "market_cap":    int(output.get("hts_avls", 0)),
        }
        await cache_stock_price(ticker, result, ttl_seconds=60)
        return result

    async def get_minute_candles(ticker: str, time_div: str = "1") -> pd.DataFrame:
        """분봉 데이터 반환 (time_div: "1"=1분봉, "5"=5분봉)."""
        headers = await get_headers("FHKST03010200")
        params = {
            "fid_etc_cls_code": "",
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
            "fid_input_hour_1": time_div,
            "fid_pw_data_incu_yn": "N",
        }
        data = await _request(
            "get", "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            headers=headers, params=params
        )
        rows = data.get("output2", [])
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).rename(columns={
            "stck_bsop_date": "date", "stck_cntg_hour": "time",
            "stck_prpr": "close", "stck_oprc": "open",
            "stck_hgpr": "high", "stck_lwpr": "low", "cntg_vol": "volume",
        })
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df[["date", "time", "open", "high", "low", "close", "volume"]].dropna()

    async def get_daily_candles(ticker: str, period: int = 90) -> pd.DataFrame:
        """일봉 데이터 반환."""
        headers = await get_headers("FHKST01010400")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker,
            "fid_input_date_1": "", "fid_input_date_2": "",
            "fid_period_div_code": "D", "fid_org_adj_prc": "0",
        }
        data = await _request(
            "get", "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            headers=headers, params=params
        )
        rows = data.get("output2", [])
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows[:period]).rename(columns={
            "stck_bsop_date": "date", "stck_clpr": "close",
            "stck_oprc": "open", "stck_hgpr": "high",
            "stck_lwpr": "low", "acml_vol": "volume",
        })
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df[["date", "open", "high", "low", "close", "volume"]].dropna()

    async def get_financial_data(ticker: str) -> dict:
        """PER, PBR, ROE, EPS 등 재무 지표 반환."""
        headers = await get_headers("FHKST66430200")
        params = {"fid_cond_mrkt_div_code": "J", "fid_input_iscd": ticker}
        data = await _request(
            "get", "/uapi/domestic-stock/v1/finance/financial-ratio",
            headers=headers, params=params
        )
        item = (data.get("output") or [{}])[0]
        return {
            "per":              _to_float(item.get("per")),
            "pbr":              _to_float(item.get("pbr")),
            "roe":              _to_float(item.get("roe")),
            "eps":              _to_float(item.get("eps")),
            "debt_ratio":       _to_float(item.get("lblt_rate")),
            "revenue_growth":   _to_float(item.get("sls_gr")),
            "operating_margin": _to_float(item.get("bsop_prfi_inrt")),
        }

    async def get_top_stocks_by_volume(market: str = "J", limit: int = 100) -> list[dict]:
        """거래량 상위 종목 목록 반환."""
        headers = await get_headers("FHPST01710000")
        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_cond_scr_div_code": "20171",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0", "fid_blng_cls_code": "0",
            "fid_trgt_cls_code": "111111111",
            "fid_trgt_exls_cls_code": "0000000000",
            "fid_input_price_1": "", "fid_input_price_2": "",
            "fid_vol_cnt": "", "fid_input_date_1": "",
        }
        data = await _request(
            "get", "/uapi/domestic-stock/v1/quotations/volume-rank",
            headers=headers, params=params
        )
        return [
            {
                "ticker":        r.get("mksc_shrn_iscd", ""),
                "name":          r.get("hts_kor_isnm", ""),
                "current_price": _to_float(r.get("stck_prpr")),
                "volume":        _to_int(r.get("acml_vol")),
                "change_rate":   _to_float(r.get("prdy_ctrt")),
            }
            for r in data.get("output", [])[:limit]
            if r.get("mksc_shrn_iscd")
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
