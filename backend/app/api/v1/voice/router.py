"""
음성 AI 어시스턴트 '자비스' — 자연어 질문을 받아 음성용 답변 반환
"""
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.auth.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/voice", tags=["음성 AI 자비스"])
logger = logging.getLogger(__name__)

# 자비스 페르소나 프롬프트
_SYSTEM = """당신은 AI 주식 투자 어시스턴트 '자비스'입니다.
규칙:
1. 반드시 한국어로만 답변
2. 2~3문장으로 간결하게 (음성으로 읽기 좋게)
3. 주식 수치나 지표 질문에는 구체적인 수치 포함
4. 투자 결정 조언 시 '최종 판단은 투자자 본인의 몫'이라 언급
5. 모르는 것은 솔직하게 모른다고 답변
6. 친근하고 신뢰감 있는 전문가 톤 유지"""


class VoiceQuery(BaseModel):
    query: str


@router.post("/query")
async def voice_query(
    body: VoiceQuery,
    current_user=Depends(get_current_user),
):
    """음성 질문 → AI 자연어 답변"""
    response = await _ask(body.query)
    return {"response": response}


async def _ask(query: str) -> str:
    prompt = f"{_SYSTEM}\n\n사용자: {query}\n자비스:"
    provider = settings.LLM_PROVIDER
    try:
        if provider == "claude":
            return await _claude(prompt)
        elif provider == "openai":
            return await _openai(prompt)
        elif provider == "gemini":
            return await _gemini(prompt)
        return "설정된 AI 제공자를 찾을 수 없습니다."
    except Exception as e:
        logger.error(f"자비스 LLM 오류: {e}")
        return "죄송합니다, 지금은 답변드리기 어렵습니다. 잠시 후 다시 시도해 주세요."


async def _claude(prompt: str) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    msg = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


async def _openai(prompt: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    resp = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
    )
    return resp.choices[0].message.content.strip()


async def _gemini(prompt: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    resp = await model.generate_content_async(prompt)
    return resp.text.strip()
