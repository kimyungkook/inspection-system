class TokenResponse {
  final String accessToken;
  final String refreshToken;
  final int userId;
  final String username;
  final String tier;

  const TokenResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.userId,
    required this.username,
    required this.tier,
  });

  factory TokenResponse.fromJson(Map<String, dynamic> j) => TokenResponse(
    accessToken:  j['access_token'],
    refreshToken: j['refresh_token'],
    userId:       j['user_id'],
    username:     j['username'],
    tier:         j['tier'],
  );
}

class UserInfo {
  final int id;
  final String username;
  final String email;
  final String? phone;
  final String tier;
  final bool otpEnabled;

  const UserInfo({
    required this.id,
    required this.username,
    required this.email,
    this.phone,
    required this.tier,
    required this.otpEnabled,
  });

  factory UserInfo.fromJson(Map<String, dynamic> j) => UserInfo(
    id:         j['id'],
    username:   j['username'],
    email:      j['email'],
    phone:      j['phone'],
    tier:       j['tier'],
    otpEnabled: j['otp_enabled'] ?? false,
  );
}
