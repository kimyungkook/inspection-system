"""
데모 데이터 자동 입력 모듈
DEMO_MODE=true 일 때 앱 시작 시 자동으로 실행됩니다.

입력 데이터:
  - 한국 대표 주식 20종목
  - 데모 관리자 계정 (admin / demo1234!)
  - AI 추천 top5 종목
  - 기술적 신호 샘플 (S/A/B 등급)
  - 기술적 지표 현재값
  - 관심종목 5개
  - 가상투자 계좌 + 포지션 3개
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 데모 종목 목록 (mock_client.py 와 동일하게 유지)
# ─────────────────────────────────────────────────────────────
DEMO_STOCKS = [
    ("005930", "삼성전자",         "반도체/전자",   55000,   2_000_000_000_000),
    ("000660", "SK하이닉스",        "반도체",        185000,  1_350_000_000_000),
    ("035420", "NAVER",            "IT/인터넷",     195000,    320_000_000_000),
    ("035720", "카카오",            "IT/플랫폼",     42000,    190_000_000_000),
    ("005380", "현대차",            "자동차",        195000,    420_000_000_000),
    ("000270", "기아",              "자동차",        93000,    380_000_000_000),
    ("373220", "LG에너지솔루션",    "2차전지",       295000,    690_000_000_000),
    ("207940", "삼성바이오로직스",  "바이오",        880000,    620_000_000_000),
    ("068270", "셀트리온",          "바이오",        155000,    215_000_000_000),
    ("005490", "POSCO홀딩스",      "철강/소재",     290000,    250_000_000_000),
    ("105560", "KB금융",            "금융",          85000,    360_000_000_000),
    ("055550", "신한지주",          "금융",          52000,    270_000_000_000),
    ("006400", "삼성SDI",           "2차전지",       220000,    160_000_000_000),
    ("051910", "LG화학",            "화학/소재",     265000,    190_000_000_000),
    ("012330", "현대모비스",        "자동차부품",    235000,    225_000_000_000),
    ("323410", "카카오뱅크",        "핀테크",        22000,    105_000_000_000),
    ("259960", "크래프톤",          "게임",          250000,    125_000_000_000),
    ("086520", "에코프로",          "2차전지 소재",  95000,     86_000_000_000),
    ("034020", "두산에너빌리티",    "원전/에너지",   26000,     68_000_000_000),
    ("267260", "HD현대일렉트릭",    "전력기기",      235000,    157_000_000_000),
]

# AI top5 추천 종목 (ticker, recommendation, prob, target, stop, summary)
AI_TOP5 = [
    ("000660", "strong_buy", 92, 215000, 172000, "HBM 수요 급증으로 실적 서프라이즈 기대, 강력 매수 구간"),
    ("267260", "buy",        87, 280000, 218000, "전력기기 수퍼사이클 초입, 해외 수주 급증으로 성장 지속"),
    ("034020", "buy",        84, 31000,  24000,  "SMR 원전 기대감 + 체코 수주로 재평가 구간 진입"),
    ("086520", "buy",        81, 115000, 88000,  "양극재 판가 반등 + 전기차 수요 회복으로 반전 시점"),
    ("005930", "buy",        78, 68000,  51000,  "반도체 HBM 전환 가속, AI 투자 수혜 본격화 예상"),
]

# 기술적 신호 샘플
DEMO_SIGNALS = [
    # (ticker, signal_type, grade, indicators, price)
    ("000660", "BUY", "S", {"RSI": "28 (과매도)", "MACD": "골든크로스", "볼린저밴드": "하단 돌파 반등", "거래량": "380% 급증", "이동평균선": "20일선 지지"}, 185000),
    ("267260", "BUY", "A", {"RSI": "32 (과매도 근접)", "MACD": "골든크로스", "거래량": "250% 급증", "이동평균선": "5일선 상향돌파"}, 235000),
    ("034020", "BUY", "A", {"RSI": "35", "볼린저밴드": "하단 터치 반등", "OBV": "지속 상승", "거래량": "180% 증가"}, 26000),
    ("005930", "BUY", "B", {"RSI": "38", "MACD": "히스토그램 플러스 전환"}, 55000),
    ("035720", "SELL", "B", {"RSI": "72 (과매수)", "볼린저밴드": "상단 초과"}, 42000),
    ("323410", "SELL", "A", {"RSI": "78 (과매수)", "MACD": "데드크로스", "거래량": "120% 감소", "이동평균선": "5일선 하향이탈"}, 22000),
]


async def seed_demo_data() -> None:
    """데모 데이터를 DB에 입력합니다. 이미 입력된 경우 건너뜁니다."""
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.user import User, UserTier
    from app.models.stock import Stock, StockMarket
    from app.models.tech_signal import TechSignal, TechIndicator, SignalType, SignalGrade
    from app.models.ai_analysis import AiAnalysis, Recommendation
    from app.models.watchlist import Watchlist
    from app.models.simulation import SimAccount, SimPosition

    async with AsyncSessionLocal() as db:
        # ① 이미 입력됐으면 건너뛰기
        exist_r = await db.execute(select(Stock).limit(1))
        if exist_r.scalar_one_or_none():
            logger.info("[데모] 데이터 이미 존재 — 시더 건너뜀")
            return

        logger.info("[데모] 샘플 데이터 입력 시작...")

        # ② 주식 종목 20개 입력
        stock_map: dict[str, Stock] = {}
        for ticker, name, sector, price, cap in DEMO_STOCKS:
            s = Stock(
                ticker=ticker, name=name, name_en=name,
                market=StockMarket.KR, sector=sector,
                market_cap=cap, is_active=True,
                last_price=Decimal(str(price)),
                last_updated=datetime.now(timezone.utc),
            )
            db.add(s)
            stock_map[ticker] = s

        await db.flush()

        # ③ 데모 관리자 계정 생성
        from passlib.context import CryptContext
        pwd_ctx = CryptContext(schemes=["bcrypt"])
        admin = User(
            username="admin",
            email="admin@demo.com",
            password_hash=pwd_ctx.hash("demo1234!"),
            tier=UserTier.VIP,
            is_active=True,
            is_admin=True,
        )
        db.add(admin)

        demo_user = User(
            username="demo",
            email="demo@demo.com",
            password_hash=pwd_ctx.hash("demo1234!"),
            tier=UserTier.PREMIUM,
            is_active=True,
            is_admin=False,
        )
        db.add(demo_user)
        await db.flush()

        # ④ 관심종목 5개 (demo 계정)
        watchlist_tickers = ["005930", "000660", "267260", "034020", "086520"]
        for t in watchlist_tickers:
            db.add(Watchlist(user_id=demo_user.id, stock_id=stock_map[t].id))

        # ⑤ AI 분석 top5 입력
        now = datetime.now(timezone.utc)
        rec_map = {
            "strong_buy": Recommendation.STRONG_BUY,
            "buy": Recommendation.BUY,
            "hold": Recommendation.HOLD,
            "sell": Recommendation.SELL,
        }
        for ticker, rec_str, prob, target, stop, summary in AI_TOP5:
            s = stock_map[ticker]
            price = int(str(s.last_price).split(".")[0])
            db.add(AiAnalysis(
                stock_id=s.id,
                recommendation=rec_map[rec_str],
                buy_probability=prob,
                target_price=Decimal(str(target)),
                stop_loss_price=Decimal(str(stop)),
                expected_period_days=20,
                one_line_summary=summary,
                buy_reason=f"{s.name}의 펀더멘털 개선과 기술적 지표가 동시에 긍정적 신호를 보내고 있습니다. 목표가 {target:,}원까지 상승 여력이 충분합니다.",
                risk_reason="글로벌 경기 둔화와 환율 변동이 주요 리스크입니다. 손절가를 반드시 설정하세요.",
                factor_scores={"재무성장성": prob-5, "경쟁우위": prob-8, "밸류에이션": prob-12, "투자자프로필": prob},
                llm_model="demo-mode",
                is_top30=1,
                is_top5=1,
                analyzed_at=now - timedelta(hours=2),
            ))

        # ⑥ 기술적 신호 입력
        grade_map = {"S": SignalGrade.S, "A": SignalGrade.A, "B": SignalGrade.B, "C": SignalGrade.C}
        type_map  = {"BUY": SignalType.BUY, "SELL": SignalType.SELL}
        for idx, (ticker, sig_type, grade, indicators, price) in enumerate(DEMO_SIGNALS):
            s = stock_map[ticker]
            ts = TechSignal(
                stock_id=s.id,
                signal_type=type_map[sig_type],
                grade=grade_map[grade],
                indicators_triggered=indicators,
                indicator_count=len(indicators),
                price_at_signal=Decimal(str(price)),
                alert_sent=(grade in ("S", "A", "B")),
                detected_at=now - timedelta(minutes=idx * 15),
            )
            db.add(ts)

        # ⑦ 기술적 지표 현재값 입력 (상위 10종목)
        import random
        for ticker in list(stock_map.keys())[:10]:
            s = stock_map[ticker]
            price = float(s.last_price)
            db.add(TechIndicator(
                stock_id=s.id,
                timeframe="5m",
                current_price=Decimal(str(price)),
                volume=Decimal("850000"),
                volume_ratio=Decimal(str(round(random.uniform(80, 300), 2))),
                rsi=Decimal(str(round(random.uniform(28, 72), 2))),
                macd_line=Decimal(str(round(random.uniform(-500, 500), 2))),
                macd_signal=Decimal(str(round(random.uniform(-400, 400), 2))),
                macd_hist=Decimal(str(round(random.uniform(-200, 200), 2))),
                bb_upper=Decimal(str(round(price * 1.02))),
                bb_middle=Decimal(str(round(price))),
                bb_lower=Decimal(str(round(price * 0.98))),
                ma5=Decimal(str(round(price * random.uniform(0.995, 1.005)))),
                ma20=Decimal(str(round(price * random.uniform(0.985, 1.015)))),
                ma60=Decimal(str(round(price * random.uniform(0.97, 1.03)))),
                ma120=Decimal(str(round(price * random.uniform(0.95, 1.05)))),
                stoch_k=Decimal(str(round(random.uniform(20, 80), 2))),
                stoch_d=Decimal(str(round(random.uniform(20, 80), 2))),
                obv=Decimal(str(round(random.uniform(1_000_000, 50_000_000)))),
                updated_at=now,
            ))

        # ⑧ 가상투자 계좌 + 포지션 (demo 계정)
        sim_acct = SimAccount(
            user_id=demo_user.id,
            name="데모 투자 계좌",
            initial_balance=Decimal("10000000"),
            virtual_balance=Decimal("7850000"),
            total_profit_loss=Decimal("1250000"),
            profit_rate=Decimal("12.50"),
            is_active=True,
        )
        db.add(sim_acct)
        await db.flush()

        # 보유 포지션 3개
        positions = [
            ("005930", 30, 52000, 68000, 48000),   # 삼성전자 30주
            ("000660", 5,  175000, 215000, 165000),  # SK하이닉스 5주
            ("267260", 3,  220000, 280000, 205000),  # HD현대일렉트릭 3주
        ]
        for ticker, qty, avg_price, target_p, stop_p in positions:
            s = stock_map[ticker]
            curr = float(s.last_price)
            pnl_rate = (curr - avg_price) / avg_price * 100
            pnl = Decimal(str((curr - avg_price) * qty))
            db.add(SimPosition(
                account_id=sim_acct.id,
                stock_id=s.id,
                quantity=qty,
                avg_buy_price=Decimal(str(avg_price)),
                current_price=s.last_price,
                unrealized_pnl=pnl,
                unrealized_pnl_rate=Decimal(str(round(pnl_rate, 4))),
                take_profit_price=Decimal(str(target_p)),
                stop_loss_price=Decimal(str(stop_p)),
            ))

        await db.commit()
        logger.info("[데모] 샘플 데이터 입력 완료 ✓ (종목 20개, 신호 %d개, top5 AI 추천)", len(DEMO_SIGNALS))
