import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/ai_agent.dart';
import 'package:mindweaver_flutter/providers/ai_agent_provider.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'mocks/api_client_mock.dart';

void main() {
  late MockApiClient mockClient;
  late ProviderContainer container;

  setUp(() {
    mockClient = MockApiClient();
    container = ProviderContainer(
      overrides: [apiClientProvider.overrideWithValue(mockClient)],
    );
  });

  tearDown(() {
    container.dispose();
  });

  group('AIAgentListNotifier', () {
    test('loadAgents fetches data correctly', () async {
      final notifier = container.read(aiAgentListProvider.notifier);
      final agentData = [
        {
          'id': 1,
          'name': 'Agent 1',
          'title': 'My Agent',
          'model': 'gpt-4',
          'temperature': 0.7,
          'system_prompt': 'You are a helper',
          'status': 'Active',
          'knowledge_db_ids': [1, 2],
        },
      ];
      mockClient.setMockResponse(agentData);

      await notifier.loadAgents();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'Agent 1');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/ai_agents');
    });

    test('createAgent sends correct parameters', () async {
      final notifier = container.read(aiAgentListProvider.notifier);
      final newAgent = AIAgent(
        name: 'New Agent',
        title: 'New Title',
        model: 'gpt-3.5-turbo',
        knowledge_db_ids: [],
      );

      mockClient.setMockResponse(newAgent.toJson());

      await notifier.createAgent(newAgent);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/ai_agents');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'New Agent');
      expect(body['model'], 'gpt-3.5-turbo');
    });

    test('updateAgent sends correct data', () async {
      final notifier = container.read(aiAgentListProvider.notifier);
      final agentToUpdate = AIAgent(
        id: 10,
        name: 'Updated Agent',
        title: 'Title',
        knowledge_db_ids: [5],
      );

      mockClient.setMockResponse(agentToUpdate.toJson());

      await notifier.updateAgent(agentToUpdate);

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/ai_agents/10');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'Updated Agent');
      expect(body['knowledge_db_ids'], [5]);
    });

    test('deleteAgent calls correct endpoint', () async {
      final notifier = container.read(aiAgentListProvider.notifier);

      await notifier.deleteAgent(22);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/ai_agents/22');
    });
  });
}
