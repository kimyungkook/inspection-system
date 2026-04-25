import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../data/repositories/auth_repository.dart';
import '../widgets/common_widgets.dart';

class SignupScreen extends ConsumerStatefulWidget {
  const SignupScreen({super.key});
  @override
  ConsumerState<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends ConsumerState<SignupScreen> {
  final _formKey   = GlobalKey<FormState>();
  final _idCtrl    = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _pwCtrl    = TextEditingController();
  final _pw2Ctrl   = TextEditingController();
  final _invCtrl   = TextEditingController();
  bool _loading    = false;

  @override
  void dispose() {
    for (final c in [_idCtrl, _emailCtrl, _pwCtrl, _pw2Ctrl, _invCtrl]) c.dispose();
    super.dispose();
  }

  Future<void> _signup() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ref.read(authRepoProvider).signup(
        username:   _idCtrl.text.trim(),
        email:      _emailCtrl.text.trim(),
        password:   _pwCtrl.text,
        inviteCode: _invCtrl.text.trim().isEmpty ? null : _invCtrl.text.trim(),
      );
      if (mounted) {
        showSuccessSnack(context, '회원가입 완료! 로그인해주세요.');
        context.pop();
      }
    } catch (e) {
      if (mounted) showErrorSnack(context, _parseError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('회원가입')),
    body: SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Form(
        key: _formKey,
        child: Column(children: [
          AppTextField(
            controller: _idCtrl, label: '아이디 (4~20자)',
            prefixIcon: Icons.person_outline,
            validator: (v) {
              if (v == null || v.length < 4) return '4자 이상 입력하세요';
              if (v.length > 20) return '20자 이하로 입력하세요';
              return null;
            },
          ),
          const SizedBox(height: 14),
          AppTextField(
            controller: _emailCtrl, label: '이메일',
            prefixIcon: Icons.email_outlined,
            keyboardType: TextInputType.emailAddress,
            validator: (v) => (v?.contains('@') ?? false) ? null : '올바른 이메일을 입력하세요',
          ),
          const SizedBox(height: 14),
          AppTextField(
            controller: _pwCtrl, label: '비밀번호',
            prefixIcon: Icons.lock_outline, obscure: true,
            validator: (v) {
              if ((v?.length ?? 0) < 8) return '8자 이상 입력하세요';
              if (!RegExp(r'[A-Z]').hasMatch(v!)) return '대문자를 포함해야 합니다';
              if (!RegExp(r'[0-9]').hasMatch(v))  return '숫자를 포함해야 합니다';
              if (!RegExp(r'[!@#\$%]').hasMatch(v)) return '특수문자(!@#\$%)를 포함해야 합니다';
              return null;
            },
          ),
          const SizedBox(height: 14),
          AppTextField(
            controller: _pw2Ctrl, label: '비밀번호 확인',
            prefixIcon: Icons.lock_outline, obscure: true,
            validator: (v) => v != _pwCtrl.text ? '비밀번호가 일치하지 않습니다' : null,
          ),
          const SizedBox(height: 14),
          AppTextField(
            controller: _invCtrl, label: '초대코드 (선택)',
            prefixIcon: Icons.card_gift_card_outlined,
          ),
          const SizedBox(height: 28),
          _loading
              ? const CircularProgressIndicator(color: AppColors.neonGreen)
              : ElevatedButton(onPressed: _signup, child: const Text('가입하기')),
        ]),
      ),
    ),
  );

  String _parseError(dynamic e) {
    try { return e.response?.data['detail'] ?? '가입 실패'; } catch (_) { return '네트워크 오류'; }
  }
}
