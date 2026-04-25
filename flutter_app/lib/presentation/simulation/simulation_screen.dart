import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/simulation_model.dart';
import '../../data/repositories/simulation_repository.dart';
import '../widgets/common_widgets.dart';

final simAccountProvider = FutureProvider<SimAccount?>((ref) =>
    ref.read(simRepoProvider).getAccount());

final simPositionsProvider = FutureProvider<List<SimPosition>>((ref) =>
    ref.read(simRepoProvider).getPositions());

class SimulationScreen extends ConsumerWidget {
  const SimulationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final accountAsync = ref.watch(simAccountProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('가상투자 시뮬레이션'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.refresh(simAccountProvider);
              ref.refresh(simPositionsProvider);
            },
          ),
        ],
      ),
      body: accountAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: AppColors.neonGreen)),
        error: (e, _) =>
            ErrorView('시뮬레이션 데이터를 불러올 수 없습니다'),
        data: (account) => account == null
            ? _NoAccount(onCreate: () => _showCreateDialog(context, ref))
            : RefreshIndicator(
                color: AppColors.neonGreen,
                onRefresh: () async {
                  ref.refresh(simAccountProvider);
                  ref.refresh(simPositionsProvider);
                },
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _AccountSummary(account),
                    const SizedBox(height: 16),
                    _SectionHeader(
                      '보유 종목',
                      action: ElevatedButton.icon(
                        onPressed: () => _showBuyDialog(context, ref),
                        icon: const Icon(Icons.add, size: 16),
                        label: const Text('매수'),
                        style: ElevatedButton.styleFrom(
                          minimumSize: Size.zero,
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 8),
                          textStyle: const TextStyle(fontSize: 13),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Consumer(builder: (ctx, ref, _) {
                      final posAsync = ref.watch(simPositionsProvider);
                      return posAsync.when(
                        loading: () => Column(
                            children: List.generate(
                                2, (_) => const SkeletonCard(height: 110))),
                        error: (_, __) => const Text('포지션 조회 실패',
                            style: TextStyle(color: AppColors.textHint)),
                        data: (positions) => positions.isEmpty
                            ? const _EmptyPositions()
                            : Column(
                                children: positions
                                    .map((p) => _PositionCard(
                                          position: p,
                                          onSell: () =>
                                              _showSellDialog(ctx, ref, p),
                                        ))
                                    .toList()),
                      );
                    }),
                  ],
                ),
              ),
      ),
    );
  }

  // ── 가상계좌 개설 다이얼로그 ─────────────────────────────────────
  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    final ctrl = TextEditingController(text: '10000000');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('가상계좌 개설',
            style: TextStyle(color: AppColors.textPrimary)),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('초기 가상 자금을 설정하세요',
              style:
                  TextStyle(color: AppColors.textSecondary, fontSize: 13)),
          const SizedBox(height: 12),
          TextFormField(
            controller: ctrl,
            keyboardType: TextInputType.number,
            style: const TextStyle(color: AppColors.textPrimary),
            decoration: const InputDecoration(labelText: '초기 자금 (원)'),
          ),
        ]),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소',
                style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            onPressed: () async {
              final amount =
                  double.tryParse(ctrl.text.replaceAll(',', ''));
              if (amount == null || amount <= 0) return;
              try {
                await ref
                    .read(simRepoProvider)
                    .createAccount(initialBalance: amount);
                ref.refresh(simAccountProvider);
                if (ctx.mounted) Navigator.pop(ctx);
              } catch (e) {
                if (ctx.mounted) showErrorSnack(ctx, '계좌 개설 실패');
              }
            },
            child: const Text('개설'),
          ),
        ],
      ),
    );
  }

  // ── 매수 다이얼로그 ──────────────────────────────────────────────
  void _showBuyDialog(BuildContext context, WidgetRef ref) {
    final tickerCtrl = TextEditingController();
    final qtyCtrl = TextEditingController(text: '1');
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('가상 매수',
            style: TextStyle(color: AppColors.textPrimary)),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextFormField(
            controller: tickerCtrl,
            textCapitalization: TextCapitalization.characters,
            style: const TextStyle(color: AppColors.textPrimary),
            decoration:
                const InputDecoration(labelText: '종목 코드 (예: 005930)'),
          ),
          const SizedBox(height: 10),
          TextFormField(
            controller: qtyCtrl,
            keyboardType: TextInputType.number,
            style: const TextStyle(color: AppColors.textPrimary),
            decoration: const InputDecoration(labelText: '수량 (주)'),
          ),
        ]),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소',
                style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            onPressed: () async {
              final qty = int.tryParse(qtyCtrl.text);
              if (tickerCtrl.text.isEmpty || qty == null || qty <= 0) return;
              try {
                await ref.read(simRepoProvider).trade(
                    ticker: tickerCtrl.text.trim(),
                    tradeType: 'buy',
                    quantity: qty);
                ref.refresh(simAccountProvider);
                ref.refresh(simPositionsProvider);
                if (ctx.mounted) {
                  Navigator.pop(ctx);
                  showSuccessSnack(ctx, '매수 완료!');
                }
              } catch (e) {
                if (ctx.mounted) showErrorSnack(ctx, '매수 실패: 잔고 부족 또는 오류');
              }
            },
            child: const Text('매수'),
          ),
        ],
      ),
    );
  }

  // ── 매도 다이얼로그 ──────────────────────────────────────────────
  void _showSellDialog(
      BuildContext context, WidgetRef ref, SimPosition pos) {
    final qtyCtrl = TextEditingController(text: pos.quantity.toString());
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: Text('${pos.name} 매도',
            style: const TextStyle(color: AppColors.textPrimary)),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('보유수량',
                style:
                    TextStyle(color: AppColors.textHint, fontSize: 13)),
            Text('${pos.quantity}주',
                style: const TextStyle(color: AppColors.textPrimary)),
          ]),
          const SizedBox(height: 10),
          TextFormField(
            controller: qtyCtrl,
            keyboardType: TextInputType.number,
            style: const TextStyle(color: AppColors.textPrimary),
            decoration: const InputDecoration(labelText: '매도 수량 (주)'),
          ),
        ]),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소',
                style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            onPressed: () async {
              final qty = int.tryParse(qtyCtrl.text);
              if (qty == null || qty <= 0 || qty > pos.quantity) return;
              try {
                await ref.read(simRepoProvider).trade(
                    ticker: pos.ticker,
                    tradeType: 'sell',
                    quantity: qty);
                ref.refresh(simAccountProvider);
                ref.refresh(simPositionsProvider);
                if (ctx.mounted) {
                  Navigator.pop(ctx);
                  showSuccessSnack(ctx, '매도 완료!');
                }
              } catch (e) {
                if (ctx.mounted) showErrorSnack(ctx, '매도 실패');
              }
            },
            style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.neonRed,
                foregroundColor: Colors.white),
            child: const Text('매도'),
          ),
        ],
      ),
    );
  }
}

