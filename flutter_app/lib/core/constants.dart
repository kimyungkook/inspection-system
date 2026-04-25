class AppConst {
  // 개발: 로컬 Docker / 배포: 실제 서버 주소로 변경
  static const baseUrl = 'http://localhost:8000/api/v1';

  // 토큰 저장 키
  static const keyAccess  = 'access_token';
  static const keyRefresh = 'refresh_token';
  static const keyUserId  = 'user_id';
  static const keyTier    = 'user_tier';

  // 타임아웃
  static const connectTimeout = Duration(seconds: 10);
  static const receiveTimeout = Duration(seconds: 30);
}

class ApiPath {
  // 인증
  static const signup        = '/auth/signup';
  static const login         = '/auth/login';
  static const refresh       = '/auth/refresh';
  static const me            = '/auth/me';
  static const logout        = '/auth/logout';
  static const inviteCode    = '/auth/invite-code';
  static const changePw      = '/auth/change-password';

  // 주식
  static String price(String t)      => '/stocks/$t/price';
  static String indicators(String t) => '/stocks/$t/indicators';
  static String candles(String t)    => '/stocks/$t/candles';
  static const watchlist             = '/stocks/watchlist';
  static String addWatch(String t)   => '/stocks/watchlist/$t';
  static String delWatch(int id)     => '/stocks/watchlist/$id';

  // AI 분석
  static const aiTop5       = '/ai/recommendations';
  static const aiTop30      = '/ai/recommendations/top30';
  static String aiAnalyze(String t) => '/ai/analyze/$t';
  static const aiPerf       = '/ai/performance';

  // 시뮬레이션 (Phase 3.5에서 추가 예정)
  static const simAccounts  = '/simulation/accounts';
  static const simPositions = '/simulation/positions';
  static const simTrades    = '/simulation/trades';
}
