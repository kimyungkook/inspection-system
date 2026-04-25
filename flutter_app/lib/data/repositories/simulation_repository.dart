import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../../core/constants.dart';
import '../models/simulation_model.dart';

final simRepoProvider = Provider((ref) => SimRepository(ref.read(dioProvider)));

class SimRepository {
  SimRepository(this._dio);
  final dynamic _dio;

  Future<SimAccount?> getAccount() async {
    final res = await _dio.get(ApiPath.simAccounts);
    final list = res.data as List;
    return list.isEmpty ? null : SimAccount.fromJson(list.first);
  }

  Future<List<SimPosition>> getPositions() async {
    final res = await _dio.get(ApiPath.simPositions);
    return (res.data as List).map((e) => SimPosition.fromJson(e)).toList();
  }

  Future<void> trade({
    required String ticker,
    required String tradeType,
    required int quantity,
  }) => _dio.post(ApiPath.simTrades, data: {
    'ticker': ticker,
    'trade_type': tradeType,
    'quantity': quantity,
  });

  Future<SimAccount> createAccount({required double initialBalance}) async {
    final res = await _dio.post(ApiPath.simAccounts,
        data: {'initial_balance': initialBalance});
    return SimAccount.fromJson(res.data);
  }
}
