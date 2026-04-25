import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/stock_model.dart';
import '../../data/repositories/stock_repository.dart';
import '../widgets/common_widgets.dart';

// 비교할 종목 코드 목록 (최대 4개)
final compareTickersProvider =
    StateProvider<List<String>>((ref) => []);

class CompareScreen extends ConsumerWidget {
  const CompareScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tickers = ref.watch(compareTickersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('비교분석'),
        actions: [
          if (tickers.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear_all),
              onPressed: () =>
                  ref.read(compareTickersProvider.notifier).state = [],
            ),
        ],
      ),
      body: Column(children: [
        // 종목 추가 입력창
        _AddTickerBar(
          onAdd: (ticker) {
            if (tickers.length >= 4) {
              showErrorSnack(context, '최대 4종목까지 비교 가능합니다');
              return;
            }
            if (tickers.contains(ticker)) {
              showErrorSnack(context, '이미 추가된 종목입니다');
              return;
            }
            ref.read(compareTickersProvider.notifier).state = [
              ...tickers,
              ticker,
            ];
          },
        ),

        // 비교 결과
        Expanded(
          child: tickers.isEmpty
              ? const _EmptyCompare()
              : ListView(
                  padding: const EdgeInsets.all(12),
                  children: [
                    // 가격 비교 섹션
                    _SectionLabel('현재가 비교'),
                    const SizedBox(height: 8),
                    ...tickers.map((t) => _PriceCompareRow(ticker: t,
                        onRemove: () {
                          ref.read(compareTickersProvider.notifier).state =
                              tickers.where((x) => x != t).toList();
                        })),
                    const SizedBox(height: 16),

                    // 기술지표 비교 섹션
                    _SectionLabel('기술지표 비교'),
                    const SizedBox(height: 8),
                    ...tickers
                        .map((t) => _IndicatorCompareRow(ticker: t)),
                  ],
                ),
        ),
      ]),
    );
  }
}

// ── 종목 코드 입력 바 ─────────────────────────────────────────────
class _AddTickerBar extends StatefulWidget {
  const _AddTickerBar({required this.onAdd});
  final void Function(String) onAdd;

  @override
  State<_AddTickerBar> createState() => _AddTickerBarState();
}

class _AddTickerBarState extends State<_AddTickerBar> {
  final _ctrl = TextEditingController();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
    decoration: const BoxDecoration(
      border: Border(bottom: BorderSide(color: AppColors.border)),
    ),
    child: Row(children: [
      Expanded(
        child: TextField(
          controller: _ctrl,
          textCapitalization: TextCapitalization.characters,
          style: const TextStyle(color: AppColors.textPrimary),
          decoration: const InputDecoration(
            hintText: '종목 코드 입력 (예: 005930)',
            prefixIcon: Icon(Icons.search, color: AppColors.textHint, size: 20),
            contentPadding: EdgeInsets.symmetric(vertical: 10),
            isDense: true,
          ),
          onSubmitted: (v) => _submit(),
        ),
      ),
      const SizedBox(width: 8),
      ElevatedButton(
        onPressed: _submit,
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(60, 40),
          padding: EdgeInsets.zero,
        ),
        child: const Text('추가'),
      ),
    ]),
  );

  void _submit() {
    final v = _ctrl.text.trim();
    if (v.isNotEmpty) {
      widget.onAdd(v);
      _ctrl.clear();
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }
}

// ── 가격 비교 행 ──────────────────────────────────────────────────
class _PriceCompareRow extends ConsumerWidget {
  const _PriceCompareRow({required this.ticker, required this.onRemove});
  final String ticker;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final priceAsync = ref.watch(
      FutureProvider.autoDispose.family<StockPrice, String>(
        (ref, t) => ref.read(stockRepoProvider).getPrice(t),
      )(ticker),
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(children: [
        Expanded(child: Text(ticker,
            style: const TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w600))),
        priceAsync.when(
          loading: () => const SizedBox(
            width: 14, height: 14,
            child: CircularProgressIndicator(
                strokeWidth: 2, color: AppColors.textHint),
          ),
          error: (_, __) => const Text('-',
              style: TextStyle(color: AppColors.textHint)),
          data: (p) => Row(children: [
            Text(fmtWon(p.currentPrice), style: const TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.bold)),
            const SizedBox(width: 8),
            PriceChangeText(p.changeRate),
          ]),
        ),
        IconButton(
          icon: const Icon(Icons.close, size: 16, color: AppColors.textHint),
          onPressed: onRemove,
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
        ),
      ]),
    );
  }
}

