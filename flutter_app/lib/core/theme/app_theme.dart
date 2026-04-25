import 'package:flutter/material.dart';

// 색상 팔레트
class AppColors {
  // 배경
  static const bg         = Color(0xFF0A0E1A);  // 메인 배경 (매우 어두운 남색)
  static const bgCard     = Color(0xFF141829);  // 카드 배경
  static const bgSurface  = Color(0xFF1C2035);  // 서피스

  // 네온 강조색
  static const neonGreen  = Color(0xFF00FF88);  // 매수/상승
  static const neonRed    = Color(0xFFFF3366);  // 매도/하락
  static const neonBlue   = Color(0xFF00BFFF);  // 정보
  static const neonYellow = Color(0xFFFFD700);  // 경고/S등급

  // 텍스트
  static const textPrimary   = Color(0xFFE0E6FF);
  static const textSecondary = Color(0xFF7B8DB8);
  static const textHint      = Color(0xFF4A5578);

  // 신호 등급 색상
  static const gradeS = Color(0xFFFFD700);  // 금색
  static const gradeA = Color(0xFF00FF88);  // 초록
  static const gradeB = Color(0xFF00BFFF);  // 파랑
  static const gradeC = Color(0xFF7B8DB8);  // 회색

  // 보더
  static const border = Color(0xFF2A3050);
}

class AppTheme {
  static ThemeData get dark => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.bg,
    colorScheme: const ColorScheme.dark(
      primary: AppColors.neonGreen,
      secondary: AppColors.neonBlue,
      surface: AppColors.bgCard,
      error: AppColors.neonRed,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.bg,
      elevation: 0,
      titleTextStyle: TextStyle(
        color: AppColors.textPrimary,
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
      iconTheme: IconThemeData(color: AppColors.textPrimary),
    ),
    cardTheme: CardThemeData(
      color: AppColors.bgCard,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.border, width: 1),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.bgCard,
      selectedItemColor: AppColors.neonGreen,
      unselectedItemColor: AppColors.textHint,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.bgSurface,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: AppColors.neonGreen, width: 1.5),
      ),
      labelStyle: const TextStyle(color: AppColors.textSecondary),
      hintStyle: const TextStyle(color: AppColors.textHint),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.neonGreen,
        foregroundColor: AppColors.bg,
        minimumSize: const Size(double.infinity, 50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
      ),
    ),
    textTheme: const TextTheme(
      headlineMedium: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold),
      bodyLarge:  TextStyle(color: AppColors.textPrimary),
      bodyMedium: TextStyle(color: AppColors.textSecondary),
      labelSmall: TextStyle(color: AppColors.textHint),
    ),
  );
}

// 등급 색상 헬퍼
Color gradeColor(String grade) => switch (grade) {
  'S' => AppColors.gradeS,
  'A' => AppColors.gradeA,
  'B' => AppColors.gradeB,
  _   => AppColors.gradeC,
};

// 등락 색상 헬퍼
Color changeColor(double rate) =>
    rate > 0 ? AppColors.neonGreen : rate < 0 ? AppColors.neonRed : AppColors.textSecondary;