// ── 계좌 요약 카드 ────────────────────────────────────────────────
class _AccountSummary extends StatelessWidget {
  const _AccountSummary(this.account);
  final SimAccount account;

  @override
  Widget build(BuildContext context) {
    final isProfit = account.totalProfitLoss >= 0;
    final pnlColor =
        isProfit ? AppColors.neonGreen : AppColors.neonRed;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgCard, AppColors.bgSurface],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isProfit
              ? AppColors.neonGreen.withOpacity(0.3)
              : AppColors.neonRed.withOpacity(0.3),
        ),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(account.name,
              style: const TextStyle(
                  color: AppColors.textSecondary, fontSize: 13)),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: AppColors.neonBlue.withOpacity(0.15),
              borderRadius: BorderRadius.circular(5),
            ),
            child: const Text('가상계좌',
                style:
                    TextStyle(color: AppColors.neonBlue, fontSize: 11)),
          ),
        ]),
        const SizedBox(height: 8),
        Text('예수금 ${fmtWon(account.virtualBalance)}',
            style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 22,
                fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Divider(color: AppColors.border, height: 1),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(child: _StatCell('투자원금',
              fmtWon(account.initialBalance), AppColors.textSecondary)),
          Expanded(child: _StatCell(
            '평가손익',
            '${isProfit ? '+' : ''}${fmtWon(account.totalProfitLoss)}',
            pnlColor,
          )),
          Expanded(child: _StatCell(
            '수익률',
            '${isProfit ? '+' : ''}${account.profitRate.toStringAsFixed(2)}%',
            pnlColor,
          )),
        ]),
      ]),
    );
  }

  Widget _StatCell(String label, String value, Color color) =>
      Column(children: [
        Text(label,
            style: const TextStyle(
                color: AppColors.textHint, fontSize: 11)),
        const SizedBox(height: 4),
        Text(value,
            style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 13)),
      ]);
}

