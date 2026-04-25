class StockPrice {
  final String ticker;
  final double currentPrice;
  final double changeRate;
  final int volume;
  final double openPrice;
  final double highPrice;
  final double lowPrice;

  const StockPrice({
    required this.ticker,
    required this.currentPrice,
    required this.changeRate,
    required this.volume,
    required this.openPrice,
    required this.highPrice,
    required this.lowPrice,
  });

  factory StockPrice.fromJson(Map<String, dynamic> j) => StockPrice(
    ticker:       j['ticker'] ?? '',
    currentPrice: _d(j['current_price']),
    changeRate:   _d(j['change_rate']),
    volume:       (j['volume'] as num?)?.toInt() ?? 0,
    openPrice:    _d(j['open_price']),
    highPrice:    _d(j['high_price']),
    lowPrice:     _d(j['low_price']),
  );

  static double _d(dynamic v) => (v as num?)?.toDouble() ?? 0.0;
}

class TechIndicators {
  final String ticker;
  final double? rsi;
  final double? macdHist;
  final double? bbPosition;
  final double? ma5;
  final double? ma20;
  final double? volumeRatio;
  final bool maAligned;

  const TechIndicators({
    required this.ticker,
    this.rsi,
    this.macdHist,
    this.bbPosition,
    this.ma5,
    this.ma20,
    this.volumeRatio,
    this.maAligned = false,
  });

  factory TechIndicators.fromJson(Map<String, dynamic> j) => TechIndicators(
    ticker:      j['ticker'] ?? '',
    rsi:         _d(j['rsi']),
    macdHist:    _d(j['macd_hist']),
    bbPosition:  _d(j['bb_position']),
    ma5:         _d(j['ma5']),
    ma20:        _d(j['ma20']),
    volumeRatio: _d(j['volume_ratio']),
    maAligned:   j['ma_aligned'] ?? false,
  );

  static double? _d(dynamic v) => v == null ? null : (v as num).toDouble();
}

class AiRecommendation {
  final int rank;
  final String ticker;
  final String name;
  final double? currentPrice;
  final String recommendation;
  final int buyProbability;
  final double? targetPrice;
  final double? stopLossPrice;
  final String? oneLineSummary;
  final String? buyReason;
  final String? riskReason;

  const AiRecommendation({
    required this.rank,
    required this.ticker,
    required this.name,
    this.currentPrice,
    required this.recommendation,
    required this.buyProbability,
    this.targetPrice,
    this.stopLossPrice,
    this.oneLineSummary,
    this.buyReason,
    this.riskReason,
  });

  factory AiRecommendation.fromJson(Map<String, dynamic> j) => AiRecommendation(
    rank:           j['rank'] ?? 0,
    ticker:         j['ticker'] ?? '',
    name:           j['name'] ?? '',
    currentPrice:   _d(j['current_price']),
    recommendation: j['recommendation'] ?? 'hold',
    buyProbability: (j['buy_probability'] as num?)?.toInt() ?? 0,
    targetPrice:    _d(j['target_price']),
    stopLossPrice:  _d(j['stop_loss_price']),
    oneLineSummary: j['one_line_summary'],
    buyReason:      j['buy_reason'],
    riskReason:     j['risk_reason'],
  );

  static double? _d(dynamic v) => v == null ? null : (v as num).toDouble();
}

class WatchlistItem {
  final int watchlistId;
  final String ticker;
  final String name;
  final double? targetPrice;
  final bool alertOnSignal;

  const WatchlistItem({
    required this.watchlistId,
    required this.ticker,
    required this.name,
    this.targetPrice,
    required this.alertOnSignal,
  });

  factory WatchlistItem.fromJson(Map<String, dynamic> j) => WatchlistItem(
    watchlistId:  j['watchlist_id'],
    ticker:       j['ticker'],
    name:         j['name'],
    targetPrice:  (j['target_price'] as num?)?.toDouble(),
    alertOnSignal: j['alert_on_signal'] ?? true,
  );
}
