import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/stock_model.dart';
import '../../data/repositories/stock_repository.dart';
import '../widgets/common_widgets.dart';
import '../widgets/indicator_widgets.dart';

class StockDetailScreen extends ConsumerWidget {
  const StockDetailScreen({super.key, required this.ticker, required this.name});
  final String ticker, name;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final priceAsync = ref.watch(
      FutureProvider.autoDispose<StockPrice>(
          (ref) => ref.read(stockRepoProvider).getPrice(ticker)));
    final indAsync = ref.watch(
      FutureProvider.autoDispose<TechIndicators>(
          (ref) => ref.read(stockRepoProvider).getIndicators(ticker)));

    return Scaffold(
      appBar: AppBar(
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(name, style: const TextStyle(fontSize: 16)),
          Text(ticker, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
        ]),
        actions: [
          IconButton(
            icon: const Icon(Icons.star_outline),
            onPressed: () => _addWatchlist(context, ref),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 현재가 카드
          priceAsync.when(
            loading: () => const SkeletonCard(height: 80),
            error: (e, _) => ErrorView('시세 조회 실패'),
            data: (p) => _PriceCard(p),
          ),
          const SizedBox(height: 16),

          // 기술적 지표 카드
          indAsync.when(
            loading: () => const SkeletonCard(height: 200),
            error: (e, _) => ErrorView('지표 조회 실패'),
            data: (ind) => IndicatorCard(ind),
          ),
          const SizedBox(height: 16),

          // 법적 고지
          _LegalNote(),
        ],
      ),
    );
  }

  Future<void> _addWatchlist(BuildContext context, WidgetRef ref) async {
    try {
      await ref.read(stockRepoProvider).addWatchlist(ticker);
      if (context.mounted) showSuccessSnack(context, '관심종목에 추가되었습니다.');
    } catch (e) {
      if (context.mounted) showErrorSnack(context, '추가 실패');
    }
  }
}

class _PriceCard extends StatelessWidget {
  const _PriceCard(this.price);
  final StockPrice price;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(children: [
        Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(fmtWon(price.currentPrice),
                style: const TextStyle(color: AppColors.textPrimary,
                    fontSize: 28, fontWeight: FontWeight.bold)),
            PriceChangeText(price.changeRate, fontSize: 15),
          ])),
          Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
            _PriceRow('고가', price.highPrice, AppColors.neonGreen),
            const SizedBox(height: 4),
            _PriceRow('저가', price.lowPrice, AppColors.neonRed),
          ]),
        ]),
        const SizedBox(height: 12),
        appDivider,
        const SizedBox(height: 10),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          _InfoChip('시가', fmtWon(price.openPrice)),
          _InfoChip('거래량', _fmtVol(price.volume)),
        ]),
      ]),
    ),
  );

  Widget _PriceRow(String label, double val, Color color) => Row(children: [
    Text('$label ', style: const TextStyle(color: AppColors.textHint, fontSize: 11)),
    Text(fmtWon(val), style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
  ]);

  Widget _InfoChip(String label, String val) => Column(children: [
    Text(label, style: const TextStyle(color: AppColors.textHint, fontSize: 11)),
    Text(val, style: const TextStyle(color: AppColors.textPrimary, fontSize: 13)),
  ]);

  String _fmtVol(int v) => v >= 10000
      ? '${(v / 10000).toStringAsFixed(0)}만'
      : v.toString();
}

class _LegalNote extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: AppColors.bgSurface,
      borderRadius: BorderRadius.circular(8),
    ),
    child: const Text(
      '본 서비스의 AI 분석 결과는 투자 참고용 정보이며, 투자 결정 및 그에 따른 손익의 책임은 투자자 본인에게 있습니다.',
      style: TextStyle(color: AppColors.textHint, fontSize: 11),
      textAlign: TextAlign.center,
    ),
  );
}
