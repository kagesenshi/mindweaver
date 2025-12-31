import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/ai_agent.dart';
import 'api_providers.dart';

class AIAgentListNotifier extends StateNotifier<AsyncValue<List<AIAgent>>> {
  final Ref ref;

  AIAgentListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadAgents();
  }

  Future<void> loadAgents() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/ai_agents',
        (json) => AIAgent.fromJson(json as Map<String, dynamic>),
      );
      if (!mounted) return;
      state = AsyncValue.data(response);
    } catch (e, st) {
      if (!mounted) return;
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createAgent(AIAgent agent) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post(
        '/api/v1/ai_agents',
        agent.toJson(),
        (json) => AIAgent.fromJson(json as Map<String, dynamic>),
      );
      await loadAgents();
    } catch (e) {
      rethrow;
    }
  }

  Future<void> deleteAgent(int id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.delete('/api/v1/ai_agents/$id');
      await loadAgents();
    } catch (e) {
      rethrow;
    }
  }
}

final aiAgentListProvider =
    StateNotifierProvider.autoDispose<
      AIAgentListNotifier,
      AsyncValue<List<AIAgent>>
    >((ref) {
      return AIAgentListNotifier(ref);
    });
