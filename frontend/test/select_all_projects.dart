import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mindweaver_flutter/models/project.dart';
import 'package:mindweaver_flutter/providers/project_provider.dart';
import 'package:mindweaver_flutter/widgets/main_layout.dart';
import 'package:go_router/go_router.dart';

void main() {
  testWidgets('Selecting All Projects should clear the current project', (
    WidgetTester tester,
  ) async {
    final project = Project(id: 1, name: 'test-project', title: 'Test Project');

    final container = ProviderContainer(
      overrides: [
        projectListProvider.overrideWith((ref) {
          return ProjectListNotifierMock(ref, [project]);
        }),
      ],
    );

    // Set initial project
    container.read(currentProjectProvider.notifier).setProject(project);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp.router(
          routerConfig: GoRouter(
            routes: [
              GoRoute(
                path: '/',
                builder: (context, state) =>
                    const MainLayout(child: SizedBox()),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify initial state: dropdown shows the project title
    expect(find.text('Test Project'), findsOneWidget);

    // Open the dropdown by clicking the project title
    await tester.tap(find.text('Test Project'));
    await tester.pumpAndSettle();

    // Tap "All Projects" - specifically find the one in the PopupMenuItem
    final allProjectsItem = find.descendant(
      of: find.byType(PopupMenuItem<int?>),
      matching: find.text('All Projects'),
    );
    expect(allProjectsItem, findsOneWidget);
    await tester.tap(allProjectsItem);
    await tester.pumpAndSettle();

    // Verify that currentProjectProvider is null
    expect(container.read(currentProjectProvider), null);

    // Verify that the dropdown label has changed back to "All Projects"
    expect(find.text('All Projects'), findsOneWidget);
  });

  testWidgets('Selecting a specific project should set the current project', (
    WidgetTester tester,
  ) async {
    final project = Project(id: 1, name: 'test-project', title: 'Test Project');

    final container = ProviderContainer(
      overrides: [
        projectListProvider.overrideWith((ref) {
          return ProjectListNotifierMock(ref, [project]);
        }),
      ],
    );

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp.router(
          routerConfig: GoRouter(
            routes: [
              GoRoute(
                path: '/',
                builder: (context, state) =>
                    const MainLayout(child: SizedBox()),
              ),
            ],
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Initially should show "All Projects"
    expect(find.text('All Projects'), findsOneWidget);

    // Open dropdown
    await tester.tap(find.text('All Projects'));
    await tester.pumpAndSettle();

    // Tap "Test Project"
    final specificProjectItem = find.descendant(
      of: find.byType(PopupMenuItem<int?>),
      matching: find.text('Test Project'),
    );
    expect(specificProjectItem, findsOneWidget);
    await tester.tap(specificProjectItem);
    await tester.pumpAndSettle();

    // Verify current project is set
    expect(container.read(currentProjectProvider)?.id, 1);
    expect(find.text('Test Project'), findsOneWidget);
  });
}

class ProjectListNotifierMock extends ProjectListNotifier {
  final List<Project> projects;
  ProjectListNotifierMock(Ref ref, this.projects) : super(ref);

  @override
  Future<void> loadProjects() async {
    state = AsyncValue.data(projects);
  }
}
