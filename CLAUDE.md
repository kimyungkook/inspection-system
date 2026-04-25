# AI 주식 매매 가이드 앱 — 프로젝트 인수인계 파일

> 이 파일을 읽으면 이전 대화 내용 없이도 바로 이어서 작업 가능합니다.
> 새 대화 시작 시 → "CLAUDE.md 읽고 이어서 작업해줘" 라고 말하면 됩니다.

---

## 프로젝트 기본 정보

- **프로젝트명**: AI 주식 매매 가이드 앱
- **목적**: AI가 실제 주식 종목을 분석하고 매수/매도 타이밍을 알림으로 알려주는 앱
- **최종 목표**: AI 타이밍 신호로 실제 투자 시 수익 극대화 / 손실 최소화 검증
- **개발 진행 상태**: Phase 1~4 완료 → Phase 5(테스트 + 출시) 진행 중

---

## 확정된 기술 결정사항

| 항목 | 결정 내용 |
|------|-----------|
| 증권사 API | 한국투자증권 KIS API (실제 데이터, Mock 데이터 사용 안 함) |
| AI 모델 | Claude Sonnet API (기본값, 변경 가능) |
| AI 교체 방식 | .env 파일 1줄만 바꾸면 Gemini / OpenAI로 교체 가능 |
| 운영체제 | 윈도우 10 |
| 가상계좌 금액 | 사용자가 직접 설정 |
| Mock 데이터 | 사용 안 함 — 처음부터 실제 API 연동 |
| 자동매매 | 법적 이유로 제외 → 가상투자 시뮬레이션으로 대체 |
| 알림 채널 | 텔레그램 봇 (먼저), 카카오 알림톡 (나중에), FCM 푸시 |

---

## 사용자 환경 정보

- 코딩 지식: 없음
- 프로그램 설치 경험: 기초 수준
- 영어 프로그램: 어려움 → 모든 설명은 한글로
- 컴퓨터: 윈도우 10
- 한국투자증권 계좌: 발급 예정 (아직 없음)
- Claude API 키: 미발급 (발급 예정)
- Claude.ai Pro: 유료 구독 중 (API와는 별도 요금)

---

## 앱 구조 요약

### 하단 탭 8개
1. 대시보드 — AI 추천 5종목 요약, 시장 분위기
2. 통합검색 — 종목명/업종/자연어 검색
3. 주식현재가 — 실시간 시세 + 기술적 신호 등급
4. 관심종목 — 저장 종목 + 신호 알림
5. 비교분석 — 최대 4종목 동시 비교
6. **가상투자 시뮬레이션** — 가상 돈으로 실제 종목 투자 테스트
7. 자산평가 — 실투자 포트폴리오 관리
8. 설정 — API 키, 알림 설정, 가상계좌 초기화
9. **자비스 (FAB 버튼)** — 음성 AI 어시스턴트 (STT → LLM → TTS)

### 핵심 기능
- AI 2단계 필터링: 전체 종목 → 30개 → 최종 5개
- 기술적 지표 실시간 분석: RSI, MACD, 볼린저밴드, 이동평균선, 스토캐스틱, OBV, 거래량
- 신호 등급: S(강력매수) / A(매수적기) / B(매수검토) / C(관찰)
- 알림: 신호 발생 후 60초 이내 발송 (절대 타이밍 놓치지 않음)
- 가상투자 검증: 3개월 시뮬레이션 후 AI 신뢰도 점수로 실투자 판단

---

## 기술 스택

