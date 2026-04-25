# AI 2차 필터 — 30개 → 최종 5개 (LLM 심층 분석)
# LLM API를 호출해서 각 종목의 매수 확률 + 종합 판단 생성

import asyncio
import logging
from app.services.ai_engine.llm_client import analyze_stock

logger = logging.getLogger(__name__)


async def run_second_filter(candidates: list[dict]) -> list[dict]:
    """
    1차 필터 통과 30개 → LLM 병렬 분석 → 매수 확률 상위 5개 반환.
    비용 절감: 병렬 처리로 분석 시간 단축, 결과 캐싱.
    """
    logger.info(f"2차 AI 필터 시작 ({len(candidates)}개 → 5개)")

    # 최대 5개 동시 LLM 호출 (API 요청 제한 준수)
    semaphore = asyncio.Semaphore(5)

    async def analyze_with_limit(stock: dict) -> dict | None:
        async with semaphore:
            return await _analyze_single(stock)

    tasks = [analyze_with_limit(s) for s in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    analyzed = [r for r in results if isinstance(r, dict) and r.get("buy_probability", 0) > 0]

    # 매수 확률 내림차순 → 상위 5개
    analyzed.sort(key=lambda x: x["buy_probability"], reverse=True)
    top5 = analyzed[:5]

    logger.info(f"2차 필터 완료: {len(top5)}개 최종 선정")
    return top5


async def _analyze_single(stock: dict) -> dict | None:
    """단일 종목 LLM 분석."""
    ticker = stock.get("ticker", "")
    try:
        stock_data = {
            "종목코드": ticker,
            "종목명": stock.get("name", ""),
            "현재가": stock.get("current_price", 0),
            "정량점수": stock.get("total_score", 0),
            "재무지표": stock.get("financial", {}),
            "기술적지표": stock.get("indicators", {}),
        }
        result = await analyze_stock(stock_data)
        if not result:
            return None

        return {
            "ticker": ticker,
            "name": stock.get("name", ""),
            "current_price": stock.get("current_price", 0),
            "quant_score": stock.get("total_score", 0),
            **result,   # LLM 응답 병합 (recommendation, buy_probability, etc.)
        }
    except Exception as e:
        logger.error(f"{ticker} LLM 분석 실패: {e}")
        return None
