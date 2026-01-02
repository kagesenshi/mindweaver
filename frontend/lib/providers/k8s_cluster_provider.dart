import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/k8s_cluster.dart';
import 'api_providers.dart';

class K8sClusterListNotifier
    extends StateNotifier<AsyncValue<List<K8sCluster>>> {
  final Ref ref;

  K8sClusterListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadClusters();
  }

  Future<void> loadClusters() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/k8s_clusters',
        (json) => K8sCluster.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createCluster(K8sCluster cluster) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/k8s_clusters',
        cluster.toJson(),
        (json) => K8sCluster.fromJson(json as Map<String, dynamic>),
      );
      await loadClusters();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> updateCluster(K8sCluster cluster) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.put(
        '/api/v1/k8s_clusters/${cluster.id}',
        cluster.toJson(),
        (json) => K8sCluster.fromJson(json as Map<String, dynamic>),
      );
      await loadClusters();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteCluster(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/k8s_clusters/$id');
      await loadClusters();
    } catch (e) {
      rethrow;
    }
  }
}

final k8sClusterListProvider =
    StateNotifierProvider.autoDispose<
      K8sClusterListNotifier,
      AsyncValue<List<K8sCluster>>
    >((ref) {
      ref.watch(apiClientProvider);
      return K8sClusterListNotifier(ref);
    });
