import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'widgets/main_layout.dart';
import 'pages/projects_page.dart';
import 'pages/project_overview_page.dart';
import 'pages/knowledge_db_page.dart';
import 'pages/ai_agents_page.dart';
import 'pages/chat_page.dart';
import 'pages/data_sources_page.dart';
import 'pages/lakehouse_storage_page.dart';
import 'pages/ingestion_page.dart';
import 'pages/ontology_page.dart';

void main() {
  runApp(const ProviderScope(child: MindweaverApp()));
}

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        return MainLayout(child: child);
      },
      routes: [
        GoRoute(path: '/', builder: (context, state) => const ProjectsPage()),
        GoRoute(
          path: '/overview',
          builder: (context, state) => const ProjectOverviewPage(),
        ),
        GoRoute(
          path: '/knowledge_db',
          builder: (context, state) => const KnowledgeDbPage(),
        ),
        GoRoute(
          path: '/agents',
          builder: (context, state) => const AiAgentsPage(),
        ),
        GoRoute(path: '/chat', builder: (context, state) => const ChatPage()),
        GoRoute(
          path: '/sources',
          builder: (context, state) => const DataSourcesPage(),
        ),
        GoRoute(
          path: '/lakehouse',
          builder: (context, state) => const LakehouseStoragePage(),
        ),
        GoRoute(
          path: '/ingestion',
          builder: (context, state) => const IngestionPage(),
        ),
        GoRoute(
          path: '/ontology',
          builder: (context, state) => const OntologyPage(),
        ),
      ],
    ),
  ],
);

class MindweaverApp extends StatelessWidget {
  const MindweaverApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Mindweaver',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
        textTheme: const TextTheme(
          displayLarge: TextStyle(fontSize: 55),
          displayMedium: TextStyle(fontSize: 43),
          displaySmall: TextStyle(fontSize: 34),
          headlineLarge: TextStyle(fontSize: 30),
          headlineMedium: TextStyle(fontSize: 26),
          headlineSmall: TextStyle(fontSize: 22),
          titleLarge: TextStyle(fontSize: 20),
          titleMedium: TextStyle(fontSize: 14),
          titleSmall: TextStyle(fontSize: 12),
          bodyLarge: TextStyle(fontSize: 14),
          bodyMedium: TextStyle(fontSize: 12),
          bodySmall: TextStyle(fontSize: 10),
          labelLarge: TextStyle(fontSize: 12),
          labelMedium: TextStyle(fontSize: 10),
          labelSmall: TextStyle(fontSize: 9),
        ),
      ),
      routerConfig: _router,
    );
  }
}
