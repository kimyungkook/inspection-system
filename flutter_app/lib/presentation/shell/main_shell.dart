import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';

class MainShell extends StatelessWidget {
  const MainShell({super.key, required this.child});
  final Widget child;

  static const _tabs = [
    _TabItem('/',          Icons.dashboard_outlined,     Icons.dashboard,     '대시보드'),
    _TabItem('/stocks',    Icons.show_chart,              Icons.show_chart,    '주식현재가'),
    _TabItem('/watchlist', Icons.star_outline,            Icons.star,          '관심종목'),
    _TabItem('/simulate',  Icons.science_outlined,        Icons.science,       '시뮬레이션'),
    _TabItem('/compare',   Icons.compare_arrows_outlined, Icons.compare_arrows,'비교분석'),
    _TabItem('/portfolio', Icons.account_balance_wallet_outlined,
                           Icons.account_balance_wallet, '자산평가'),
    _TabItem('/settings',  Icons.settings_outlined,       Icons.settings,      '설정'),
  ];

  @override
  Widget build(BuildContext context) {
    final loc = GoRouterState.of(context).matchedLocation;
    final idx = _tabs.indexWhere((t) => t.path == loc).clamp(0, _tabs.length - 1);

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: AppColors.border)),
        ),
        child: BottomNavigationBar(
          currentIndex: idx,
          onTap: (i) => context.go(_tabs[i].path),
          items: _tabs.map((t) => BottomNavigationBarItem(
            icon:       Icon(t.icon),
            activeIcon: Icon(t.activeIcon),
            label: t.label,
          )).toList(),
        ),
      ),
    );
  }
}

class _TabItem {
  const _TabItem(this.path, this.icon, this.activeIcon, this.label);
  final String path;
  final IconData icon;
  final IconData activeIcon;
  final String label;
}
