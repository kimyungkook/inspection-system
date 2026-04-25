import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants.dart';
import '../storage/secure_storage.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: AppConst.baseUrl,
    connectTimeout: AppConst.connectTimeout,
    receiveTimeout: AppConst.receiveTimeout,
    headers: {'Content-Type': 'application/json'},
  ));

  dio.interceptors.addAll([
    _AuthInterceptor(dio, ref),
    LogInterceptor(requestBody: true, responseBody: false),
  ]);

  return dio;
});

/// JWT 자동 주입 + 만료 시 자동 갱신 인터셉터
class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._dio, this._ref);
  final Dio _dio;
  final Ref _ref;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await SecureStorage.getAccess();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // 토큰 만료 → refresh token으로 재발급
      final refreshed = await _tryRefresh();
      if (refreshed) {
        final retry = await _retry(err.requestOptions);
        return handler.resolve(retry);
      }
      // 갱신 실패 → 로그인 화면으로
      await SecureStorage.clearAll();
    }
    handler.next(err);
  }

  Future<bool> _tryRefresh() async {
    final refresh = await SecureStorage.getRefresh();
    if (refresh == null) return false;
    try {
      final res = await _dio.post(
        ApiPath.refresh,
        data: {'refresh_token': refresh},
        options: Options(headers: {}), // 인터셉터 재귀 방지
      );
      await SecureStorage.saveTokens(
        access: res.data['access_token'],
        refresh: res.data['refresh_token'],
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<Response> _retry(RequestOptions req) async {
    final token = await SecureStorage.getAccess();
    req.headers['Authorization'] = 'Bearer $token';
    return _dio.fetch(req);
  }
}
