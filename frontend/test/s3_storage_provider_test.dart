import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/s3_storage.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/s3_storage_provider.dart';
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

  group('S3StorageListNotifier', () {
    test('loadStorages fetches data correctly', () async {
      final notifier = container.read(s3StorageListProvider.notifier);
      final storageData = <Map<String, dynamic>>[
        {
          'id': 1,
          'name': 'S3 Storage',
          'title': 'My S3',
          'bucket': 'my-bucket',
          'region': 'us-east-1',
          'access_key': 'AKIA...',
          'parameters': <String, dynamic>{},
        },
      ];
      mockClient.setMockResponse(storageData);

      await notifier.loadStorages();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'S3 Storage');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/s3_storages');
    });

    test('createStorage sends correct parameters', () async {
      final notifier = container.read(s3StorageListProvider.notifier);
      final newStorage = S3Storage(
        name: 'New S3',
        title: 'New Storage',
        bucket: 'new-bucket',
        region: 'us-east-1',
        access_key: 'xyz',
        parameters: {},
      );

      mockClient.setMockResponse(newStorage.toJson());

      await notifier.createStorage(newStorage);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/s3_storages');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'New S3');
      expect(body['bucket'], 'new-bucket');
    });

    test('updateStorage sends correct data', () async {
      final notifier = container.read(s3StorageListProvider.notifier);
      final storageToUpdate = S3Storage(
        id: 11,
        name: 'Updated Storage',
        title: 'Title',
        bucket: 'updated',
        region: 'us-east-1',
        access_key: 'xyz',
        parameters: {},
      );

      mockClient.setMockResponse(storageToUpdate.toJson());

      await notifier.updateStorage(storageToUpdate);

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/s3_storages/11');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'Updated Storage');
    });

    test('deleteStorage calls correct endpoint', () async {
      final notifier = container.read(s3StorageListProvider.notifier);

      await notifier.deleteStorage(88);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/s3_storages/88');
    });

    test('testConnection sends correct parameters', () async {
      final notifier = container.read(s3StorageListProvider.notifier);
      final params = {'bucket': 'test'};

      mockClient.setMockResponse({'status': 'connected'});

      final result = await notifier.testConnection(params);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/s3_storages/test_connection');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['bucket'], 'test');
      expect(result['status'], 'connected');
    });
  });
}
