import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/project.dart';
import 'api_providers.dart';

class CurrentProjectNotifier extends StateNotifier<Project?> {
  CurrentProjectNotifier() : super(null);

  void setProject(Project project) {
    state = project;
  }

  void clearProject() {
    state = null;
  }
}

final currentProjectProvider =
    StateNotifierProvider<CurrentProjectNotifier, Project?>((ref) {
      return CurrentProjectNotifier();
    });

class ProjectListNotifier extends StateNotifier<AsyncValue<List<Project>>> {
  final Ref ref;

  ProjectListNotifier(this.ref) : super(const AsyncValue.loading()) {
    loadProjects();
  }

  Future<void> loadProjects() async {
    state = const AsyncValue.loading();
    try {
      final client = ref.read(apiClientProvider);
      final response = await client.listAll(
        '/api/v1/projects',
        (json) => Project.fromJson(json as Map<String, dynamic>),
      );
      state = AsyncValue.data(response);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> createProject(
    String name,
    String title,
    String description,
  ) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.post('/api/v1/projects', {
        'name': name,
        'title': title,
        'description': description,
      }, (json) => Project.fromJson(json as Map<String, dynamic>));
      await loadProjects();
    } catch (e) {
      rethrow;
    }
  }
}

final projectListProvider =
    StateNotifierProvider<ProjectListNotifier, AsyncValue<List<Project>>>((
      ref,
    ) {
      return ProjectListNotifier(ref);
    });
