import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/knowledge_db.dart';
import 'api_providers.dart';

class KnowledgeDBListNotifier
    extends StateNotifier<AsyncValue<List<KnowledgeDB>>> {
  final Ref ref;

  KnowledgeDBListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadDBs();
  }

  Future<void> loadDBs() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/knowledge_dbs',
        (json) => KnowledgeDB.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createDB(KnowledgeDB db) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/knowledge_dbs',
        db.toJson(),
        (json) => KnowledgeDB.fromJson(json as Map<String, dynamic>),
      );
      await loadDBs();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateDB(KnowledgeDB db) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.put(
        '/api/v1/knowledge_dbs/${db.id}',
        db.toJson(),
        (json) => KnowledgeDB.fromJson(json as Map<String, dynamic>),
      );
      await loadDBs();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteDB(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/knowledge_dbs/$id');
      await loadDBs();
    } catch (e) {
      rethrow;
    }
  }
}

final knowledgeDBListProvider =
    StateNotifierProvider.autoDispose<
      KnowledgeDBListNotifier,
      AsyncValue<List<KnowledgeDB>>
    >((ref) {
      ref.watch(apiClientProvider);
      return KnowledgeDBListNotifier(ref);
    });
