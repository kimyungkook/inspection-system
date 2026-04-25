# =============================================================
# 알림 발송 작업
# 신호 발생 즉시 호출 — 목표: 60초 이내 발송
# =============================================================

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, queue="alerts")
def send_signal_alert(self, stock_id: int, signal_type: str, grade: str, indicators: dict, price: float):
    """
    [즉시 실행] 기술적 신호 발생 알림을 발송합니다.

    S등급: 즉시 발송 (모든 채널)
    A등급: 즉시 발송 (텔레그램 + 푸시)
    B등급: 즉시 발송 (텔레그램)
    C등급: 사용자 설정에 따라
    """
    try:
        from app.services.notification.alert_sender import AlertSender
        sender = AlertSender()
        result = sender.send_signal_sync(
            stock_id=stock_id,
            signal_type=signal_type,
            grade=grade,
            indicators=indicators,
            price=price,
        )
        logger.info(f"알림 발송 완료: stock={stock_id} grade={grade}")
        return result
    except Exception as exc:
        logger.error(f"알림 발송 실패: {exc}")
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=3)
def send_daily_recommendation(self, top5_stock_ids: list):
    """[매일 07:30] AI 일일 추천 5종목 알림을 발송합니다."""
    try:
        from app.services.notification.alert_sender import AlertSender
        sender = AlertSender()
        sender.send_daily_recommendation_sync(top5_stock_ids)
        logger.info("일일 추천 알림 발송 완료")
    except Exception as exc:
        logger.error(f"일일 추천 알림 실패: {exc}")
        raise self.retry(exc=exc, countdown=60)
