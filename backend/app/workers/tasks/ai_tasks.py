# =============================================================
# AI 분석 작업
#
# 매일 07:00 자동 실행:
#   전체 종목 → 30개 1차 필터 → 5개 최종 선정
#   LLM API 호출 → 분석 결과 DB 저장
# =============================================================

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def run_daily_ai_analysis(self):
    """
    [매일 07:00 실행] AI 2단계 종목 필터링을 실행합니다.

    처리 순서:
    1. 한국투자증권 API로 전체 상장 종목 데이터 수집
    2. 1차 필터: 재무지표 + 기술적 점수로 30개 선별
    3. 2차 필터: LLM API 호출로 최종 5개 선별
    4. 결과 DB 저장 + 사용자들에게 일일 추천 알림 발송
    """
    try:
        from app.services.ai_engine.daily_analyzer import DailyAnalyzer
        analyzer = DailyAnalyzer()
        result = analyzer.run_sync()
        logger.info(f"AI 분석 완료: 최종 {result.get('top5_count', 0)}종목 선정")
        return result
    except Exception as exc:
        logger.error(f"AI 분석 오류: {exc}")
        raise self.retry(exc=exc, countdown=300)   # 5분 후 재시도


@shared_task(bind=True)
def generate_weekly_report(self):
    """
    [매주 월요일 09:00 실행] AI 추천 성과 주간 리포트를 생성합니다.

    분석 항목:
    - 지난 주 추천 5종목의 실제 수익률
    - 기술적 신호 정확도 (신호 → 실제 방향 일치율)
    - 시뮬레이션 누적 성과
    - AI 신뢰도 점수 업데이트
    """
    try:
        from app.services.ai_engine.performance_reporter import PerformanceReporter
        reporter = PerformanceReporter()
        result = reporter.generate_weekly_sync()
        logger.info("주간 성과 리포트 생성 완료")
        return result
    except Exception as exc:
        logger.error(f"주간 리포트 오류: {exc}")
