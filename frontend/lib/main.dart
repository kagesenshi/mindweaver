import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

import 'widgets/main_layout.dart';
import 'pages/login_page.dart';
import 'pages/projects_page.dart';
import 'pages/project_overview_page.dart';
import 'pages/knowledge_db_page.dart';
import 'pages/ai_agents_page.dart';
import 'pages/chat_page.dart';
import 'pages/ontology_page.dart';
import 'pages/data_sources_page.dart';
import 'pages/s3_storage_page.dart';
import 'pages/ingestion_page.dart';
import 'pages/k8s_clusters_page.dart';
import 'pages/platform/pgsql_page.dart';
import 'pages/callback_page.dart';
import 'providers/auth_provider.dart';

void main() {
  usePathUrlStrategy();
  runApp(const ProviderScope(child: MindweaverApp()));
}

final _routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isLoggedIn = authState.value != null;
      final isLoggingIn = state.uri.path == '/login';
      final isCallback = state.uri.path == '/callback';

      // Allow /login and /auth/callback
      if (isLoggingIn || isCallback) {
        return null;
      }

      if (!isLoggedIn) {
        return '/login';
      }

      return null;
    },
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
            path: '/ontology',
            builder: (context, state) => const OntologyPage(),
          ),
          GoRoute(
            path: '/sources',
            builder: (context, state) => const DataSourcesPage(),
          ),
          GoRoute(
            path: '/s3_storage',
            builder: (context, state) => const S3StoragePage(),
          ),
          GoRoute(
            path: '/ingestion',
            builder: (context, state) => const IngestionPage(),
          ),
          GoRoute(
            path: '/k8s_clusters',
            builder: (context, state) => const K8sClustersPage(),
          ),
          GoRoute(
            path: '/platform/pgsql',
            builder: (context, state) => const PgSqlPage(),
          ),
        ],
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) {
          final error = state.uri.queryParameters['error'];
          return LoginPage(error: error);
        },
      ),
      GoRoute(
        path: '/callback',
        builder: (context, state) {
          final code = state.uri.queryParameters['code'];
          final stateParam = state.uri.queryParameters['state'];
          final error = state.uri.queryParameters['error'];
          return CallbackPage(code: code, state: stateParam, error: error);
        },
      ),
    ],
  );
});

class MindweaverApp extends ConsumerWidget {
  const MindweaverApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(_routerProvider);

    return MaterialApp.router(
      title: 'Mindweaver',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1A73E8)),
        useMaterial3: true,
        textTheme: GoogleFonts.interTextTheme(),
      ),
      routerConfig: router,
    );
  }
}
