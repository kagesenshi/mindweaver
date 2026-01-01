import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/data_source.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/data_source_provider.dart';
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

  group('DataSourceListNotifier', () {
    test('loadSources fetches data correctly', () async {
      final notifier = container.read(dataSourceListProvider.notifier);
      final sourcesData = [
        {
          'id': 1,
          'name': 'API Source',
          'title': 'My API',
          'type': 'API',
          'parameters': {'base_url': 'http://test.com', 'api_key': '123'},
        },
      ];
      mockClient.setMockResponse(sourcesData);

      await notifier.loadSources();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'API Source');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/data_sources');
    });

    test('createSource sends correct API parameters', () async {
      final notifier = container.read(dataSourceListProvider.notifier);
      final newSource = DataSource(
        name: 'New API',
        title: 'New API Title',
        type: 'API',
        parameters: {'base_url': 'http://new.com', 'api_key': 'abc'},
      );

      // Mock response for the create call (returns the created object)
      mockClient.setMockResponse(newSource.toJson());

      await notifier.createSource(newSource);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/data_sources');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'New API');
      expect(body['type'], 'API');
      expect(body['parameters']['base_url'], 'http://new.com');
    });

    test('createSource sends correct Database parameters', () async {
      final notifier = container.read(dataSourceListProvider.notifier);
      final dbSource = DataSource(
        name: 'DB Source',
        title: 'My DB',
        type: 'Database',
        parameters: {
          'host': 'localhost',
          'port': 5432,
          'username': 'usr',
          'password': 'pwd',
          'database_type': 'postgresql',
        },
      );

      mockClient.setMockResponse(dbSource.toJson());

      await notifier.createSource(dbSource);

      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['type'], 'Database');
      expect(body['parameters']['host'], 'localhost');
      expect(body['parameters']['port'], 5432);
    });

    test('updateSource sends correct data', () async {
      final notifier = container.read(dataSourceListProvider.notifier);
      final sourceToUpdate = DataSource(
        id: 123,
        name: 'Updated Name',
        title: 'Title',
        type: 'API',
        parameters: {},
      );

      mockClient.setMockResponse(sourceToUpdate.toJson());

      await notifier.updateSource(sourceToUpdate);

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/data_sources/123');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'Updated Name');
    });

    test('deleteSource calls correct endpoint', () async {
      final notifier = container.read(dataSourceListProvider.notifier);

      await notifier.deleteSource(99);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/data_sources/99');
    });

    test('testConnection sends correct parameters', () async {
      final notifier = container.read(dataSourceListProvider.notifier);
      final params = {'base_url': 'http://test.com'};

      mockClient.setMockResponse({'status': 'success'});

      final result = await notifier.testConnection('API', params);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/data_sources/test_connection');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['type'], 'API');
      expect(body['parameters'], params);
      expect(result['status'], 'success');
    });
  });
}
