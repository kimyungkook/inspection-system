# =============================================================
# 가상투자 시뮬레이션 작업
# 장 마감 후 보유 포지션의 손익을 실시간 시세로 재계산
# =============================================================

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def evaluate_positions(self):
    """
    [매일 16:00 실행] 전체 사용자의 가상 보유 포지션을 평가합니다.

    처리 내용:
    - 보유 중인 모든 가상 포지션의 현재가 업데이트
    - 평가손익 재계산
    - 손절가/목표가 도달 종목 자동 청산 처리
    - 계좌 전체 수익률 업데이트
    """
    try:
        from app.services.sim_engine.position_evaluator import PositionEvaluator
        evaluator = PositionEvaluator()
        result = evaluator.evaluate_all_sync()
        logger.info(f"포지션 평가 완료: {result.get('evaluated', 0)}개 포지션")
        return result
    except Exception as exc:
        logger.error(f"포지션 평가 오류: {exc}")
        raise self.retry(exc=exc, countdown=120)
