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
import 'pages/login_page.dart';
import 'providers/auth_provider.dart';

void main() {
  runApp(const ProviderScope(child: MindweaverApp()));
}

final _routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final loggingIn = state.matchedLocation == '/login';
      final authSuccess = state.matchedLocation == '/auth/success';

      if (authState.status == AuthStatus.loading) return null;

      if (authState.status == AuthStatus.unauthenticated &&
          !loggingIn &&
          !authSuccess) {
        return '/login';
      }

      if (authState.status == AuthStatus.authenticated &&
          (loggingIn || authSuccess)) {
        return '/';
      }

      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
      GoRoute(
        path: '/auth/success',
        builder: (context, state) {
          final token = state.uri.queryParameters['token'];
          if (token != null) {
            // We need to trigger the login in the provider
            // Since this is a builder, we can't do it directly.
            // We use a Future.delayed or similar, but better is a separate widget or a hook.
            return _AuthSuccessHandler(token: token);
          }
          return const LoginPage();
        },
      ),
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
});

class _AuthSuccessHandler extends ConsumerStatefulWidget {
  final String token;
  const _AuthSuccessHandler({required this.token});

  @override
  ConsumerState<_AuthSuccessHandler> createState() =>
      _AuthSuccessHandlerState();
}

class _AuthSuccessHandlerState extends ConsumerState<_AuthSuccessHandler> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.read(authProvider.notifier).login(widget.token);
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}

class MindweaverApp extends ConsumerWidget {
  const MindweaverApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
      routerConfig: ref.watch(_routerProvider),
    );
  }
}
