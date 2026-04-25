# =============================================================
# 기술적 신호 감지 작업
#
# 1분마다 자동 실행:
#   전체 관심/보유 종목의 RSI, MACD, 볼린저밴드 등을 계산하고
#   매수/매도 신호 발생 시 즉시 알림 큐에 등록
# =============================================================

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def detect_all_signals(self):
    """
    [1분마다 실행] 전체 모니터링 종목의 기술적 신호를 감지합니다.

    처리 순서:
    1. DB에서 모니터링 대상 종목 목록 가져오기
       (AI 추천 5종목 + 모든 사용자 관심종목 + 가상투자 보유종목)
    2. 한국투자증권 API로 현재가 + 분봉 데이터 조회
    3. 각 지표 계산 (RSI, MACD, 볼린저밴드, 이동평균, 스토캐스틱, OBV)
    4. 신호 등급 산출 (S/A/B/C)
    5. 새 신호 발생 시 → 알림 발송 태스크 즉시 실행
    """
    try:
        from app.services.tech_engine.signal_detector import SignalDetector
        detector = SignalDetector()
        result = detector.run_sync()
        logger.info(f"신호 감지 완료: {result.get('signals_found', 0)}개 신호 발생")
        return result
    except Exception as exc:
        logger.error(f"신호 감지 오류: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def update_tech_indicators(self):
    """
    [5분마다 실행] 전체 종목의 기술적 지표 값을 DB에 저장합니다.
    앱에서 차트를 볼 때 이 데이터를 사용합니다.
    """
    try:
        from app.services.tech_engine.indicator_calculator import IndicatorCalculator
        calc = IndicatorCalculator()
        result = calc.update_all_sync()
        logger.info(f"지표 업데이트 완료: {result.get('updated', 0)}개 종목")
        return result
    except Exception as exc:
        logger.error(f"지표 업데이트 오류: {exc}")
        raise self.retry(exc=exc, countdown=60)
