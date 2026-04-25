import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/stock_model.dart';
import '../../data/repositories/stock_repository.dart';
import '../widgets/common_widgets.dart';
import 'stock_detail_screen.dart';

// 검색어 상태
final searchQueryProvider = StateProvider<String>((ref) => '');

// 주요 종목 목록 (실제로는 백엔드에서 가져옴)
const _defaultTickers = [
  ('005930', '삼성전자'), ('000660', 'SK하이닉스'), ('035420', 'NAVER'),
  ('005380', '현대차'),   ('051910', 'LG화학'),     ('006400', '삼성SDI'),
  ('035720', '카카오'),   ('207940', '삼성바이오로직스'),
  ('068270', '셀트리온'), ('028260', '삼성물산'),
];

class StocksScreen extends ConsumerWidget {
  const StocksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final query = ref.watch(searchQueryProvider);
    final filtered = _defaultTickers.where((t) =>
        t.$1.contains(query) || t.$2.contains(query)).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('주식현재가'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: TextField(
              onChanged: (v) => ref.read(searchQueryProvider.notifier).state = v,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: InputDecoration(
                hintText: '종목명 또는 코드 검색',
                prefixIcon: const Icon(Icons.search, color: AppColors.textHint, size: 20),
                contentPadding: const EdgeInsets.symmetric(vertical: 10),
                isDense: true,
              ),
            ),
          ),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(12),
        itemCount: filtered.length,
        separatorBuilder: (_, __) => const SizedBox(height: 6),
        itemBuilder: (ctx, i) => _StockRow(
          ticker: filtered[i].$1,
          name: filtered[i].$2,
          onTap: () => Navigator.push(ctx, MaterialPageRoute(
            builder: (_) => StockDetailScreen(
                ticker: filtered[i].$1, name: filtered[i].$2))),
        ),
      ),
    );
  }
}

// ── 종목 행 (실시간 가격 표시) ────────────────────────────────────
class _StockRow extends ConsumerWidget {
  const _StockRow({required this.ticker, required this.name, required this.onTap});
  final String ticker, name;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final priceAsync = ref.watch(
      FutureProvider.autoDispose.family<StockPrice, String>(
        (ref, t) => ref.read(stockRepoProvider).getPrice(t)
      )(ticker),
    );

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.bgCard,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(children: [
          // 종목 정보
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(name, style: const TextStyle(
                color: AppColors.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
            Text(ticker, style: const TextStyle(color: AppColors.textHint, fontSize: 11)),
          ])),
          // 가격 정보
          priceAsync.when(
            loading: () => const SizedBox(width: 80,
                child: Align(alignment: Alignment.centerRight,
                    child: SizedBox(width: 16, height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2,
                            color: AppColors.textHint)))),
            error: (_, __) => const Text('-', style: TextStyle(color: AppColors.textHint)),
            data: (p) => Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Text(fmtWon(p.currentPrice),
                  style: const TextStyle(color: AppColors.textPrimary,
                      fontWeight: FontWeight.bold, fontSize: 15)),
              PriceChangeText(p.changeRate),
            ]),
          ),
          const SizedBox(width: 8),
          const Icon(Icons.chevron_right, color: AppColors.textHint, size: 18),
        ]),
      ),
    );
  }
}
