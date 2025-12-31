import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/lakehouse_storage.dart';
import 'api_providers.dart';

class LakehouseStorageListNotifier
    extends StateNotifier<AsyncValue<List<LakehouseStorage>>> {
  final Ref ref;

  LakehouseStorageListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadStorages();
  }

  Future<void> loadStorages() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/lakehouse_storages',
        (json) => LakehouseStorage.fromJson(json as Map<String, dynamic>),
      );
      state = AsyncValue.data(response);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createStorage(LakehouseStorage storage) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/lakehouse_storages',
        storage.toJson(),
        (json) => LakehouseStorage.fromJson(json as Map<String, dynamic>),
      );
      await loadStorages();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteStorage(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/lakehouse_storages/$id');
      await loadStorages();
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> testConnection(
    Map<String, dynamic> params, {
    int? storageId,
  }) async {
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.post(
        '/api/v1/lakehouse_storages/test_connection',
        {'parameters': params, 'storage_id': storageId},
        (json) => json as Map<String, dynamic>,
      );
      return response.record!;
    } catch (e) {
      rethrow;
    }
  }
}

final lakehouseStorageListProvider =
    StateNotifierProvider.autoDispose<
      LakehouseStorageListNotifier,
      AsyncValue<List<LakehouseStorage>>
    >((ref) {
      return LakehouseStorageListNotifier(ref);
    });
