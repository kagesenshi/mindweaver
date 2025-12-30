import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

class MainLayout extends StatelessWidget {
  final Widget child;

  const MainLayout({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final router = GoRouter.of(context);
    final currentPath = router.routerDelegate.currentConfiguration.fullPath;

    return Scaffold(
      body: Row(
        children: [
          _Sidebar(currentPath: currentPath),
          Expanded(child: child),
        ],
      ),
    );
  }
}

class _Sidebar extends StatelessWidget {
  final String? currentPath;

  const _Sidebar({this.currentPath});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 250,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Theme.of(context).colorScheme.primary.withOpacity(0.9),
            Theme.of(context).colorScheme.primaryContainer,
          ],
        ),
      ),
      child: Column(
        children: [
          const SizedBox(height: 40),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                const FaIcon(
                  FontAwesomeIcons.brain,
                  color: Colors.white,
                  size: 30,
                ),
                const SizedBox(width: 15),
                Text(
                  'Mindweaver',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 40),
          _SidebarItem(
            icon: FontAwesomeIcons.folder,
            label: 'Projects',
            path: '/',
            isCurrent: currentPath == '/',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.chartLine,
            label: 'Overview',
            path: '/overview',
            isCurrent: currentPath == '/overview',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.database,
            label: 'Knowledge DB',
            path: '/knowledge_db',
            isCurrent: currentPath == '/knowledge_db',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.robot,
            label: 'AI Agents',
            path: '/agents',
            isCurrent: currentPath == '/agents',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.message,
            label: 'Chat',
            path: '/chat',
            isCurrent: currentPath == '/chat',
          ),
          const Divider(color: Colors.white24, height: 40),
          _SidebarItem(
            icon: FontAwesomeIcons.plug,
            label: 'Sources',
            path: '/sources',
            isCurrent: currentPath == '/sources',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.server,
            label: 'Lakehouse',
            path: '/lakehouse',
            isCurrent: currentPath == '/lakehouse',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.upload,
            label: 'Ingestion',
            path: '/ingestion',
            isCurrent: currentPath == '/ingestion',
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.diagramProject,
            label: 'Ontology',
            path: '/ontology',
            isCurrent: currentPath == '/ontology',
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Text(
              'v1.0.0',
              style: TextStyle(color: Colors.white.withOpacity(0.5)),
            ),
          ),
        ],
      ),
    );
  }
}

class _SidebarItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String path;
  final bool isCurrent;

  const _SidebarItem({
    required this.icon,
    required this.label,
    required this.path,
    required this.isCurrent,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      child: InkWell(
        onTap: () => context.go(path),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
          decoration: BoxDecoration(
            color: isCurrent
                ? Colors.white.withOpacity(0.2)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              FaIcon(icon, color: Colors.white, size: 20),
              const SizedBox(width: 15),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
