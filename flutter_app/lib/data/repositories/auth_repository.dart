import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../../core/constants.dart';
import '../../core/storage/secure_storage.dart';
import '../models/auth_model.dart';

final authRepoProvider = Provider((ref) => AuthRepository(ref.read(dioProvider)));

class AuthRepository {
  AuthRepository(this._dio);
  final dynamic _dio;

  Future<TokenResponse> login(String username, String password, {String? otp}) async {
    final res = await _dio.post(ApiPath.login, data: {
      'username': username,
      'password': password,
      if (otp != null) 'otp_code': otp,
    });
    final token = TokenResponse.fromJson(res.data);
    await SecureStorage.saveTokens(access: token.accessToken, refresh: token.refreshToken);
    await SecureStorage.saveUser(userId: token.userId, tier: token.tier);
    return token;
  }

  Future<void> signup({
    required String username,
    required String email,
    required String password,
    String? inviteCode,
  }) async {
    await _dio.post(ApiPath.signup, data: {
      'username': username,
      'email': email,
      'password': password,
      if (inviteCode != null && inviteCode.isNotEmpty) 'invite_code': inviteCode,
    });
  }

  Future<UserInfo> getMe() async {
    final res = await _dio.get(ApiPath.me);
    return UserInfo.fromJson(res.data);
  }

  Future<void> logout() async {
    try { await _dio.post(ApiPath.logout); } catch (_) {}
    await SecureStorage.clearAll();
  }

  Future<String> generateInviteCode() async {
    final res = await _dio.post(ApiPath.inviteCode);
    return res.data['code'];
  }
}
