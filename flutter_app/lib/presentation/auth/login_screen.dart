import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../data/repositories/auth_repository.dart';
import '../widgets/common_widgets.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _idCtrl  = TextEditingController();
  final _pwCtrl  = TextEditingController();
  bool _loading  = false;
  bool _pwHide   = true;

  @override
  void dispose() {
    _idCtrl.dispose();
    _pwCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ref.read(authRepoProvider).login(_idCtrl.text.trim(), _pwCtrl.text);
      if (mounted) context.go('/');
    } catch (e) {
      if (mounted) showErrorSnack(context, _parseError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Spacer(),
              // 로고 영역
              const _LogoBadge(),
              const SizedBox(height: 40),

              // 아이디
              AppTextField(
                controller: _idCtrl,
                label: '아이디',
                prefixIcon: Icons.person_outline,
                validator: (v) => (v?.isEmpty ?? true) ? '아이디를 입력하세요' : null,
              ),
              const SizedBox(height: 16),

              // 비밀번호
              AppTextField(
                controller: _pwCtrl,
                label: '비밀번호',
                prefixIcon: Icons.lock_outline,
                obscure: _pwHide,
                suffixIcon: IconButton(
                  icon: Icon(_pwHide ? Icons.visibility_off : Icons.visibility,
                      color: AppColors.textHint),
                  onPressed: () => setState(() => _pwHide = !_pwHide),
                ),
                validator: (v) => (v?.isEmpty ?? true) ? '비밀번호를 입력하세요' : null,
                onSubmit: (_) => _login(),
              ),
              const SizedBox(height: 24),

              // 로그인 버튼
              _loading
                  ? const Center(child: CircularProgressIndicator(color: AppColors.neonGreen))
                  : ElevatedButton(onPressed: _login, child: const Text('로그인')),

              const SizedBox(height: 16),
              // 회원가입 이동
              Center(
                child: TextButton(
                  onPressed: () => context.push('/signup'),
                  child: const Text('계정이 없으신가요? 회원가입',
                      style: TextStyle(color: AppColors.neonBlue)),
                ),
              ),
              const Spacer(),
            ],
          ),
        ),
      ),
    ),
  );

  String _parseError(dynamic e) {
    try { return e.response?.data['detail'] ?? '로그인 실패'; } catch (_) { return '네트워크 오류'; }
  }
}

class _LogoBadge extends StatelessWidget {
  const _LogoBadge();
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.neonGreen.withOpacity(0.15),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: AppColors.neonGreen.withOpacity(0.4)),
        ),
        child: const Text('AI POWERED', style: TextStyle(color: AppColors.neonGreen, fontSize: 11)),
      ),
      const SizedBox(height: 10),
      const Text('주식 매매\n가이드', style: TextStyle(
        color: AppColors.textPrimary, fontSize: 34, fontWeight: FontWeight.bold, height: 1.2)),
      const SizedBox(height: 8),
      const Text('AI가 분석하고 타이밍을 알려드립니다',
          style: TextStyle(color: AppColors.textSecondary, fontSize: 14)),
    ],
  );
}
