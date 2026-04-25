import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants.dart';

/// JWT 토큰을 암호화된 로컬 저장소에 보관
class SecureStorage {
  static const _s = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  static Future<void> saveTokens({
    required String access,
    required String refresh,
  }) async {
    await Future.wait([
      _s.write(key: AppConst.keyAccess,  value: access),
      _s.write(key: AppConst.keyRefresh, value: refresh),
    ]);
  }

  static Future<void> saveUser({
    required int userId,
    required String tier,
  }) async {
    await Future.wait([
      _s.write(key: AppConst.keyUserId, value: userId.toString()),
      _s.write(key: AppConst.keyTier,   value: tier),
    ]);
  }

  static Future<String?> getAccess()  => _s.read(key: AppConst.keyAccess);
  static Future<String?> getRefresh() => _s.read(key: AppConst.keyRefresh);
  static Future<String?> getUserId()  => _s.read(key: AppConst.keyUserId);
  static Future<String?> getTier()    => _s.read(key: AppConst.keyTier);

  static Future<bool> isLoggedIn() async =>
      (await getAccess()) != null;

  static Future<void> clearAll() => _s.deleteAll();
}
