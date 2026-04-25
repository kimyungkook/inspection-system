# LLM 클라이언트 — .env의 LLM_PROVIDER 값으로 AI 모델 교체
# claude / openai / gemini 중 1줄만 바꾸면 전환됨

import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# 공통 프롬프트 템플릿
ANALYSIS_PROMPT = """당신은 20년 경력의 전문 주식 애널리스트입니다.
다음 종목을 수익성/안전성/환금성 기준으로 분석하세요.

[종목 정보]
{stock_data}

반드시 아래 JSON 형식만 반환하세요. 다른 텍스트 없이 JSON만:
{{
  "recommendation": "strong_buy 또는 buy 또는 hold 또는 sell",
  "buy_probability": 0에서100사이정수,
  "target_price": 목표가숫자,
  "stop_loss_price": 손절가숫자,
  "expected_period_days": 예상기간일수,
  "factor_scores": {{
    "재무성장성": 0에서100,
    "경쟁우위": 0에서100,
    "밸류에이션": 0에서100,
    "투자자적합성": 0에서100
  }},
  "buy_reason": "구체적 매수 이유 3문장",
  "risk_reason": "주요 리스크 2문장",
  "one_line_summary": "초보자용 한 줄 요약"
}}"""


async def analyze_stock(stock_data: dict) -> dict:
    """종목 데이터를 LLM으로 분석. 설정된 provider에 따라 자동 라우팅."""
    provider = settings.LLM_PROVIDER
    prompt = ANALYSIS_PROMPT.format(stock_data=json.dumps(stock_data, ensure_ascii=False, indent=2))

    if provider == "claude":
        return await _call_claude(prompt)
    elif provider == "openai":
        return await _call_openai(prompt)
    elif provider == "gemini":
        return await _call_gemini(prompt)
    else:
        raise ValueError(f"지원하지 않는 LLM 제공자: {provider}")


async def _call_claude(prompt: str) -> dict:
    """Claude Sonnet API 호출."""
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    msg = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json(msg.content[0].text)


async def _call_openai(prompt: str) -> dict:
    """OpenAI GPT API 호출."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    resp = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    return _parse_json(resp.choices[0].message.content)


async def _call_gemini(prompt: str) -> dict:
    """Google Gemini API 호출."""
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    resp = await model.generate_content_async(prompt)
    return _parse_json(resp.text)


def _parse_json(text: str) -> dict:
    """LLM 응답에서 JSON 추출. 마크다운 코드블록 제거 후 파싱."""
    text = text.strip()
    # ```json ... ``` 블록 제거
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"LLM JSON 파싱 실패: {e}\n원문: {text[:200]}")
        return {}