// ── 포지션 카드 ───────────────────────────────────────────────────
class _PositionCard extends StatelessWidget {
  const _PositionCard({required this.position, required this.onSell});
  final SimPosition position;
  final VoidCallback onSell;

  @override
  Widget build(BuildContext context) {
    final isProfit = position.unrealizedPnl >= 0;
    final pnlColor = isProfit ? AppColors.neonGreen : AppColors.neonRed;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(position.name, style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.bold)),
                  Text(position.ticker, style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 12)),
                ])),
            if (position.aiSignalGrade != null) ...[
              GradeBadge(position.aiSignalGrade!),
              const SizedBox(width: 8),
            ],
            OutlinedButton(
              onPressed: onSell,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.neonRed,
                side: const BorderSide(color: AppColors.neonRed),
                minimumSize: Size.zero,
                padding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 6),
                textStyle: const TextStyle(fontSize: 12),
              ),
              child: const Text('매도'),
            ),
          ]),
          const SizedBox(height: 10),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: _Cell(
                '보유수량', '${position.quantity}주', AppColors.textPrimary)),
            Expanded(child: _Cell(
                '평균단가', fmtWon(position.avgBuyPrice), AppColors.textSecondary)),
            Expanded(child: _Cell(
                '현재가',
                position.currentPrice != null
                    ? fmtWon(position.currentPrice!)
                    : '-',
                AppColors.textPrimary)),
            Expanded(child: _Cell(
                '수익률',
                '${isProfit ? '+' : ''}${position.unrealizedPnlRate.toStringAsFixed(1)}%',
                pnlColor)),
          ]),
          if (position.stopLossPrice != null ||
              position.takeProfitPrice != null) ...[
            const SizedBox(height: 8),
            Row(children: [
              if (position.takeProfitPrice != null) ...[
                const Icon(Icons.flag_outlined,
                    size: 12, color: AppColors.neonGreen),
                const SizedBox(width: 3),
                Text('익절 ${fmtWon(position.takeProfitPrice!)}',
                    style: const TextStyle(
                        color: AppColors.neonGreen, fontSize: 11)),
                const SizedBox(width: 12),
              ],
              if (position.stopLossPrice != null) ...[
                const Icon(Icons.shield_outlined,
                    size: 12, color: AppColors.neonRed),
                const SizedBox(width: 3),
                Text('손절 ${fmtWon(position.stopLossPrice!)}',
                    style: const TextStyle(
                        color: AppColors.neonRed, fontSize: 11)),
              ],
            ]),
          ],
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
        Text(value,
            style: TextStyle(
                color: color,
                fontWeight: FontWeight.w600,
                fontSize: 12)),
      ]);
}

// ── 섹션 헤더 ─────────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title, {required this.action});
  final String title;
  final Widget action;

  @override
  Widget build(BuildContext context) =>
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(title, style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 15,
            fontWeight: FontWeight.bold)),
        action,
      ]);
}

class _EmptyPositions extends StatelessWidget {
  const _EmptyPositions();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(28),
    alignment: Alignment.center,
    child: const Text('보유 종목이 없습니다.\n위의 매수 버튼을 눌러 시작하세요.',
        textAlign: TextAlign.center,
        style: TextStyle(color: AppColors.textHint, fontSize: 13)),
  );
}

class _NoAccount extends StatelessWidget {
  const _NoAccount({required this.onCreate});
  final VoidCallback onCreate;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.science_outlined,
          color: AppColors.textHint, size: 64),
      const SizedBox(height: 16),
      const Text('가상계좌가 없습니다',
          style: TextStyle(
              color: AppColors.textSecondary, fontSize: 16)),
      const SizedBox(height: 8),
      const Text('가상 자금으로 실제 종목에 투자해보세요',
          style:
              TextStyle(color: AppColors.textHint, fontSize: 13)),
      const SizedBox(height: 24),
      ElevatedButton(
        onPressed: onCreate,
        style: ElevatedButton.styleFrom(
            minimumSize: const Size(200, 48)),
        child: const Text('가상계좌 개설'),
      ),
    ]),
  );
}
