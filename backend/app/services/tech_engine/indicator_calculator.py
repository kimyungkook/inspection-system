# 기술적 지표 계산 엔진
# pandas_ta 라이브러리로 RSI, MACD, 볼린저밴드, 이동평균, 스토캐스틱, OBV 계산

import pandas as pd
import pandas_ta as ta
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Indicators:
    """계산된 전체 지표 값을 담는 컨테이너."""
    ticker: str
    current_price: float = 0.0
    volume: float = 0.0
    volume_ratio: float = 0.0     # 20일 평균 대비 현재 거래량 비율(%)

    # RSI (0~100, 30이하=과매도, 70이상=과매수)
    rsi: Optional[float] = None

    # MACD (macd_line - signal_line = hist, 양수=상승모멘텀)
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    macd_golden_cross: bool = False   # 이번 봉에서 골든크로스 발생

    # 볼린저밴드
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_position: Optional[float] = None   # 0~1 (0=하단, 1=상단)

    # 이동평균선
    ma5: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    ma_aligned: bool = False    # 5>20>60 정배열 여부

    # 스토캐스틱 (0~100, 20이하=과매도, 80이상=과매수)
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None

    # OBV (거래량 기반 추세)
    obv: Optional[float] = None
    obv_rising: bool = False


def calculate(df: pd.DataFrame, ticker: str = "") -> Optional[Indicators]:
    """
    OHLCV DataFrame → 전체 지표 계산 후 Indicators 반환.
    최소 30행 이상 필요.
    """
    if df is None or len(df) < 30:
        logger.warning(f"{ticker}: 데이터 부족 ({len(df) if df is not None else 0}행)")
        return None

    df = df.copy().sort_index()
    ind = Indicators(ticker=ticker)

    try:
        ind.current_price = float(df["close"].iloc[-1])
        ind.volume = float(df["volume"].iloc[-1])

        # 거래량 비율 (현재 거래량 / 20일 평균)
        avg_vol = df["volume"].rolling(20).mean().iloc[-1]
        ind.volume_ratio = round((ind.volume / avg_vol * 100) if avg_vol > 0 else 0, 1)

        # RSI
        rsi_s = ta.rsi(df["close"], length=14)
        if rsi_s is not None and not rsi_s.empty:
            ind.rsi = round(float(rsi_s.iloc[-1]), 2)

        # MACD (12, 26, 9)
        macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            ind.macd_line   = round(float(macd_df.iloc[-1, 0]), 4)
            ind.macd_hist   = round(float(macd_df.iloc[-1, 1]), 4)
            ind.macd_signal = round(float(macd_df.iloc[-1, 2]), 4)
            # 골든크로스: 이전 봉 macd < signal, 현재 봉 macd > signal
            if len(macd_df) >= 2:
                prev_cross = macd_df.iloc[-2, 0] < macd_df.iloc[-2, 2]
                curr_cross = macd_df.iloc[-1, 0] > macd_df.iloc[-1, 2]
                ind.macd_golden_cross = prev_cross and curr_cross

        # 볼린저밴드 (20, 2)
        bb_df = ta.bbands(df["close"], length=20, std=2)
        if bb_df is not None and not bb_df.empty:
            ind.bb_lower  = round(float(bb_df.iloc[-1, 0]), 2)
            ind.bb_middle = round(float(bb_df.iloc[-1, 1]), 2)
            ind.bb_upper  = round(float(bb_df.iloc[-1, 2]), 2)
            band_width = ind.bb_upper - ind.bb_lower
            if band_width > 0:
                ind.bb_position = round((ind.current_price - ind.bb_lower) / band_width, 3)

        # 이동평균선
        for period, attr in [(5, "ma5"), (20, "ma20"), (60, "ma60"), (120, "ma120")]:
            if len(df) >= period:
                val = df["close"].rolling(period).mean().iloc[-1]
                setattr(ind, attr, round(float(val), 2))
        # 정배열: 5 > 20 > 60
        if all(x is not None for x in [ind.ma5, ind.ma20, ind.ma60]):
            ind.ma_aligned = ind.ma5 > ind.ma20 > ind.ma60

        # 스토캐스틱 (14, 3, 3)
        stoch_df = ta.stoch(df["high"], df["low"], df["close"], k=14, d=3, smooth_k=3)
        if stoch_df is not None and not stoch_df.empty:
            ind.stoch_k = round(float(stoch_df.iloc[-1, 0]), 2)
            ind.stoch_d = round(float(stoch_df.iloc[-1, 1]), 2)

        # OBV
        obv_s = ta.obv(df["close"], df["volume"])
        if obv_s is not None and len(obv_s) >= 2:
            ind.obv = round(float(obv_s.iloc[-1]), 0)
            ind.obv_rising = float(obv_s.iloc[-1]) > float(obv_s.iloc[-6])  # 5봉 추세

    except Exception as e:
        logger.error(f"{ticker} 지표 계산 오류: {e}")
        return None

    return ind
