import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/s3_storage.dart';
import 'api_providers.dart';

class S3StorageListNotifier extends StateNotifier<AsyncValue<List<S3Storage>>> {
  final Ref ref;

  S3StorageListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadStorages();
  }

  Future<void> loadStorages() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/s3_storages',
        (json) => S3Storage.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createStorage(S3Storage storage) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/s3_storages',
        storage.toJson(),
        (json) => S3Storage.fromJson(json as Map<String, dynamic>),
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateStorage(S3Storage storage) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.put(
        '/api/v1/s3_storages/${storage.id}',
        storage.toJson(),
        (json) => S3Storage.fromJson(json as Map<String, dynamic>),
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteStorage(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/s3_storages/$id');
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
        '/api/v1/s3_storages/test_connection',
        {'parameters': params, 'storage_id': storageId},
        (json) => json as Map<String, dynamic>,
      );
      return response.record!;
    } catch (e) {
      rethrow;
    }
  }
}

final s3StorageListProvider =
    StateNotifierProvider.autoDispose<
      S3StorageListNotifier,
      AsyncValue<List<S3Storage>>
    >((ref) {
      ref.watch(apiClientProvider);
      return S3StorageListNotifier(ref);
    });
