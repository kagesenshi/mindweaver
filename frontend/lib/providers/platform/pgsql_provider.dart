import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../models/platform/pgsql.dart';
import '../../models/platform/state.dart';
import '../api_providers.dart';

class PgSqlPlatformListNotifier
    extends StateNotifier<AsyncValue<List<PgSqlPlatform>>> {
  final Ref ref;

  PgSqlPlatformListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadPlatforms();
  }

  Future<void> loadPlatforms() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/platform/pgsql',
        (json) => PgSqlPlatform.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createPlatform(PgSqlPlatform platform) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/platform/pgsql',
        platform.toJson(),
        (json) => PgSqlPlatform.fromJson(json as Map<String, dynamic>),
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updatePlatform(PgSqlPlatform platform) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.put(
        '/api/v1/platform/pgsql/${platform.id}',
        platform.toJson(),
        (json) => PgSqlPlatform.fromJson(json as Map<String, dynamic>),
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deletePlatform(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/platform/pgsql/$id');
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updatePlatformState(int id, {bool? active}) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.postRaw('/api/v1/platform/pgsql/$id/_state', {
        'active': active,
      });
      ref.invalidate(pgsqlPlatformStateProvider(id));
    } catch (e) {
      rethrow;
    }
  }
}

final pgsqlPlatformListProvider =
    StateNotifierProvider.autoDispose<
      PgSqlPlatformListNotifier,
      AsyncValue<List<PgSqlPlatform>>
    >((ref) {
      ref.watch(apiClientProvider);
      return PgSqlPlatformListNotifier(ref);
    });

final pgsqlPlatformStateProvider = FutureProvider.autoDispose
    .family<PlatformState, int>((ref, id) async {
      final client = ref.watch(apiClientProvider);
      final json = await client.getRaw('/api/v1/platform/pgsql/$id/_state');
      if (json.isEmpty) {
        return PlatformState(platform_id: id, status: 'offline', active: false);
      }
      return PlatformState.fromJson(json);
    });
