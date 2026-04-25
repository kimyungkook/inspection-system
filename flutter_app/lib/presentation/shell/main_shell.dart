import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../voice/voice_screen.dart';

class MainShell extends StatelessWidget {
  const MainShell({super.key, required this.child});
  final Widget child;

  static const _tabs = [
    _TabItem('/',          Icons.dashboard_outlined,              Icons.dashboard,             '대시보드'),
    _TabItem('/stocks',    Icons.show_chart,                      Icons.show_chart,            '주식현재가'),
    _TabItem('/watchlist', Icons.star_outline,                    Icons.star,                  '관심종목'),
    _TabItem('/simulate',  Icons.science_outlined,                Icons.science,               '시뮬레이션'),
    _TabItem('/compare',   Icons.compare_arrows_outlined,         Icons.compare_arrows,        '비교분석'),
    _TabItem('/portfolio', Icons.account_balance_wallet_outlined, Icons.account_balance_wallet,'자산평가'),
    _TabItem('/settings',  Icons.settings_outlined,               Icons.settings,              '설정'),
  ];

  @override
  Widget build(BuildContext context) {
    final loc = GoRouterState.of(context).matchedLocation;
    final idx = _tabs.indexWhere((t) => t.path == loc).clamp(0, _tabs.length - 1);

    return Scaffold(
      body: child,

      // 자비스 AI 플로팅 버튼
      floatingActionButton: _JarvisFab(),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,

      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: BottomAppBar(
          color: AppColors.bgCard,
          notchMargin: 6,
          shape: const CircularNotchedRectangle(),
          child: SizedBox(
            height: 60,
            child: Row(children: [
              // 왼쪽 탭 3개
              ..._tabs.sublist(0, 3).asMap().entries.map((e) =>
                  _NavItem(tab: e.value, active: idx == e.key,
                      onTap: () => context.go(e.value.path))),
              // 가운데 빈 공간 (FAB 자리)
              const Expanded(child: SizedBox()),
              // 오른쪽 탭 4개 (3~6)
              ..._tabs.sublist(3).asMap().entries.map((e) =>
                  _NavItem(tab: e.value, active: idx == e.key + 3,
                      onTap: () => context.go(e.value.path))),
            ]),
          ),
        ),
      ),
    );
  }
}

// ── 자비스 FAB ────────────────────────────────────────────────────
class _JarvisFab extends StatefulWidget {
  @override
  State<_JarvisFab> createState() => _JarvisFabState();
}

class _JarvisFabState extends State<_JarvisFab>
    with SingleTickerProviderStateMixin {
  late AnimationController _glowCtrl;
  late Animation<double> _glowAnim;

  @override
  void initState() {
    super.initState();
    _glowCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1500))
      ..repeat(reverse: true);
    _glowAnim = Tween(begin: 0.5, end: 1.0).animate(
        CurvedAnimation(parent: _glowCtrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _glowCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: _glowAnim,
    builder: (_, child) => Container(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: AppColors.neonBlue.withOpacity(_glowAnim.value * 0.5),
            blurRadius: 16,
            spreadRadius: 2,
          ),
        ],
      ),
      child: child,
    ),
    child: FloatingActionButton(
      onPressed: () => Navigator.push(context,
          MaterialPageRoute(builder: (_) => const VoiceScreen())),
      backgroundColor: AppColors.bgCard,
      shape: const CircleBorder(
          side: BorderSide(color: AppColors.neonBlue, width: 2)),
      elevation: 0,
      child: const Icon(Icons.smart_toy_outlined,
          color: AppColors.neonBlue, size: 26),
    ),
  );
}

// ── 하단 네비 아이템 ──────────────────────────────────────────────
class _NavItem extends StatelessWidget {
  const _NavItem({required this.tab, required this.active, required this.onTap});
  final _TabItem tab;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Expanded(
    child: InkWell(
      onTap: onTap,
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(active ? tab.activeIcon : tab.icon,
            color: active ? AppColors.neonGreen : AppColors.textHint,
            size: 22),
        const SizedBox(height: 2),
        Text(tab.label,
            style: TextStyle(
                color: active ? AppColors.neonGreen : AppColors.textHint,
                fontSize: 9)),
      ]),
    ),
  );
}

class _TabItem {
  const _TabItem(this.path, this.icon, this.activeIcon, this.label);
  final String path;
  final IconData icon;
  final IconData activeIcon;
  final String label;
}