| 구분 | 기술 | 설명 |
|------|------|------|
| 백엔드 서버 | FastAPI (Python) | 앱의 두뇌 역할 |
| 데이터베이스 | PostgreSQL 15 | 모든 정보 저장소 |
| 임시저장소 | Redis 7 | 빠른 알림 처리용 |
| 비동기 작업 | Celery | 실시간 지표 계산, 알림 발송 |
| 모바일 앱 | Flutter | iOS + Android 동시 지원 |
| 관리자 웹 | Next.js | 브라우저에서 통계/모니터링 |
| 실행 환경 | Docker Desktop | 명령어 1줄로 전체 실행 |
| AI 엔진 | Claude Sonnet API | 종목 분석 및 추천 |
| 보안 | AES256 + bcrypt + JWT + OTP | 금융 수준 보안 |

---

## 월 예상 운영 비용

| 단계 | 사용자 수 | 월 비용 |
|------|----------|---------|
| 개인 테스트 | 1~5명 | 약 4~7만원 |
| 초기 운영 | ~50명 | 약 11~16만원 |
| 본격 운영 | ~100명 | 약 14~21만원 |

---

## 8주 개발 로드맵

```
Phase 1 (1-2주): DB 설계 + 보안/인증 시스템              ✅ 완료
Phase 2 (3-4주): 한국투자증권 API 연동 + AI 분석 엔진     ✅ 완료
Phase 2.5 (4주 후반): 기술적 지표 실시간 계산 엔진        ✅ 완료
Phase 3 (5-6주): Flutter 앱 화면 8개 구현                ✅ 완료
Phase 3.5 (6주 후반): 가상투자 시뮬레이션 모듈           ✅ 완료
Phase 3.6 (추가): 자비스 음성 AI 어시스턴트              ✅ 완료
Phase 4 (7주): 알림 시스템 + 관리자 페이지               ✅ 완료
Phase 5 (8주): 테스트 + 출시                             ⬜ 다음 작업
```

---

## 현재 진행 상태

- [x] 전체 기획 완료
- [x] 아키텍처 설계 완료
- [x] 기술 스택 결정 완료
- [x] Phase 1: DB 설계 + 인증 시스템 완료
- [x] Phase 2: KIS API 연동 + AI 분석 엔진 완료
- [x] Phase 2.5: 기술적 지표 실시간 계산 엔진 완료
- [x] Phase 3: Flutter 앱 화면 8개 완료
- [x] Phase 3.5: 가상투자 시뮬레이션 완료
- [x] Phase 3.6: 자비스 음성 AI 어시스턴트 완료
- [x] Phase 4: Celery 태스크 + 알림 + 관리자 API 완료
- [ ] Phase 5: 테스트 + 출시 — **다음 작업**
- [ ] 한국투자증권 API 키 발급 (사용자 준비 중)
- [ ] Claude API 키 발급 (사용자 준비 중)

---

## 완성된 주요 파일 목록

### 백엔드 (backend/)
```
app/main.py                                  ← FastAPI 앱 진입점 (모든 라우터 등록)
app/core/config.py                           ← 환경변수 설정
app/core/database.py                         ← PostgreSQL 연결
app/core/redis_client.py                     ← Redis 연결
app/models/                                  ← DB 테이블 정의
  user.py, stock.py, tech_signal.py,
  ai_analysis.py, simulation.py, alert.py,
  watchlist.py
app/api/v1/
  auth/router.py                             ← 회원가입/로그인/초대코드
  stocks/router.py                           ← 주식 검색/시세/지표
  ai/router.py                               ← AI 추천 top5
  voice/router.py                            ← 자비스 음성 AI (POST /voice/query)
  simulation/router.py                       ← 가상투자 계좌/매매
  signals/router.py                          ← 신호 이력 조회
  admin/router.py                            ← 관리자 통계/트리거
app/workers/tasks/
  signal_tasks.py                            ← 신호 감지 (매 5분)
  alert_tasks.py                             ← 텔레그램 알림 발송
  simulation_tasks.py                        ← 포지션 평가 + 자동청산
  ai_tasks.py                               ← AI 분석 + 주간 리포트
app/services/
  kis_api/client.py                          ← KIS API 연동
  ai_engine/daily_analyzer.py               ← AI 2단계 필터링
  notification/telegram.py                  ← 텔레그램 발송
```

