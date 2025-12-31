import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/data_source.dart';
import 'api_providers.dart';

class DataSourceListNotifier
    extends StateNotifier<AsyncValue<List<DataSource>>> {
  final Ref ref;

  DataSourceListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadSources();
  }

  Future<void> loadSources() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/data_sources',
        (json) => DataSource.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createSource(DataSource source) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/data_sources',
        source.toJson(),
        (json) => DataSource.fromJson(json as Map<String, dynamic>),
      );
      await loadSources();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateSource(DataSource source) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.put(
        '/api/v1/data_sources/${source.id}',
        source.toJson(),
        (json) => DataSource.fromJson(json as Map<String, dynamic>),
      );
      await loadSources();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteSource(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/data_sources/$id');
      await loadSources();
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> testConnection(
    String type,
    Map<String, dynamic> params, {
    int? sourceId,
  }) async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.post(
        '/api/v1/data_sources/test_connection',
        {'type': type, 'parameters': params, 'source_id': sourceId},
        (json) => json as Map<String, dynamic>,
      );
      return response.record!;
    } catch (e) {
      rethrow;
    }
  }
}

final dataSourceListProvider =
    StateNotifierProvider.autoDispose<
      DataSourceListNotifier,
      AsyncValue<List<DataSource>>
    >((ref) {
      ref.watch(apiClientProvider);
      return DataSourceListNotifier(ref);
    });
