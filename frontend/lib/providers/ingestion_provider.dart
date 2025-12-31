import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/ingestion.dart';
import 'api_providers.dart';

class IngestionListNotifier extends StateNotifier<AsyncValue<List<Ingestion>>> {
  final Ref ref;

  IngestionListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadIngestions();
  }

  Future<void> loadIngestions() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/ingestions',
        (json) => Ingestion.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createIngestion(Ingestion ingestion) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/ingestions',
        ingestion.toJson(),
        (json) => Ingestion.fromJson(json as Map<String, dynamic>),
      );
      await loadIngestions();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteIngestion(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/ingestions/$id');
      await loadIngestions();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> executeIngestion(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post('/api/v1/ingestions/$id/execute', {}, (json) => json);
    } catch (e) {
      rethrow;
    }
  }

  Future<List<IngestionRun>> getRuns(int ingestionId) async {
    try {
      final client = ref.read(apiClientProvider);
      return await client.listAll(
        '/api/v1/ingestions/$ingestionId/runs',
        (json) => IngestionRun.fromJson(json as Map<String, dynamic>),
      );
    } catch (e) {
      rethrow;
    }
  }
}

final ingestionListProvider =
    StateNotifierProvider.autoDispose<
      IngestionListNotifier,
      AsyncValue<List<Ingestion>>
    >((ref) {
      return IngestionListNotifier(ref);
    });
