import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/repositories/stock_repository.dart';
import '../../data/models/stock_model.dart';
import '../widgets/common_widgets.dart';

// 실제 포트폴리오 종목 (사용자가 직접 입력/관리)
class PortfolioEntry {
  final String ticker;
  final String name;
  final int quantity;
  final double avgPrice;

  const PortfolioEntry({
    required this.ticker,
    required this.name,
    required this.quantity,
    required this.avgPrice,
  });
}

final portfolioProvider =
    StateProvider<List<PortfolioEntry>>((ref) => []);

class PortfolioScreen extends ConsumerWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final entries = ref.watch(portfolioProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('자산평가'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            onPressed: () => _showAddDialog(context, ref),
          ),
        ],
      ),
      body: entries.isEmpty
          ? _EmptyPortfolio(onAdd: () => _showAddDialog(context, ref))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // 총 자산 요약
                _PortfolioSummary(entries: entries),
                const SizedBox(height: 16),
                const Text('보유 종목',
                    style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                // 종목별 평가
                ...entries.map((e) => _PortfolioEntryCard(
                      entry: e,
                      onDelete: () {
                        final list = [...ref.read(portfolioProvider)];
                        list.removeWhere((x) =>
                            x.ticker == e.ticker &&
                            x.avgPrice == e.avgPrice);
                        ref.read(portfolioProvider.notifier).state = list;
                      },
                    )),
                const SizedBox(height: 16),
                _LegalNote(),
              ],
            ),
    );
  }

  void _showAddDialog(BuildContext context, WidgetRef ref) {
    final tickerCtrl = TextEditingController();
    final nameCtrl = TextEditingController();
    final qtyCtrl = TextEditingController(text: '1');
    final priceCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('종목 추가',
            style: TextStyle(color: AppColors.textPrimary)),
        content: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextFormField(
              controller: tickerCtrl,
              textCapitalization: TextCapitalization.characters,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(labelText: '종목 코드'),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: nameCtrl,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(labelText: '종목명'),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: qtyCtrl,
              keyboardType: TextInputType.number,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(labelText: '보유수량 (주)'),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: priceCtrl,
              keyboardType: TextInputType.number,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(labelText: '평균매수단가 (원)'),
            ),
          ]),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소',
                style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            onPressed: () {
              final ticker = tickerCtrl.text.trim();
              final name = nameCtrl.text.trim();
              final qty = int.tryParse(qtyCtrl.text);
              final price = double.tryParse(
                  priceCtrl.text.replaceAll(',', ''));
              if (ticker.isEmpty ||
                  name.isEmpty ||
                  qty == null ||
                  price == null ||
                  qty <= 0 ||
                  price <= 0) return;
              ref.read(portfolioProvider.notifier).state = [
                ...ref.read(portfolioProvider),
                PortfolioEntry(
                    ticker: ticker,
                    name: name,
                    quantity: qty,
                    avgPrice: price),
              ];
              Navigator.pop(ctx);
            },
            child: const Text('추가'),
          ),
        ],
      ),
    );
  }
}

// ── 총 자산 요약 ──────────────────────────────────────────────────
class _PortfolioSummary extends ConsumerWidget {
  const _PortfolioSummary({required this.entries});
  final List<PortfolioEntry> entries;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    double totalCost = 0;
    for (final e in entries) {
      totalCost += e.avgPrice * e.quantity;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgCard, AppColors.bgSurface],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.neonBlue.withOpacity(0.3)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('투자원금 합계',
            style: TextStyle(
                color: AppColors.textSecondary, fontSize: 13)),
        const SizedBox(height: 6),
        Text(fmtWon(totalCost),
            style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 24,
                fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Text('총 ${entries.length}개 종목',
            style: const TextStyle(
                color: AppColors.textHint, fontSize: 12)),
      ]),
    );
  }
}

// ── 종목 카드 (실시간 평가) ───────────────────────────────────────
class _PortfolioEntryCard extends ConsumerWidget {
  const _PortfolioEntryCard(
      {required this.entry, required this.onDelete});
  final PortfolioEntry entry;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final priceAsync = ref.watch(
      FutureProvider.autoDispose.family<StockPrice, String>(
        (ref, t) => ref.read(stockRepoProvider).getPrice(t),
      )(entry.ticker),
    );

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start,
            children: [
          Row(children: [
            Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(entry.name, style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.bold)),
                  Text(entry.ticker, style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 12)),
                ])),
            IconButton(
              icon: const Icon(Icons.delete_outline,
                  size: 18, color: AppColors.textHint),
              onPressed: onDelete,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ]),
          const SizedBox(height: 8),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 8),
          priceAsync.when(
            loading: () => const SizedBox(
              height: 20,
              child: Center(child: SizedBox(width: 14, height: 14,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: AppColors.textHint))),
            ),
            error: (_, __) => const Text('시세 조회 실패',
                style: TextStyle(
                    color: AppColors.textHint, fontSize: 12)),
            data: (p) {
              final cost = entry.avgPrice * entry.quantity;
              final eval = p.currentPrice * entry.quantity;
              final pnl = eval - cost;
              final rate = (pnl / cost) * 100;
              final isProfit = pnl >= 0;
              final pnlColor =
                  isProfit ? AppColors.neonGreen : AppColors.neonRed;
              return Row(children: [
                Expanded(child: _Cell(
                    '보유수량', '${entry.quantity}주',
                    AppColors.textPrimary)),
                Expanded(child: _Cell(
                    '평균단가', fmtWon(entry.avgPrice),
                    AppColors.textSecondary)),
                Expanded(child: _Cell(
                    '현재가', fmtWon(p.currentPrice),
                    AppColors.textPrimary)),
                Expanded(child: _Cell(
                    '평가손익',
                    '${isProfit ? '+' : ''}${rate.toStringAsFixed(1)}%',
                    pnlColor)),
              ]);
            },
          ),
        ]),
      ),
    );
  }

  Widget _Cell(String label, String value, Color color) =>
      Column(children: [
        Text(label,
            style: const TextStyle(
                color: AppColors.textHint, fontSize: 10)),
        const SizedBox(height: 3),
        Text(value, style: TextStyle(
            color: color,
            fontWeight: FontWeight.w600,
            fontSize: 12)),
      ]);
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
      '자산 평가는 현재 시세 기준이며 실제 손익과 다를 수 있습니다. 투자 결정 및 책임은 투자자 본인에게 있습니다.',
      style: TextStyle(color: AppColors.textHint, fontSize: 11),
      textAlign: TextAlign.center,
    ),
  );
}

class _EmptyPortfolio extends StatelessWidget {
  const _EmptyPortfolio({required this.onAdd});
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.account_balance_wallet_outlined,
          color: AppColors.textHint, size: 56),
      const SizedBox(height: 14),
      const Text('보유 종목이 없습니다',
          style: TextStyle(
              color: AppColors.textSecondary, fontSize: 15)),
      const SizedBox(height: 6),
      const Text('실제 보유 주식을 입력하면\n실시간 평가손익을 확인할 수 있습니다',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.textHint, fontSize: 12)),
      const SizedBox(height: 20),
      ElevatedButton(
        onPressed: onAdd,
        style: ElevatedButton.styleFrom(
            minimumSize: const Size(180, 46)),
        child: const Text('종목 추가'),
      ),
    ]),
  );
}
