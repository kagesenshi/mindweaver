import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/knowledge_db.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/knowledge_db_provider.dart';
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

  group('KnowledgeDBListNotifier', () {
    test('loadDBs fetches data correctly', () async {
      final notifier = container.read(knowledgeDBListProvider.notifier);
      final dbData = [
        {
          'id': 1,
          'name': 'KDB 1',
          'title': 'Knowledge DB',
          'type': 'knowledge-graph',
          'parameters': <String, dynamic>{},
          'description': 'Test DB',
        },
      ];
      mockClient.setMockResponse(dbData);

      await notifier.loadDBs();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'KDB 1');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/knowledge_dbs');
    });

    test('createDB sends correct parameters including ontology_id', () async {
      final notifier = container.read(knowledgeDBListProvider.notifier);
      final newDB = KnowledgeDB(
        name: 'New KDB',
        title: 'New KDB Title',
        type: 'passage-graph',
        parameters: {'graph_type': 'simple'},
        description: 'Desc',
        ontology_id: 10,
      );

      mockClient.setMockResponse(newDB.toJson());

      await notifier.createDB(newDB);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/knowledge_dbs');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'New KDB');
      expect(body['type'], 'passage-graph');
      expect(body['ontology_id'], 10);
    });

    test('updateDB sends correct data', () async {
      final notifier = container.read(knowledgeDBListProvider.notifier);
      final dbToUpdate = KnowledgeDB(
        id: 55,
        name: 'Updated KDB',
        title: 'Title',
        type: 'tree-graph',
        parameters: {},
        description: 'New Desc',
      );

      mockClient.setMockResponse(dbToUpdate.toJson());

      await notifier.updateDB(dbToUpdate);

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/knowledge_dbs/55');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'Updated KDB');
      expect(body['description'], 'New Desc');
    });

    test('deleteDB calls correct endpoint', () async {
      final notifier = container.read(knowledgeDBListProvider.notifier);

      await notifier.deleteDB(77);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/knowledge_dbs/77');
    });
  });
}
