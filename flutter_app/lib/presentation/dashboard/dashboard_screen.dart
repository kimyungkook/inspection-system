import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/stock_model.dart';
import '../../data/repositories/stock_repository.dart';
import '../widgets/common_widgets.dart';

// AI 추천 5종목 Provider
final top5Provider = FutureProvider<List<AiRecommendation>>((ref) =>
    ref.read(stockRepoProvider).getTop5());

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final top5 = ref.watch(top5Provider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 대시보드'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {},
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.neonGreen,
        onRefresh: () => ref.refresh(top5Provider.future),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // 시장 현황 헤더
            _MarketHeader(),
            const SizedBox(height: 20),

            // 섹션 타이틀
            _SectionTitle(
              'AI 추천 TOP 5',
              subtitle: '오늘의 분석 결과',
              action: TextButton(
                onPressed: () => context.go('/stocks'),
                child: const Text('전체보기', style: TextStyle(color: AppColors.neonBlue, fontSize: 12)),
              ),
            ),
            const SizedBox(height: 12),

            // 추천 종목 목록
            top5.when(
              loading: () => Column(children: List.generate(5, (_) => const SkeletonCard(height: 90))),
              error: (e, _) => ErrorView('데이터를 불러올 수 없습니다', onRetry: () => ref.refresh(top5Provider.future)),
              data: (list) => list.isEmpty
                  ? const _EmptyRecommendation()
                  : Column(children: list.map((r) => _RecommendCard(r)).toList()),
            ),
            const SizedBox(height: 20),

            // 빠른 메뉴 그리드
            _SectionTitle('빠른 메뉴', subtitle: ''),
            const SizedBox(height: 12),
            _QuickMenuGrid(),
          ],
        ),
      ),
    );
  }
}

// ── 시장 현황 배너 ────────────────────────────────────────────────
class _MarketHeader extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      gradient: LinearGradient(
        colors: [AppColors.bgCard, AppColors.bgSurface],
        begin: Alignment.topLeft, end: Alignment.bottomRight,
      ),
      borderRadius: BorderRadius.circular(14),
      border: Border.all(color: AppColors.border),
    ),
    child: Row(children: [
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('시장 분위기', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        const SizedBox(height: 4),
        Row(children: [
          Container(width: 8, height: 8, decoration: const BoxDecoration(
            color: AppColors.neonGreen, shape: BoxShape.circle)),
          const SizedBox(width: 6),
          const Text('분석 중...', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
        ]),
      ])),
      Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
        const Text('오늘의 AI 신호', style: TextStyle(color: AppColors.textSecondary, fontSize: 11)),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.neonGreen.withOpacity(0.15),
            borderRadius: BorderRadius.circular(20),
          ),
          child: const Text('분석 완료', style: TextStyle(color: AppColors.neonGreen, fontSize: 12)),
        ),
      ]),
    ]),
  );
}

// ── AI 추천 카드 ──────────────────────────────────────────────────
class _RecommendCard extends StatelessWidget {
  const _RecommendCard(this.item);
  final AiRecommendation item;

  @override
  Widget build(BuildContext context) {
    final probColor = item.buyProbability >= 70
        ? AppColors.neonGreen
        : item.buyProbability >= 50 ? AppColors.neonBlue : AppColors.textSecondary;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            // 순위
            Container(
              width: 26, height: 26,
              decoration: BoxDecoration(
                color: AppColors.neonGreen.withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Text('${item.rank}',
                  style: const TextStyle(color: AppColors.neonGreen, fontSize: 12, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(width: 10),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(item.name, style: const TextStyle(
                  color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
              Text(item.ticker, style: const TextStyle(
                  color: AppColors.textSecondary, fontSize: 12)),
            ])),
            // 매수 확률
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Text('매수확률', style: const TextStyle(color: AppColors.textHint, fontSize: 10)),
              Text('${item.buyProbability}%',
                  style: TextStyle(color: probColor, fontSize: 18, fontWeight: FontWeight.bold)),
            ]),
          ]),
          if (item.oneLineSummary != null) ...[
            const SizedBox(height: 8),
            appDivider,
            const SizedBox(height: 8),
            Text(item.oneLineSummary!,
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
          ],
          if (item.targetPrice != null) ...[
            const SizedBox(height: 6),
            Row(children: [
              const Icon(Icons.flag_outlined, size: 13, color: AppColors.textHint),
              const SizedBox(width: 4),
              Text('목표가 ${fmtWon(item.targetPrice!)}',
                  style: const TextStyle(color: AppColors.neonGreen, fontSize: 12)),
              if (item.stopLossPrice != null) ...[
                const SizedBox(width: 12),
                const Icon(Icons.shield_outlined, size: 13, color: AppColors.textHint),
                const SizedBox(width: 4),
                Text('손절 ${fmtWon(item.stopLossPrice!)}',
                    style: const TextStyle(color: AppColors.neonRed, fontSize: 12)),
              ],
            ]),
          ],
        ]),
      ),
    );
  }
}

// ── 빠른 메뉴 2×4 그리드 ────────────────────────────────────────
class _QuickMenuGrid extends StatelessWidget {
  final _menus = const [
    _Menu(Icons.show_chart,             '실시간 시세', '/stocks'),
    _Menu(Icons.star_outline,           '관심종목',    '/watchlist'),
    _Menu(Icons.science_outlined,       '시뮬레이션',  '/simulate'),
    _Menu(Icons.compare_arrows_outlined,'비교분석',    '/compare'),
    _Menu(Icons.account_balance_wallet_outlined, '자산평가', '/portfolio'),
    _Menu(Icons.bar_chart,              'AI TOP 30', '/stocks'),
    _Menu(Icons.notifications_outlined,'알림설정',    '/settings'),
    _Menu(Icons.settings_outlined,     '환경설정',    '/settings'),
  ];

  @override
  Widget build(BuildContext context) => GridView.count(
    crossAxisCount: 4,
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    crossAxisSpacing: 10,
    mainAxisSpacing: 10,
    childAspectRatio: 0.9,
    children: _menus.map((m) => _QuickMenuItem(m)).toList(),
  );
}

class _QuickMenuItem extends StatelessWidget {
  const _QuickMenuItem(this.menu);
  final _Menu menu;

  @override
  Widget build(BuildContext context) => GestureDetector(
    onTap: () => context.go(menu.path),
    child: Container(
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(menu.icon, color: AppColors.neonBlue, size: 26),
        const SizedBox(height: 6),
        Text(menu.label,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary, fontSize: 10)),
      ]),
    ),
  );
}

class _Menu { const _Menu(this.icon, this.label, this.path);
  final IconData icon; final String label; final String path;
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.title, {required this.subtitle, this.action});
  final String title; final String subtitle; final Widget? action;

  @override
  Widget build(BuildContext context) => Row(children: [
    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(
          color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
      if (subtitle.isNotEmpty)
        Text(subtitle, style: const TextStyle(color: AppColors.textHint, fontSize: 11)),
    ])),
    if (action != null) action!,
  ]);
}

class _EmptyRecommendation extends StatelessWidget {
  const _EmptyRecommendation();
  @override
  Widget build(BuildContext context) => const SizedBox(
    height: 120,
    child: Center(child: Text('오늘의 AI 분석이 준비 중입니다.\n매일 오전 7시에 업데이트됩니다.',
        textAlign: TextAlign.center,
        style: TextStyle(color: AppColors.textSecondary))),
  );
}
