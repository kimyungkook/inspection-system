import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/stock_model.dart';
import '../../data/repositories/stock_repository.dart';
import '../widgets/common_widgets.dart';
import '../stocks/stock_detail_screen.dart';

final watchlistProvider = FutureProvider<List<WatchlistItem>>((ref) =>
    ref.read(stockRepoProvider).getWatchlist());

class WatchlistScreen extends ConsumerWidget {
  const WatchlistScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final watchAsync = ref.watch(watchlistProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('관심종목'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(watchlistProvider),
          ),
        ],
      ),
      body: watchAsync.when(
        loading: () => Padding(
          padding: const EdgeInsets.all(12),
          child: Column(children: List.generate(4, (_) => const SkeletonCard(height: 76))),
        ),
        error: (e, _) => ErrorView('관심종목을 불러올 수 없습니다',
            onRetry: () => ref.refresh(watchlistProvider)),
        data: (list) => list.isEmpty
            ? const _EmptyWatchlist()
            : ListView.separated(
                padding: const EdgeInsets.all(12),
                itemCount: list.length,
                separatorBuilder: (_, __) => const SizedBox(height: 6),
                itemBuilder: (ctx, i) => _WatchlistRow(
                  item: list[i],
                  onDelete: () async {
                    await ref.read(stockRepoProvider).removeWatchlist(list[i].watchlistId);
                    ref.refresh(watchlistProvider);
                  },
                  onTap: () => Navigator.push(ctx, MaterialPageRoute(
                    builder: (_) => StockDetailScreen(
                        ticker: list[i].ticker, name: list[i].name))),
                ),
              ),
      ),
    );
  }
}

// ── 관심종목 행 (실시간 시세 포함) ───────────────────────────────
class _WatchlistRow extends ConsumerWidget {
  const _WatchlistRow({
    required this.item,
    required this.onDelete,
    required this.onTap,
  });
  final WatchlistItem item;
  final VoidCallback onDelete, onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final priceAsync = ref.watch(
      FutureProvider.autoDispose.family<StockPrice, String>(
        (ref, t) => ref.read(stockRepoProvider).getPrice(t),
      )(item.ticker),
    );

    return Dismissible(
      key: Key(item.watchlistId.toString()),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        decoration: BoxDecoration(
          color: AppColors.neonRed.withOpacity(0.2),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Icon(Icons.delete_outline, color: AppColors.neonRed),
      ),
      onDismissed: (_) => onDelete(),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.bgCard,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Text(item.name, style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600, fontSize: 14)),
                if (item.alertOnSignal) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.neonBlue.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text('알림',
                        style: TextStyle(color: AppColors.neonBlue, fontSize: 9)),
                  ),
                ],
              ]),
              Text(item.ticker,
                  style: const TextStyle(color: AppColors.textHint, fontSize: 11)),
              if (item.targetPrice != null)
                Text('목표가 ${fmtWon(item.targetPrice!)}',
                    style: const TextStyle(color: AppColors.neonGreen, fontSize: 10)),
            ])),
            priceAsync.when(
              loading: () => const SizedBox(
                width: 80,
                child: Align(
                  alignment: Alignment.centerRight,
                  child: SizedBox(
                    width: 14, height: 14,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppColors.textHint),
                  ),
                ),
              ),
              error: (_, __) => const Text('-',
                  style: TextStyle(color: AppColors.textHint)),
              data: (p) => Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text(fmtWon(p.currentPrice), style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold, fontSize: 15)),
                PriceChangeText(p.changeRate),
              ]),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right, color: AppColors.textHint, size: 18),
          ]),
        ),
      ),
    );
  }
}

class _EmptyWatchlist extends StatelessWidget {
  const _EmptyWatchlist();

  @override
  Widget build(BuildContext context) => const Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.star_outline, color: AppColors.textHint, size: 52),
      SizedBox(height: 14),
      Text('관심종목이 없습니다',
          style: TextStyle(color: AppColors.textSecondary, fontSize: 15)),
      SizedBox(height: 6),
      Text('주식 화면에서 ★을 눌러 추가하세요',
          style: TextStyle(color: AppColors.textHint, fontSize: 12)),
    ]),
  );
}