### Flutter 앱 (flutter_app/lib/)
```
main.dart                                    ← 앱 진입점
core/
  theme/app_theme.dart                       ← 다크 테마
  router/app_router.dart                     ← go_router 라우팅
  api/api_client.dart                        ← Dio HTTP 클라이언트
presentation/
  shell/main_shell.dart                      ← BottomAppBar + 자비스 FAB
  dashboard/dashboard_screen.dart            ← AI top5 대시보드
  stocks/stock_search_screen.dart            ← 종목 검색
  watchlist/watchlist_screen.dart            ← 관심종목 관리
  simulation/simulation_screen.dart          ← 가상투자
  compare/compare_screen.dart                ← 최대 4종목 비교
  portfolio/portfolio_screen.dart            ← 실투자 포트폴리오
  settings/settings_screen.dart              ← 앱 설정
  voice/voice_screen.dart                    ← 자비스 음성 UI
```

### 인프라
```
docker-compose.yml                           ← 전체 실행 (DB + Redis + API + Celery)
앱시작.bat                                   ← 윈도우 더블클릭으로 앱 시작
앱중지.bat                                   ← 앱 안전 종료
.github/workflows/build-apk.yml             ← GitHub Actions APK 자동빌드
```

---

## 다음에 이어서 할 작업 (Phase 5)

**Phase 5: 테스트 + 최종 점검 + 출시 준비**
1. `.env.example` 파일 작성 (사용자가 키만 입력하면 되는 템플릿)
2. Docker Compose 최종 검증 (모든 서비스 정상 기동 확인)
3. Flutter 앱 빌드 최종 확인 (pubspec.yaml 의존성 점검)
4. API 엔드포인트 전체 테스트 (`/docs` 화면에서)
5. 텔레그램 알림 테스트 발송
6. KIS API 연결 테스트 (실제 키 발급 후)
7. 사용자 가이드 작성 (설치부터 첫 실행까지)

---

## 사용자에게 드리는 안내

### Claude API 키 발급 방법
1. `console.anthropic.com` 접속
2. 구글 계정으로 회원가입
3. API Keys → Create Key 클릭
4. 발급된 키 메모장에 저장
5. 카드 등록 (사용한 만큼만 청구, 월 1~3만원 예상)

### 한국투자증권 API 키 발급 방법
1. 한국투자증권 앱 또는 홈페이지 접속
2. KIS Developers 메뉴 찾기
3. 앱 등록 → 앱키 + 앱시크릿 발급
4. 메모장에 저장

### Docker Desktop 설치 방법
1. `docker.com` 접속 → Windows 버전 다운로드
2. 설치 파일 실행 → 다음다음완료
3. 컴퓨터 재시작

### 앱 실행 방법 (설치 후)
1. `앱시작.bat` 더블클릭
2. 브라우저에서 `http://localhost:8000/docs` 자동 열림
3. 앱 종료 시: `앱중지.bat` 더블클릭

---

## 개발 시 주의사항 (Claude에게)

- 모든 설명은 한글로 작성
- 전문용어 사용 시 괄호 안에 한글 설명 추가
- 설치/실행 방법은 번호 붙여서 단계별로
- 코드 파일 작성 후 "이 파일이 하는 역할" 한 줄 설명
- Mock 데이터 절대 사용 금지 — 처음부터 실제 API 연동
- LLM은 .env 파일 1줄로 교체 가능하게 설계 (claude/openai/gemini)
- 사용자는 코딩 지식 없음 — 코드 직접 수정 불필요하게 설계
- Celery 태스크: 항상 asyncio.run() 사용, 절대 get_event_loop() 사용 금지
- DB 세션: 항상 async with AsyncSessionLocal() as db: 패턴 사용
- Decimal: 모든 금액 계산은 Python Decimal 사용 (float 정밀도 오류 방지)
