"""
관리자 모니터링 API — 관리자 계정만 접근 가능

GET /admin/stats          : 전체 현황 요약 (사용자 수, 신호 수, AI 분석 현황)
GET /admin/signals/recent : 최근 발생 신호 목록
GET /admin/users          : 전체 사용자 목록
GET /admin/ai/performance : AI 추천 누적 성과
POST /admin/ai/trigger    : AI 분석 즉시 실행 (수동 트리거)
POST /admin/celery/status : Celery Worker 상태 확인
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.dependencies import get_admin_user
from app.core.database import get_db
from app.models.user import User
from app.models.stock import Stock
from app.models.tech_signal import TechSignal, TechIndicator
from app.models.ai_analysis import AiAnalysis
from app.models.simulation import SimAccount, SimTrade
from app.models.alert import AlertLog

router = APIRouter(prefix="/admin", tags=["관리자"])


# ─────────────────────────────────────────────────────────────
# 전체 현황 요약
# ─────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """대시보드 핵심 통계 — 실시간 현황 한눈에 보기"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago    = now - timedelta(days=7)

    # 사용자 통계
    user_total_r = await db.execute(select(func.count(User.id)))
    user_total   = user_total_r.scalar()

    user_today_r = await db.execute(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    user_today = user_today_r.scalar()

    # 신호 통계 (오늘 / 이번 주)
    sig_today_r = await db.execute(
        select(func.count(TechSignal.id)).where(
            TechSignal.detected_at >= today_start
        )
    )
    sig_today = sig_today_r.scalar()

    sig_week_r = await db.execute(
        select(func.count(TechSignal.id)).where(
            TechSignal.detected_at >= week_ago
        )
    )
    sig_week = sig_week_r.scalar()

    # 등급별 신호 분포
    grade_r = await db.execute(
        select(TechSignal.grade, func.count(TechSignal.id))
        .where(TechSignal.detected_at >= week_ago)
        .group_by(TechSignal.grade)
    )
    grade_dist = {row[0].value: row[1] for row in grade_r.all()}

    # AI 분석 최근 실행 시각
    ai_latest_r = await db.execute(
        select(AiAnalysis.analyzed_at)
        .order_by(desc(AiAnalysis.analyzed_at))
        .limit(1)
    )
    ai_latest = ai_latest_r.scalar()

    # 가상투자 총 계좌 수
    sim_count_r = await db.execute(
        select(func.count(SimAccount.id)).where(SimAccount.is_active.is_(True))
    )
    sim_count = sim_count_r.scalar()

    # 오늘 발송 알림 수
    alert_today_r = await db.execute(
        select(func.count(AlertLog.id)).where(
            AlertLog.created_at >= today_start,
            AlertLog.is_sent.is_(True),
        )
    )
    alert_today = alert_today_r.scalar()

    return {
        "users": {
            "total":       user_total,
            "joined_today": user_today,
        },
        "signals": {
            "today":        sig_today,
            "this_week":    sig_week,
            "grade_dist":   grade_dist,
        },
        "ai_analysis": {
            "last_run":     ai_latest.isoformat() if ai_latest else None,
        },
        "simulation": {
            "active_accounts": sim_count,
        },
        "alerts": {
            "sent_today": alert_today,
        },
        "server_time": now.isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# 최근 신호 목록
# ─────────────────────────────────────────────────────────────

@router.get("/signals/recent")
async def get_recent_signals(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """최근 발생한 기술적 신호 목록 (최대 50건)"""
    r = await db.execute(
        select(TechSignal, Stock)
        .join(Stock, TechSignal.stock_id == Stock.id)
        .order_by(desc(TechSignal.detected_at))
        .limit(max(1, min(limit, 200)))
    )
    rows = r.all()

    return [
        {
            "id":          ts.id,
            "ticker":      s.ticker,
            "name":        s.name,
            "signal_type": ts.signal_type.value,
            "grade":       ts.grade.value,
            "price":       float(ts.price_at_signal),
            "indicators":  ts.indicators_triggered,
            "alert_sent":  ts.alert_sent,
            "detected_at": ts.detected_at.isoformat(),
        }
        for ts, s in rows
    ]


# ─────────────────────────────────────────────────────────────
# 사용자 목록
# ─────────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """전체 사용자 목록 (비밀번호 등 민감 정보 제외)"""
    r = await db.execute(
        select(User).order_by(desc(User.created_at)).limit(max(1, min(limit, 500)))
    )
    users = r.scalars().all()

    return [
        {
            "id":         u.id,
            "username":   u.username,
            "email":      u.email,
            "tier":       u.tier,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


# ─────────────────────────────────────────────────────────────
# AI 추천 성과 현황
# ─────────────────────────────────────────────────────────────

@router.get("/ai/performance")
async def get_ai_performance(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    """AI top5 추천 종목의 누적 성과 현황"""
    r = await db.execute(
        select(AiAnalysis, Stock)
        .join(Stock, AiAnalysis.stock_id == Stock.id)
        .where(AiAnalysis.is_top5 == 1)
        .order_by(desc(AiAnalysis.analyzed_at))
        .limit(30)   # 최근 6주치 (주 5회 × 6주)
    )
    rows = r.all()

    return [
        {
            "ticker":           s.ticker,
            "name":             s.name,
            "recommendation":   a.recommendation.value,
            "buy_probability":  a.buy_probability,
            "target_price":     float(a.target_price)     if a.target_price     else None,
            "stop_loss_price":  float(a.stop_loss_price)  if a.stop_loss_price  else None,
            "one_line_summary": a.one_line_summary,
            "analyzed_at":      a.analyzed_at.isoformat(),
        }
        for a, s in rows
    ]


# ─────────────────────────────────────────────────────────────
# AI 분석 즉시 실행 (수동 트리거)
# ─────────────────────────────────────────────────────────────

@router.post("/ai/trigger")
async def trigger_ai_analysis(
    _: User = Depends(get_admin_user),
):
    """
    AI 종목 분석을 즉시 실행합니다.
    Celery 큐에 태스크를 등록하고 task_id를 반환합니다.
    """
    try:
        from app.workers.tasks.ai_tasks import run_daily_ai_analysis
        task = run_daily_ai_analysis.delay()
        return {
            "message": "AI 분석 태스크가 큐에 등록되었습니다.",
            "task_id": task.id,
            "status":  "queued",
        }
    except Exception as e:
        raise HTTPException(500, f"태스크 등록 실패: {e}")


# ─────────────────────────────────────────────────────────────
# 신호 감지 즉시 실행 (수동 트리거)
# ─────────────────────────────────────────────────────────────

@router.post("/signals/trigger")
async def trigger_signal_detection(
    _: User = Depends(get_admin_user),
):
    """신호 감지를 즉시 실행합니다."""
    try:
        from app.workers.tasks.signal_tasks import detect_all_signals
        task = detect_all_signals.delay()
        return {
            "message": "신호 감지 태스크가 큐에 등록되었습니다.",
            "task_id": task.id,
            "status":  "queued",
        }
    except Exception as e:
        raise HTTPException(500, f"태스크 등록 실패: {e}")
