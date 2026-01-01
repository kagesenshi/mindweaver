import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/ontology.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/ontology_provider.dart';
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

  group('OntologyListNotifier', () {
    test('loadOntologies fetches data correctly', () async {
      final notifier = container.read(ontologyListProvider.notifier);
      final ontologyData = [
        {
          'id': 1,
          'name': 'Ontology 1',
          'title': 'My Ontology',
          'description': 'Desc',
          'entity_types': [],
          'relationship_types': [],
        },
      ];
      mockClient.setMockResponse(ontologyData);

      await notifier.loadOntologies();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'Ontology 1');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/ontologies');
    });

    test('createOntology sends correct parameters', () async {
      final notifier = container.read(ontologyListProvider.notifier);
      final newOntology = Ontology(
        name: 'New Ontology',
        title: 'New Title',
        description: 'Description',
        entity_types: [
          EntityType(
            name: 'Person',
            attributes: [EntityAttribute(name: 'name')],
          ),
        ],
        relationship_types: [],
      );

      mockClient.setMockResponse(jsonDecode(jsonEncode(newOntology.toJson())));

      await notifier.createOntology(newOntology);

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/ontologies');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'New Ontology');
      expect(body['entity_types'].length, 1);
      final entityType = body['entity_types'][0] as EntityType;
      expect(entityType.name, 'Person');
    });

    test('updateOntology sends correct data', () async {
      final notifier = container.read(ontologyListProvider.notifier);
      final ontologyToUpdate = Ontology(
        id: 77,
        name: 'Updated Ontology',
        title: 'Title',
        description: 'New Desc',
      );

      mockClient.setMockResponse(ontologyToUpdate.toJson());

      await notifier.updateOntology(ontologyToUpdate);

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/ontologies/77');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'Updated Ontology');
    });

    test('deleteOntology calls correct endpoint', () async {
      final notifier = container.read(ontologyListProvider.notifier);

      await notifier.deleteOntology(100);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/ontologies/100');
    });
  });
}
