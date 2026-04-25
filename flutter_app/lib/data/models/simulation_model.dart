class SimAccount {
  final int id;
  final String name;
  final double virtualBalance;
  final double initialBalance;
  final double totalInvested;
  final double totalProfitLoss;
  final double profitRate;

  const SimAccount({
    required this.id,
    required this.name,
    required this.virtualBalance,
    required this.initialBalance,
    required this.totalInvested,
    required this.totalProfitLoss,
    required this.profitRate,
  });

  factory SimAccount.fromJson(Map<String, dynamic> j) => SimAccount(
    id:               j['id'],
    name:             j['name'] ?? '내 가상계좌',
    virtualBalance:   _d(j['virtual_balance']),
    initialBalance:   _d(j['initial_balance']),
    totalInvested:    _d(j['total_invested']),
    totalProfitLoss:  _d(j['total_profit_loss']),
    profitRate:       _d(j['profit_rate']),
  );

  static double _d(dynamic v) => (v as num?)?.toDouble() ?? 0.0;
}

class SimPosition {
  final int id;
  final int accountId;
  final String ticker;
  final String name;
  final int quantity;
  final double avgBuyPrice;
  final double? currentPrice;
  final double unrealizedPnl;
  final double unrealizedPnlRate;
  final String? aiSignalGrade;
  final int? aiBuyProbability;
  final double? stopLossPrice;
  final double? takeProfitPrice;

  const SimPosition({
    required this.id,
    required this.accountId,
    required this.ticker,
    required this.name,
    required this.quantity,
    required this.avgBuyPrice,
    this.currentPrice,
    required this.unrealizedPnl,
    required this.unrealizedPnlRate,
    this.aiSignalGrade,
    this.aiBuyProbability,
    this.stopLossPrice,
    this.takeProfitPrice,
  });

  factory SimPosition.fromJson(Map<String, dynamic> j) => SimPosition(
    id:                j['id'],
    accountId:         j['account_id'],
    ticker:            j['ticker'] ?? '',
    name:              j['name'] ?? '',
    quantity:          (j['quantity'] as num?)?.toInt() ?? 0,
    avgBuyPrice:       _d(j['avg_buy_price']),
    currentPrice:      _d2(j['current_price']),
    unrealizedPnl:     _d(j['unrealized_pnl']),
    unrealizedPnlRate: _d(j['unrealized_pnl_rate']),
    aiSignalGrade:     j['ai_signal_grade'],
    aiBuyProbability:  (j['ai_buy_probability'] as num?)?.toInt(),
    stopLossPrice:     _d2(j['stop_loss_price']),
    takeProfitPrice:   _d2(j['take_profit_price']),
  );

  static double  _d(dynamic v) => (v as num?)?.toDouble() ?? 0.0;
  static double? _d2(dynamic v) => v == null ? null : (v as num).toDouble();
}
