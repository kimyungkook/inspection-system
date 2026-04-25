import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/stock_model.dart';
import 'common_widgets.dart';

class IndicatorCard extends StatelessWidget {
  const IndicatorCard(this.ind, {super.key});
  final TechIndicators ind;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('기술적 지표',
            style: TextStyle(color: AppColors.textPrimary,
                fontWeight: FontWeight.bold, fontSize: 15)),
        const SizedBox(height: 14),

        // RSI 게이지
        if (ind.rsi != null) ...[
          _RsiGauge(ind.rsi!),
          const SizedBox(height: 14),
        ],

        // MACD + 볼린저밴드 + 거래량
        Row(children: [
          Expanded(child: _IndItem('MACD', _macdLabel(ind.macdHist), _macdColor(ind.macdHist))),
          Expanded(child: _IndItem('BB위치', _bbLabel(ind.bbPosition), _bbColor(ind.bbPosition))),
          Expanded(child: _IndItem('거래량', '${(ind.volumeRatio ?? 0).toStringAsFixed(0)}%',
              (ind.volumeRatio ?? 0) >= 200 ? AppColors.neonGreen : AppColors.textSecondary)),
        ]),
        const SizedBox(height: 12),

        // 이동평균 정배열
        _MaStatus(ind.maAligned),
      ]),
    ),
  );

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
    if (v < 0.2) return '하단 근접';
    if (v > 0.8) return '상단 근접';
    return '중간';
  }
  Color _bbColor(double? v) {
    if (v == null) return AppColors.textHint;
    if (v < 0.2) return AppColors.neonGreen;
    if (v > 0.8) return AppColors.neonRed;
    return AppColors.textSecondary;
  }
}

// RSI 게이지 바
class _RsiGauge extends StatelessWidget {
  const _RsiGauge(this.rsi);
  final double rsi;

  @override
  Widget build(BuildContext context) {
    final color = rsi < 30 ? AppColors.neonGreen
        : rsi > 70 ? AppColors.neonRed : AppColors.neonBlue;
    final label = rsi < 30 ? '과매도 — 매수 기회'
        : rsi > 70 ? '과매수 — 주의 구간' : '적정 구간';

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Row(children: [
          const Text('RSI ', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
          Text(rsi.toStringAsFixed(1),
              style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 15)),
        ]),
        Text(label, style: TextStyle(color: color, fontSize: 11)),
      ]),
      const SizedBox(height: 6),
      Stack(children: [
        Container(height: 6,
            decoration: BoxDecoration(color: AppColors.bgSurface,
                borderRadius: BorderRadius.circular(3))),
        FractionallySizedBox(
          widthFactor: rsi / 100,
          child: Container(height: 6,
              decoration: BoxDecoration(color: color,
                  borderRadius: BorderRadius.circular(3))),
        ),
        // 과매도/과매수 기준선
        Positioned(left: (30 / 100) * MediaQuery.of(context).size.width * 0.7,
          child: Container(width: 1.5, height: 6, color: AppColors.textHint)),
        Positioned(left: (70 / 100) * MediaQuery.of(context).size.width * 0.7,
          child: Container(width: 1.5, height: 6, color: AppColors.textHint)),
      ]),
      const SizedBox(height: 4),
      const Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text('0', style: TextStyle(color: AppColors.textHint, fontSize: 10)),
        Text('30 (과매도)', style: TextStyle(color: AppColors.textHint, fontSize: 10)),
        Text('70 (과매수)', style: TextStyle(color: AppColors.textHint, fontSize: 10)),
        Text('100', style: TextStyle(color: AppColors.textHint, fontSize: 10)),
      ]),
    ]);
  }
}

// 이동평균 정배열 상태
class _MaStatus extends StatelessWidget {
  const _MaStatus(this.aligned);
  final bool aligned;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
    decoration: BoxDecoration(
      color: aligned
          ? AppColors.neonGreen.withOpacity(0.1)
          : AppColors.bgSurface,
      borderRadius: BorderRadius.circular(8),
      border: Border.all(
          color: aligned ? AppColors.neonGreen.withOpacity(0.4) : AppColors.border),
    ),
    child: Row(children: [
      Icon(aligned ? Icons.trending_up : Icons.remove,
          color: aligned ? AppColors.neonGreen : AppColors.textHint, size: 16),
      const SizedBox(width: 8),
      Text(
        aligned ? '이동평균 정배열 (5 > 20 > 60) — 상승추세' : '이동평균 정배열 미형성',
        style: TextStyle(
            color: aligned ? AppColors.neonGreen : AppColors.textSecondary,
            fontSize: 12),
      ),
    ]),
  );
}

class _IndItem extends StatelessWidget {
  const _IndItem(this.label, this.value, this.color);
  final String label, value; final Color color;

  @override
  Widget build(BuildContext context) => Column(children: [
    Text(label, style: const TextStyle(color: AppColors.textHint, fontSize: 11)),
    const SizedBox(height: 4),
    Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 13)),
  ]);
}