// ── 기술지표 비교 행 ──────────────────────────────────────────────
class _IndicatorCompareRow extends ConsumerWidget {
  const _IndicatorCompareRow({required this.ticker});
  final String ticker;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final indAsync = ref.watch(
      FutureProvider.autoDispose.family<TechIndicators, String>(
        (ref, t) => ref.read(stockRepoProvider).getIndicators(t),
      )(ticker),
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: indAsync.when(
        loading: () => Row(children: [
          Text(ticker,
              style: const TextStyle(color: AppColors.textPrimary)),
          const SizedBox(width: 12),
          const SizedBox(width: 14, height: 14,
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: AppColors.textHint)),
        ]),
        error: (_, __) => Text('$ticker — 지표 조회 실패',
            style: const TextStyle(color: AppColors.textHint)),
        data: (ind) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(ticker, style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 8),
              Row(children: [
                _IndCell('RSI', ind.rsi != null
                    ? ind.rsi!.toStringAsFixed(1)
                    : '-', _rsiColor(ind.rsi)),
                _IndCell('MACD', _macdLabel(ind.macdHist),
                    _macdColor(ind.macdHist)),
                _IndCell('BB위치', _bbLabel(ind.bbPosition),
                    _bbColor(ind.bbPosition)),
                _IndCell('이동평균', ind.maAligned ? '정배열' : '미형성',
                    ind.maAligned
                        ? AppColors.neonGreen
                        : AppColors.textHint),
              ]),
            ]),
      ),
    );
  }

  Widget _IndCell(String label, String value, Color color) =>
      Expanded(child: Column(children: [
        Text(label,
            style: const TextStyle(
                color: AppColors.textHint, fontSize: 10)),
        const SizedBox(height: 3),
        Text(value, style: TextStyle(
            color: color,
            fontWeight: FontWeight.w600, fontSize: 12)),
      ]));

  Color _rsiColor(double? v) {
    if (v == null) return AppColors.textHint;
    if (v < 30) return AppColors.neonGreen;
    if (v > 70) return AppColors.neonRed;
    return AppColors.neonBlue;
  }

  String _macdLabel(double? v) {
    if (v == null) return '-';
    return v > 0 ? '상승 ▲' : '하락 ▼';
  }

  Color _macdColor(double? v) {
    if (v == null) return AppColors.textHint;
    return v > 0 ? AppColors.neonGreen : AppColors.neonRed;
  }

  String _bbLabel(double? v) {
    if (v == null) return '-';
    if (v < 0.2) return '하단';
    if (v > 0.8) return '상단';
    return '중간';
  }

  Color _bbColor(double? v) {
    if (v == null) return AppColors.textHint;
    if (v < 0.2) return AppColors.neonGreen;
    if (v > 0.8) return AppColors.neonRed;
    return AppColors.textSecondary;
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.label);
  final String label;

  @override
  Widget build(BuildContext context) => Text(label,
      style: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 14,
          fontWeight: FontWeight.bold));
}

class _EmptyCompare extends StatelessWidget {
  const _EmptyCompare();

  @override
  Widget build(BuildContext context) => const Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Icon(Icons.compare_arrows_outlined,
          color: AppColors.textHint, size: 52),
      SizedBox(height: 14),
      Text('종목 코드를 입력하여 비교하세요',
          style:
              TextStyle(color: AppColors.textSecondary, fontSize: 14)),
      SizedBox(height: 6),
      Text('최대 4개 종목까지 동시 비교 가능',
          style: TextStyle(color: AppColors.textHint, fontSize: 12)),
    ]),
  );
}
