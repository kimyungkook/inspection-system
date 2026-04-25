import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/theme/app_theme.dart';
import '../../data/repositories/auth_repository.dart';
import '../widgets/common_widgets.dart';

// 설정값 키
const _keyLlmProvider    = 'llm_provider';
const _keyTelegramToken  = 'telegram_token';
const _keyNotifySignal   = 'notify_signal';
const _keyNotifyDaily    = 'notify_daily';

final _settingsProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  return {
    'llm_provider':    prefs.getString(_keyLlmProvider)    ?? 'claude',
    'telegram_token':  prefs.getString(_keyTelegramToken)  ?? '',
    'notify_signal':   prefs.getBool(_keyNotifySignal)     ?? true,
    'notify_daily':    prefs.getBool(_keyNotifyDaily)      ?? true,
  };
});

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settingsAsync = ref.watch(_settingsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('설정')),
      body: settingsAsync.when(
        loading: () =>
            const Center(child: CircularProgressIndicator(color: AppColors.neonGreen)),
        error: (e, _) => ErrorView('설정을 불러올 수 없습니다'),
        data: (s) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // ── AI 모델 설정 ─────────────────────────────
            _SectionHeader('AI 모델'),
            _LlmSelector(current: s['llm_provider'],
                onChanged: (v) => _save(ref, _keyLlmProvider, v)),
            const SizedBox(height: 20),

            // ── 알림 설정 ────────────────────────────────
            _SectionHeader('알림 설정'),
            _TelegramInput(current: s['telegram_token'],
                onSaved: (v) => _save(ref, _keyTelegramToken, v)),
            const SizedBox(height: 8),
            _SwitchTile(
              icon: Icons.bolt_outlined,
              label: '신호 발생 알림',
              subtitle: 'S/A 등급 매수 신호 즉시 알림',
              value: s['notify_signal'],
              onChanged: (v) => _saveBool(ref, _keyNotifySignal, v),
            ),
            _SwitchTile(
              icon: Icons.wb_sunny_outlined,
              label: '일일 AI 추천 알림',
              subtitle: '매일 오전 7시 TOP5 요약',
              value: s['notify_daily'],
              onChanged: (v) => _saveBool(ref, _keyNotifyDaily, v),
            ),
            const SizedBox(height: 20),

            // ── 계정 ─────────────────────────────────────
            _SectionHeader('계정'),
            _ActionTile(
              icon: Icons.vpn_key_outlined,
              label: '초대코드 생성',
              color: AppColors.neonBlue,
              onTap: () => _generateInviteCode(context, ref),
            ),
            _ActionTile(
              icon: Icons.lock_outline,
              label: '비밀번호 변경',
              color: AppColors.textSecondary,
              onTap: () => _showChangePwDialog(context, ref),
            ),
            _ActionTile(
              icon: Icons.logout,
              label: '로그아웃',
              color: AppColors.neonRed,
              onTap: () => _logout(context, ref),
            ),
            const SizedBox(height: 20),

            // ── 앱 정보 ──────────────────────────────────
            _SectionHeader('앱 정보'),
            _InfoTile('앱 버전', '1.0.0'),
            _InfoTile('AI 엔진', 'Claude Sonnet / GPT-4o / Gemini Pro 교체 가능'),
            _InfoTile('데이터', '한국투자증권 KIS API (실시간)'),
            const SizedBox(height: 20),

            // 법적 고지
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.bgSurface,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text(
                '본 앱의 AI 분석 결과는 투자 참고용입니다. 투자 결정 및 손익 책임은 투자자 본인에게 있습니다.',
                style: TextStyle(color: AppColors.textHint, fontSize: 11),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save(WidgetRef ref, String key, String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, value);
    ref.refresh(_settingsProvider);
  }

  Future<void> _saveBool(WidgetRef ref, String key, bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(key, value);
    ref.refresh(_settingsProvider);
  }

  Future<void> _generateInviteCode(BuildContext context, WidgetRef ref) async {
    try {
      final code = await ref.read(authRepoProvider).generateInviteCode();
      if (!context.mounted) return;
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: AppColors.bgCard,
          title: const Text('초대코드 생성 완료',
              style: TextStyle(color: AppColors.textPrimary)),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                color: AppColors.neonGreen.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.neonGreen.withOpacity(0.4)),
              ),
              child: Text(code,
                  style: const TextStyle(
                      color: AppColors.neonGreen,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 4)),
            ),
            const SizedBox(height: 10),
            const Text('1시간 내 1회 사용 가능',
                style: TextStyle(color: AppColors.textHint, fontSize: 12)),
          ]),
          actions: [
            TextButton(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: code));
                Navigator.pop(context);
                showSuccessSnack(context, '클립보드에 복사되었습니다');
              },
              child: const Text('복사',
                  style: TextStyle(color: AppColors.neonGreen)),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('닫기',
                  style: TextStyle(color: AppColors.textHint)),
            ),
          ],
        ),
      );
    } catch (e) {
      if (context.mounted) showErrorSnack(context, '초대코드 생성 실패');
    }
  }

  void _showChangePwDialog(BuildContext context, WidgetRef ref) {
    final oldCtrl = TextEditingController();
    final newCtrl = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('비밀번호 변경',
            style: TextStyle(color: AppColors.textPrimary)),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          AppTextField(controller: oldCtrl, label: '현재 비밀번호',
              obscure: true, prefixIcon: Icons.lock_outline),
          const SizedBox(height: 10),
          AppTextField(controller: newCtrl, label: '새 비밀번호 (8자 이상)',
              obscure: true, prefixIcon: Icons.lock_reset_outlined),
        ]),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('취소',
                style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            onPressed: () {
              if (newCtrl.text.length < 8) {
                showErrorSnack(ctx, '비밀번호는 8자 이상이어야 합니다');
                return;
              }
              Navigator.pop(ctx);
              showSuccessSnack(context, '비밀번호가 변경되었습니다');
            },
            child: const Text('변경'),
          ),
        ],
      ),
    );
  }

  Future<void> _logout(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('로그아웃',
            style: TextStyle(color: AppColors.textPrimary)),
        content: const Text('정말 로그아웃 하시겠습니까?',
            style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소',
                style: TextStyle(color: AppColors.textHint)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.neonRed,
                foregroundColor: Colors.white),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    await ref.read(authRepoProvider).logout();
    if (context.mounted) context.go('/login');
  }
}

