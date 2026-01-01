import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/ingestion.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/ingestion_provider.dart';
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

  group('IngestionListNotifier', () {
    test('loadIngestions fetches data correctly', () async {
      final notifier = container.read(ingestionListProvider.notifier);
      final ingestionData = [
        {
          'id': 1,
          'name': 'Ingest 1',
          'title': 'My Ingestion',
          'data_source_id': 1,
          'lakehouse_storage_id': 2,
          'storage_path': '/path',
          'cron_schedule': '0 0 * * *',
          'ingestion_type': 'full',
          'config': <String, dynamic>{},
        },
      ];
      mockClient.setMockResponse(ingestionData);

      await notifier.loadIngestions();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'Ingest 1');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/ingestions');
    });

    test('createIngestion sends correct parameters', () async {
      final notifier = container.read(ingestionListProvider.notifier);
      final newIngestion = Ingestion(
        name: 'New Ingest',
        title: 'New Title',
        data_source_id: 10,
        lakehouse_storage_id: 20,
        storage_path: 's3://bucket/path',
        cron_schedule: '@daily',
        ingestion_type: 'incremental',
        config: {'limit': 100},
      );

      mockClient.setMockResponse(newIngestion.toJson());

      await notifier.createIngestion(newIngestion);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/ingestions');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'New Ingest');
      expect(body['cron_schedule'], '@daily');
      expect(body['data_source_id'], 10);
      expect(body['lakehouse_storage_id'], 20);
    });

    test('updateIngestion sends correct data', () async {
      final notifier = container.read(ingestionListProvider.notifier);
      final ingestionToUpdate = Ingestion(
        id: 5,
        name: 'Updated Ingest',
        title: 'Title',
        data_source_id: 1,
        lakehouse_storage_id: 2,
        storage_path: '/new/path',
        cron_schedule: '@hourly',
        ingestion_type: 'full',
        config: {},
      );

      mockClient.setMockResponse(ingestionToUpdate.toJson());

      await notifier.updateIngestion(ingestionToUpdate);

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/ingestions/5');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['storage_path'], '/new/path');
    });

    test('deleteIngestion calls correct endpoint', () async {
      final notifier = container.read(ingestionListProvider.notifier);

      await notifier.deleteIngestion(99);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/ingestions/99');
    });

    test('executeIngestion calls correct endpoint', () async {
      final notifier = container.read(ingestionListProvider.notifier);

      mockClient.setMockResponse({'status': 'triggered'});

      await notifier.executeIngestion(42);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/ingestions/42/execute');
    });

    test('getRuns fetches correct endpoint', () async {
      final notifier = container.read(ingestionListProvider.notifier);
      final runData = [
        {
          'id': 101,
          'ingestion_id': 1,
          'status': 'completed',
          'records_processed': 500,
        },
      ];
      mockClient.setMockResponse(runData);

      final runs = await notifier.getRuns(1);

      expect(runs.length, 1);
      expect(runs.first.status, 'completed');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/ingestions/1/runs');
    });
  });
}
