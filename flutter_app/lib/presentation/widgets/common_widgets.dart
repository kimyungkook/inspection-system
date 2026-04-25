import 'package:flutter/material.dart';
import 'package:shimmer/shimmer.dart';
import '../../core/theme/app_theme.dart';

// ── 텍스트 입력 필드 ────────────────────────────────────────────
class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    required this.controller,
    required this.label,
    this.prefixIcon,
    this.suffixIcon,
    this.obscure = false,
    this.keyboardType,
    this.validator,
    this.onSubmit,
  });
  final TextEditingController controller;
  final String label;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final bool obscure;
  final TextInputType? keyboardType;
  final String? Function(String?)? validator;
  final void Function(String)? onSubmit;

  @override
  Widget build(BuildContext context) => TextFormField(
    controller: controller,
    obscureText: obscure,
    keyboardType: keyboardType,
    validator: validator,
    onFieldSubmitted: onSubmit,
    style: const TextStyle(color: AppColors.textPrimary),
    decoration: InputDecoration(
      labelText: label,
      prefixIcon: prefixIcon != null
          ? Icon(prefixIcon, color: AppColors.textHint, size: 20)
          : null,
      suffixIcon: suffixIcon,
    ),
  );
}

// ── 신호 등급 배지 ───────────────────────────────────────────────
class GradeBadge extends StatelessWidget {
  const GradeBadge(this.grade, {super.key});
  final String grade;

  @override
  Widget build(BuildContext context) {
    final color = gradeColor(grade);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(5),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(grade,
          style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }
}

// ── 가격 변동 텍스트 ─────────────────────────────────────────────
class PriceChangeText extends StatelessWidget {
  const PriceChangeText(this.rate, {super.key, this.fontSize = 13});
  final double rate;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final color = changeColor(rate);
    final sign  = rate > 0 ? '+' : '';
    return Text('$sign${rate.toStringAsFixed(2)}%',
        style: TextStyle(color: color, fontSize: fontSize, fontWeight: FontWeight.w600));
  }
}

// ── 가격 포맷 헬퍼 ───────────────────────────────────────────────
String fmtPrice(double price) {
  if (price == 0) return '-';
  if (price >= 10000) {
    return '${(price / 10000).toStringAsFixed(1)}만';
  }
  return price.toStringAsFixed(0).replaceAllMapped(
    RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]},');
}

String fmtWon(double price) =>
    '${price.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d)(?=(\d{3})+$)'), (m) => '${m[1]},')}원';

// ── 스켈레톤 로딩 카드 ───────────────────────────────────────────
class SkeletonCard extends StatelessWidget {
  const SkeletonCard({super.key, this.height = 80});
  final double height;

  @override
  Widget build(BuildContext context) => Shimmer.fromColors(
    baseColor: AppColors.bgSurface,
    highlightColor: AppColors.border,
    child: Container(
      height: height,
      margin: const EdgeInsets.symmetric(vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.bgSurface,
        borderRadius: BorderRadius.circular(12),
      ),
    ),
  );
}

// ── 오류 표시 위젯 ───────────────────────────────────────────────
class ErrorView extends StatelessWidget {
  const ErrorView(this.message, {super.key, this.onRetry});
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.error_outline, color: AppColors.neonRed, size: 40),
      const SizedBox(height: 12),
      Text(message, style: const TextStyle(color: AppColors.textSecondary), textAlign: TextAlign.center),
      if (onRetry != null) ...[
        const SizedBox(height: 12),
        TextButton(onPressed: onRetry, child: const Text('다시 시도', style: TextStyle(color: AppColors.neonBlue))),
      ],
    ]),
  );
}

// ── 스낵바 헬퍼 ──────────────────────────────────────────────────
void showErrorSnack(BuildContext ctx, String msg) =>
    ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: AppColors.neonRed.withOpacity(0.85),
    ));

void showSuccessSnack(BuildContext ctx, String msg) =>
    ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: AppColors.neonGreen.withOpacity(0.85),
    ));

// ── 구분선 ───────────────────────────────────────────────────────
const appDivider = Divider(color: AppColors.border, height: 1);
