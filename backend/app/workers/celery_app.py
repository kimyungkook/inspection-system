# =============================================================
# Celery 설정 — 백그라운드 작업 관리자
#
# Celery = 앱이 돌아가는 동안 뒤에서 자동으로 일을 처리하는 일꾼
#
# 하는 일:
#   - 매일 07:00 AI 종목 분석 실행
#   - 1분마다 관심/보유 종목 기술적 지표 계산
#   - 신호 발생 즉시 알림 발송
#   - 장 마감 후 가상투자 포지션 평가
# =============================================================

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Celery 앱 생성
# broker = 작업을 받는 곳 (Redis)
# backend = 작업 결과를 저장하는 곳 (Redis)
celery_app = Celery(
    "stock_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.ai_tasks",
        "app.workers.tasks.signal_tasks",
        "app.workers.tasks.alert_tasks",
        "app.workers.tasks.simulation_tasks",
    ],
)

celery_app.conf.update(
    # 작업 직렬화 형식
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,

    # 작업 실패 시 재시도 설정
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_max_retries=3,

    # 정기 작업 스케줄 (Beat Scheduler)
    beat_schedule={

        # ① 매일 07:00 AI 전체 종목 분석 (장 시작 전)
        "daily-ai-analysis": {
            "task": "app.workers.tasks.ai_tasks.run_daily_ai_analysis",
            "schedule": crontab(hour=7, minute=0),
        },

        # ② 장중 1분마다 기술적 지표 계산 + 신호 감지
        #    평일 09:00 ~ 15:30 (한국 주식시장 운영 시간)
        "realtime-signal-detection": {
            "task": "app.workers.tasks.signal_tasks.detect_all_signals",
            "schedule": crontab(
                minute="*",
                hour="9-15",
                day_of_week="mon-fri",
            ),
        },

        # ③ 5분마다 관심/보유종목 지표 업데이트
        "update-tech-indicators": {
            "task": "app.workers.tasks.signal_tasks.update_tech_indicators",
            "schedule": crontab(
                minute="*/5",
                hour="9-15",
                day_of_week="mon-fri",
            ),
        },

        # ④ 장 마감 후 16:00 가상투자 포지션 일일 평가
        "daily-simulation-evaluation": {
            "task": "app.workers.tasks.simulation_tasks.evaluate_positions",
            "schedule": crontab(hour=16, minute=0, day_of_week="mon-fri"),
        },

        # ⑤ 매주 월요일 09:00 AI 성과 주간 리포트 생성
        "weekly-ai-performance-report": {
            "task": "app.workers.tasks.ai_tasks.generate_weekly_report",
            "schedule": crontab(hour=9, minute=0, day_of_week="mon"),
        },
    },
)
