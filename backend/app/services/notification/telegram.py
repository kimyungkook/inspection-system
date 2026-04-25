# 텔레그램 봇 알림 발송
# 신호 등급별 메시지 포맷 + 발송 재시도 로직

import httpx
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)
BASE_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

GRADE_EMOJI = {"S": "🚨", "A": "📈", "B": "💡", "C": "👀"}
TYPE_LABEL = {"BUY": "매수", "SELL": "매도"}


async def send_message(text: str, chat_id: str | None = None) -> bool:
    """텔레그램 메시지 발송. 실패 시 최대 3회 재시도."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN 미설정 — 알림 건너뜀")
        return False

    target = chat_id or settings.TELEGRAM_CHAT_ID
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": target, "text": text, "parse_mode": "HTML"}

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return True
                logger.warning(f"텔레그램 발송 실패 {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.error(f"텔레그램 오류 (시도 {attempt+1}): {e}")
        await asyncio.sleep(2 ** attempt)

    return False


async def send_signal_alert(
    ticker: str, name: str, price: float,
    signal_type: str, grade: str, triggers: dict,
    target_price: float | None = None,
    stop_loss: float | None = None,
) -> bool:
    """기술적 신호 발생 알림 메시지 발송."""
    emoji = GRADE_EMOJI.get(grade, "📊")
    type_label = TYPE_LABEL.get(signal_type, signal_type)
    triggers_text = "\n".join(f"  • {k}: {v}" for k, v in triggers.items())

    lines = [
        f"{emoji} <b>[{grade}등급] {type_label} 타이밍!</b>",
        f"",
        f"📌 <b>{name}</b> ({ticker})",
        f"💰 현재가: <b>{price:,.0f}원</b>",
        f"",
        f"✅ 발생 신호 ({len(triggers)}개):",
        triggers_text,
    ]

    if target_price:
        pct = (target_price - price) / price * 100
        lines.append(f"\n🎯 목표가: {target_price:,.0f}원 (<b>+{pct:.1f}%</b>)")
    if stop_loss:
        pct = (stop_loss - price) / price * 100
        lines.append(f"⛔ 손절가: {stop_loss:,.0f}원 ({pct:.1f}%)")

    lines.append(f"\n⚠️ <i>본 정보는 투자 참고용입니다.</i>")

    return await send_message("\n".join(lines))


async def send_daily_recommendations(top5: list[dict]) -> bool:
    """일일 AI 추천 5종목 알림 발송."""
    lines = ["🤖 <b>오늘의 AI 추천 종목 TOP 5</b>\n"]
    for i, s in enumerate(top5, 1):
        prob = s.get("buy_probability", 0)
        lines.append(
            f"{i}. <b>{s.get('name','')}</b> ({s.get('ticker','')})\n"
            f"   매수확률 {prob}% | {s.get('one_line_summary','')}"
        )
    lines.append("\n⚠️ <i>투자 결정 및 손익 책임은 투자자 본인에게 있습니다.</i>")
    return await send_message("\n".join(lines))
