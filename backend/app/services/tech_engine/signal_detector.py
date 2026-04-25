# 기술적 신호 감지 — S/A/B/C 등급 산출
# 조건이 많을수록 높은 등급 → S: 5개+, A: 3~4개, B: 2개, C: 1개

from dataclasses import dataclass
from typing import Optional
from app.services.tech_engine.indicator_calculator import Indicators


@dataclass
class Signal:
    type: str          # "BUY" | "SELL"
    grade: str         # "S" | "A" | "B" | "C"
    triggers: dict     # 발동된 지표 {이름: 설명}
    count: int         # 발동 지표 수


def detect_buy_signal(ind: Indicators) -> Optional[Signal]:
    """매수 신호 감지. 발동 조건 수로 등급 결정."""
    triggers = {}

    # 1. RSI 과매도 (< 30)
    if ind.rsi is not None and ind.rsi < 30:
        triggers["RSI"] = f"{ind.rsi:.1f} (과매도구간)"

    # 2. MACD 골든크로스
    if ind.macd_golden_cross:
        triggers["MACD"] = "골든크로스 발생"
    # 골든크로스는 아니지만 히스토그램이 양전환
    elif ind.macd_hist is not None and ind.macd_hist > 0 and ind.macd_line is not None and ind.macd_line > ind.macd_signal:
        triggers["MACD히스토그램"] = f"양전환 ({ind.macd_hist:.2f})"

    # 3. 볼린저밴드 하단 근접 (bb_position < 0.15)
    if ind.bb_position is not None and ind.bb_position < 0.15:
        triggers["볼린저밴드"] = f"하단 근접 (위치:{ind.bb_position:.2f})"

    # 4. 이동평균 정배열
    if ind.ma_aligned:
        triggers["이동평균"] = "5>20>60 정배열"
    # 5MA가 20MA 상향돌파 (골든크로스)
    elif ind.ma5 and ind.ma20 and ind.ma5 > ind.ma20:
        triggers["이동평균크로스"] = f"5MA>{ind.ma20:.0f}(20MA)"

    # 5. 거래량 급증 (평균 대비 200% 이상)
    if ind.volume_ratio >= 200:
        triggers["거래량"] = f"{ind.volume_ratio:.0f}% 급증"

    # 6. 스토캐스틱 과매도 반전 (K < 20, K > D)
    if (ind.stoch_k is not None and ind.stoch_d is not None
            and ind.stoch_k < 20 and ind.stoch_k > ind.stoch_d):
        triggers["스토캐스틱"] = f"과매도 반전 K:{ind.stoch_k:.1f}"

    # 7. OBV 상승 추세
    if ind.obv_rising:
        triggers["OBV"] = "거래량 상승추세 확인"

    count = len(triggers)
    if count == 0:
        return None

    grade = "S" if count >= 5 else "A" if count >= 3 else "B" if count == 2 else "C"
    return Signal(type="BUY", grade=grade, triggers=triggers, count=count)


def detect_sell_signal(ind: Indicators) -> Optional[Signal]:
    """매도/주의 신호 감지."""
    triggers = {}

    # 1. RSI 과매수 (> 70)
    if ind.rsi is not None and ind.rsi > 70:
        triggers["RSI"] = f"{ind.rsi:.1f} (과매수구간)"

    # 2. MACD 데드크로스 (macd < signal)
    if (ind.macd_line is not None and ind.macd_signal is not None
            and ind.macd_line < ind.macd_signal and ind.macd_hist is not None and ind.macd_hist < 0):
        triggers["MACD"] = "데드크로스 발생"

    # 3. 볼린저밴드 상단 도달 (bb_position > 0.9)
    if ind.bb_position is not None and ind.bb_position > 0.9:
        triggers["볼린저밴드"] = f"상단 도달 (위치:{ind.bb_position:.2f})"

    # 4. 이동평균 역배열 (5 < 20)
    if ind.ma5 and ind.ma20 and ind.ma5 < ind.ma20:
        triggers["이동평균"] = "역배열 전환"

    # 5. 스토캐스틱 과매수 (K > 80, K < D)
    if (ind.stoch_k is not None and ind.stoch_d is not None
            and ind.stoch_k > 80 and ind.stoch_k < ind.stoch_d):
        triggers["스토캐스틱"] = f"과매수 하락 K:{ind.stoch_k:.1f}"

    count = len(triggers)
    if count == 0:
        return None

    grade = "S" if count >= 4 else "A" if count >= 3 else "B" if count == 2 else "C"
    return Signal(type="SELL", grade=grade, triggers=triggers, count=count)
