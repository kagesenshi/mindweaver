import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/project.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import 'package:mindweaver_flutter/providers/project_provider.dart';
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

  group('ProjectListNotifier', () {
    test('loadProjects fetches data correctly', () async {
      final notifier = container.read(projectListProvider.notifier);
      final projectData = [
        {
          'id': 1,
          'name': 'Project 1',
          'title': 'My Project',
          'description': 'Desc',
        },
      ];
      mockClient.setMockResponse(projectData);

      await notifier.loadProjects();

      expect(notifier.state.hasValue, true);
      expect(notifier.state.value!.length, 1);
      expect(notifier.state.value!.first.name, 'Project 1');
      expect(mockClient.lastMethod, 'GET_LIST');
      expect(mockClient.lastEndpoint, '/api/v1/projects');
    });

    test('createProject sends correct parameters', () async {
      final notifier = container.read(projectListProvider.notifier);

      final createdProject = Project(
        name: 'new-project',
        title: 'New Project',
        description: 'Desc',
      );
      mockClient.setMockResponse(createdProject.toJson());

      await notifier.createProject('new-project', 'New Project', 'Desc');

      expect(mockClient.lastMethod, 'POST');
      expect(mockClient.lastEndpoint, '/api/v1/projects');
      expect(mockClient.lastBody, isA<Map>());
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['name'], 'new-project');
      expect(body['title'], 'New Project');
      expect(body['description'], 'Desc');
    });

    test('updateProject sends correct data', () async {
      final notifier = container.read(projectListProvider.notifier);
      final projectResponse = Project(
        id: 5,
        name: 'project-5',
        title: 'Updated Title',
        description: 'Updated Desc',
      );

      mockClient.setMockResponse(projectResponse.toJson());

      await notifier.updateProject(5, 'Updated Title', 'Updated Desc');

      expect(mockClient.lastMethod, 'PUT');
      expect(mockClient.lastEndpoint, '/api/v1/projects/5');
      final body = mockClient.lastBody as Map<String, dynamic>;
      expect(body['title'], 'Updated Title');
      expect(body['description'], 'Updated Desc');
    });

    test('deleteProject calls correct endpoint', () async {
      final notifier = container.read(projectListProvider.notifier);

      await notifier.deleteProject(88);

      expect(mockClient.lastMethod, 'DELETE');
      expect(mockClient.lastEndpoint, '/api/v1/projects/88');
    });
  });

  group('CurrentProjectNotifier', () {
    test('sets and clears project', () {
      final notifier = container.read(currentProjectProvider.notifier);
      final p = Project(name: 'p1', title: 'P1');

      notifier.setProject(p);
      expect(notifier.state, p);

      notifier.clearProject();
      expect(notifier.state, null);
    });
  });
}