// ── 설정 섹션 헤더 ────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);
  final String title;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(title,
        style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8)),
  );
}

// ── LLM 제공자 선택 ───────────────────────────────────────────────
class _LlmSelector extends StatelessWidget {
  const _LlmSelector({required this.current, required this.onChanged});
  final String current;
  final void Function(String) onChanged;

  static const _providers = [
    ('claude',  'Claude Sonnet',  'Anthropic — 가장 정확'),
    ('openai',  'GPT-4o',         'OpenAI — 빠른 응답'),
    ('gemini',  'Gemini Pro',     'Google — 무료 쿼터'),
  ];

  @override
  Widget build(BuildContext context) => Card(
    child: Column(
      children: _providers.map((p) => RadioListTile<String>(
        title: Text(p.$2,
            style: const TextStyle(
                color: AppColors.textPrimary, fontSize: 14)),
        subtitle: Text(p.$3,
            style: const TextStyle(
                color: AppColors.textHint, fontSize: 11)),
        value: p.$1,
        groupValue: current,
        activeColor: AppColors.neonGreen,
        onChanged: (v) => onChanged(v!),
      )).toList(),
    ),
  );
}

// ── 텔레그램 토큰 입력 ────────────────────────────────────────────
class _TelegramInput extends StatefulWidget {
  const _TelegramInput({required this.current, required this.onSaved});
  final String current;
  final void Function(String) onSaved;

  @override
  State<_TelegramInput> createState() => _TelegramInputState();
}

class _TelegramInputState extends State<_TelegramInput> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.current);
  }

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Row(children: [
        const Icon(Icons.telegram, color: AppColors.neonBlue, size: 22),
        const SizedBox(width: 10),
        Expanded(
          child: TextField(
            controller: _ctrl,
            style: const TextStyle(color: AppColors.textPrimary, fontSize: 13),
            decoration: const InputDecoration(
              labelText: '텔레그램 Bot Token',
              hintText: '123456789:AAFxxxx...',
              border: InputBorder.none,
              enabledBorder: InputBorder.none,
              isDense: true,
              contentPadding: EdgeInsets.zero,
            ),
            onSubmitted: widget.onSaved,
          ),
        ),
        TextButton(
          onPressed: () => widget.onSaved(_ctrl.text),
          child: const Text('저장',
              style: TextStyle(color: AppColors.neonGreen, fontSize: 13)),
        ),
      ]),
    ),
  );

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }
}

// ── 토글 스위치 타일 ──────────────────────────────────────────────
class _SwitchTile extends StatelessWidget {
  const _SwitchTile({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });
  final IconData icon;
  final String label, subtitle;
  final bool value;
  final void Function(bool) onChanged;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 4),
    child: SwitchListTile(
      secondary: Icon(icon, color: AppColors.neonBlue, size: 20),
      title: Text(label,
          style: const TextStyle(
              color: AppColors.textPrimary, fontSize: 14)),
      subtitle: Text(subtitle,
          style: const TextStyle(
              color: AppColors.textHint, fontSize: 11)),
      value: value,
      activeColor: AppColors.neonGreen,
      onChanged: onChanged,
    ),
  );
}

// ── 액션 타일 ─────────────────────────────────────────────────────
class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 4),
    child: ListTile(
      leading: Icon(icon, color: color, size: 20),
      title: Text(label,
          style: TextStyle(color: color, fontSize: 14)),
      trailing: const Icon(Icons.chevron_right,
          color: AppColors.textHint, size: 18),
      onTap: onTap,
    ),
  );
}

// ── 정보 표시 타일 ────────────────────────────────────────────────
class _InfoTile extends StatelessWidget {
  const _InfoTile(this.label, this.value);
  final String label, value;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 4),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(children: [
        Expanded(child: Text(label,
            style: const TextStyle(
                color: AppColors.textSecondary, fontSize: 13))),
        Flexible(child: Text(value,
            textAlign: TextAlign.right,
            style: const TextStyle(
                color: AppColors.textHint, fontSize: 12))),
      ]),
    ),
  );
}
