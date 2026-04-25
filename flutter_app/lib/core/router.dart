import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../core/storage/secure_storage.dart';
import '../presentation/auth/login_screen.dart';
import '../presentation/auth/signup_screen.dart';
import '../presentation/shell/main_shell.dart';
import '../presentation/dashboard/dashboard_screen.dart';
import '../presentation/stocks/stocks_screen.dart';
import '../presentation/watchlist/watchlist_screen.dart';
import '../presentation/simulation/simulation_screen.dart';
import '../presentation/compare/compare_screen.dart';
import '../presentation/portfolio/portfolio_screen.dart';
import '../presentation/settings/settings_screen.dart';

final routerProvider = GoRouter(
  initialLocation: '/',
  redirect: (ctx, state) async {
    final loggedIn = await SecureStorage.isLoggedIn();
    final onAuth = state.matchedLocation.startsWith('/login') ||
                   state.matchedLocation.startsWith('/signup');
    if (!loggedIn && !onAuth) return '/login';
    if (loggedIn && onAuth) return '/';
    return null;
  },
  routes: [
    GoRoute(path: '/login',  builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/signup', builder: (_, __) => const SignupScreen()),
    ShellRoute(
      builder: (_, __, child) => MainShell(child: child),
      routes: [
        GoRoute(path: '/',         builder: (_, __) => const DashboardScreen()),
        GoRoute(path: '/stocks',   builder: (_, __) => const StocksScreen()),
        GoRoute(path: '/watchlist',builder: (_, __) => const WatchlistScreen()),
        GoRoute(path: '/simulate', builder: (_, __) => const SimulationScreen()),
        GoRoute(path: '/compare',  builder: (_, __) => const CompareScreen()),
        GoRoute(path: '/portfolio',builder: (_, __) => const PortfolioScreen()),
        GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      ],
    ),
  ],
);
