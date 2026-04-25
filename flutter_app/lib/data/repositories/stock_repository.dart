import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../../core/constants.dart';
import '../models/stock_model.dart';

final stockRepoProvider = Provider((ref) => StockRepository(ref.read(dioProvider)));

class StockRepository {
  StockRepository(this._dio);
  final dynamic _dio;

  Future<StockPrice> getPrice(String ticker) async {
    final res = await _dio.get(ApiPath.price(ticker));
    return StockPrice.fromJson(res.data);
  }

  Future<TechIndicators> getIndicators(String ticker, {String timeframe = '5'}) async {
    final res = await _dio.get(ApiPath.indicators(ticker), queryParameters: {'timeframe': timeframe});
    return TechIndicators.fromJson(res.data);
  }

  Future<List<Map<String, dynamic>>> getCandles(String ticker, {String type = 'daily'}) async {
    final res = await _dio.get(ApiPath.candles(ticker), queryParameters: {'type': type});
    return List<Map<String, dynamic>>.from(res.data['data']);
  }

  Future<List<AiRecommendation>> getTop5() async {
    final res = await _dio.get(ApiPath.aiTop5);
    return (res.data as List).map((e) => AiRecommendation.fromJson(e)).toList();
  }

  Future<List<WatchlistItem>> getWatchlist() async {
    final res = await _dio.get(ApiPath.watchlist);
    return (res.data as List).map((e) => WatchlistItem.fromJson(e)).toList();
  }

  Future<void> addWatchlist(String ticker) => _dio.post(ApiPath.addWatch(ticker));
  Future<void> removeWatchlist(int id)     => _dio.delete(ApiPath.delWatch(id));
}
