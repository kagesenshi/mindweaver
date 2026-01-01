import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/project_provider.dart';
import '../models/project.dart';
import '../providers/feature_flags_provider.dart';

class MainLayout extends StatefulWidget {
  final Widget child;

  const MainLayout({super.key, required this.child});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  final ScrollController _horizontalController = ScrollController();

  @override
  void dispose() {
    _horizontalController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final router = GoRouter.of(context);
    final currentPath = router.routerDelegate.currentConfiguration.fullPath;
    final screenWidth = MediaQuery.of(context).size.width;
    const minWidth = 1024.0;

    return Scaffold(
      body: Scrollbar(
        controller: _horizontalController,
        thumbVisibility: true,
        child: SingleChildScrollView(
          controller: _horizontalController,
          scrollDirection: Axis.horizontal,
          child: ConstrainedBox(
            constraints: BoxConstraints(
              minWidth: minWidth,
              maxWidth: screenWidth > minWidth ? screenWidth : minWidth,
              minHeight: MediaQuery.of(context).size.height,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _Sidebar(currentPath: currentPath),
                Expanded(
                  child: Column(
                    children: [
                      const _TopBar(),
                      Expanded(child: widget.child),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Sidebar extends StatefulWidget {
  final String? currentPath;

  const _Sidebar({this.currentPath});

  @override
  State<_Sidebar> createState() => _SidebarState();
}

class _SidebarState extends State<_Sidebar> {
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 250,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Theme.of(context).colorScheme.primary,
            Theme.of(context).colorScheme.primary.withOpacity(0.8),
          ],
        ),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Scrollbar(
            controller: _scrollController,
            thumbVisibility: true,
            child: SingleChildScrollView(
              controller: _scrollController,
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: IntrinsicHeight(
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
                            Expanded(
                              child: Text(
                                'Mindweaver',
                                style: Theme.of(context).textTheme.headlineSmall
                                    ?.copyWith(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                    ),
                                overflow: TextOverflow.ellipsis,
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
                        isCurrent: widget.currentPath == '/',
                      ),
                      const Divider(color: Colors.white24, height: 40),
                      _SidebarItem(
                        icon: FontAwesomeIcons.chartLine,
                        label: 'Overview',
                        path: '/overview',
                        isCurrent: widget.currentPath == '/overview',
                      ),
                      const Divider(color: Colors.white24, height: 40),
                      Consumer(
                        builder: (context, ref, child) {
                          final featureFlags = ref.watch(featureFlagsProvider);
                          final showKnowledge = featureFlags.when(
                            data: (f) => f.experimentalKnowledgeDb,
                            loading: () => true,
                            error: (_, __) => true,
                          );

                          if (!showKnowledge) return const SizedBox.shrink();

                          return _SidebarGroup(
                            icon: FontAwesomeIcons.lightbulb,
                            label: 'Knowledge & AI',
                            currentPath: widget.currentPath,
                            items: [
                              _SidebarItem(
                                icon: FontAwesomeIcons.book,
                                label: 'Knowledge DB',
                                path: '/knowledge_db',
                                isCurrent:
                                    widget.currentPath == '/knowledge_db',
                              ),
                              _SidebarItem(
                                icon: FontAwesomeIcons.robot,
                                label: 'AI Agents',
                                path: '/agents',
                                isCurrent: widget.currentPath == '/agents',
                              ),
                              _SidebarItem(
                                icon: FontAwesomeIcons.message,
                                label: 'Chat',
                                path: '/chat',
                                isCurrent: widget.currentPath == '/chat',
                              ),
                              _SidebarItem(
                                icon: FontAwesomeIcons.diagramProject,
                                label: 'Ontology',
                                path: '/ontology',
                                isCurrent: widget.currentPath == '/ontology',
                              ),
                            ],
                          );
                        },
                      ),
                      _SidebarGroup(
                        icon: FontAwesomeIcons.networkWired,
                        label: 'Connections',
                        currentPath: widget.currentPath,
                        items: [
                          _SidebarItem(
                            icon: FontAwesomeIcons.plug,
                            label: 'Sources',
                            path: '/sources',
                            isCurrent: widget.currentPath == '/sources',
                          ),
                          _SidebarItem(
                            icon: FontAwesomeIcons.server,
                            label: 'Lakehouse',
                            path: '/lakehouse',
                            isCurrent: widget.currentPath == '/lakehouse',
                          ),
                          _SidebarItem(
                            icon: FontAwesomeIcons.upload,
                            label: 'Ingestion',
                            path: '/ingestion',
                            isCurrent: widget.currentPath == '/ingestion',
                          ),
                        ],
                      ),
                      const Spacer(),
                      Padding(
                        padding: const EdgeInsets.all(20),
                        child: Text(
                          'v1.0.0',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.5),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
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
                  fontSize: 14,
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

class _SidebarGroup extends StatefulWidget {
  final IconData icon;
  final String label;
  final String? currentPath;
  final List<_SidebarItem> items;

  const _SidebarGroup({
    required this.icon,
    required this.label,
    this.currentPath,
    required this.items,
  });

  @override
  State<_SidebarGroup> createState() => _SidebarGroupState();
}

class _SidebarGroupState extends State<_SidebarGroup> {
  late bool _isExpanded;

  @override
  void initState() {
    super.initState();
    _isExpanded = widget.items.any((item) => item.isCurrent);
  }

  @override
  void didUpdateWidget(_SidebarGroup oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.items.any((item) => item.isCurrent)) {
      _isExpanded = true;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          child: InkWell(
            onTap: () {
              setState(() {
                _isExpanded = !_isExpanded;
              });
            },
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
              child: Row(
                children: [
                  FaIcon(widget.icon, color: Colors.white, size: 20),
                  const SizedBox(width: 15),
                  Expanded(
                    child: Text(
                      widget.label,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  FaIcon(
                    _isExpanded
                        ? FontAwesomeIcons.chevronDown
                        : FontAwesomeIcons.chevronRight,
                    color: Colors.white,
                    size: 14,
                  ),
                ],
              ),
            ),
          ),
        ),
        if (_isExpanded)
          ...widget.items.map((item) {
            return Padding(
              padding: const EdgeInsets.only(left: 20),
              child: item,
            );
          }).toList(),
      ],
    );
  }
}

class _TopBar extends ConsumerWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      height: 70,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor.withOpacity(0.1),
          ),
        ),
      ),
      child: Row(
        children: [
          const Spacer(),
          // Project Selection Dropdown
          Consumer(
            builder: (context, ref, child) {
              final currentProject = ref.watch(currentProjectProvider);
              final projectsAsync = ref.watch(projectListProvider);

              return PopupMenuButton<Project?>(
                offset: const Offset(0, 50),
                onSelected: (project) {
                  if (project == null) {
                    ref.read(currentProjectProvider.notifier).clearProject();
                  } else {
                    ref
                        .read(currentProjectProvider.notifier)
                        .setProject(project);
                  }
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: Theme.of(
                      context,
                    ).colorScheme.primaryContainer.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.folder_shared_outlined,
                        size: 18,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        currentProject?.title ?? 'All Projects',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.primary,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(
                        Icons.keyboard_arrow_down,
                        size: 18,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ],
                  ),
                ),
                itemBuilder: (context) {
                  final List<PopupMenuEntry<Project?>> items = [
                    const PopupMenuItem<Project?>(
                      value: null,
                      child: Row(
                        children: [
                          Icon(Icons.all_inclusive, size: 20),
                          SizedBox(width: 10),
                          Text('All Projects'),
                        ],
                      ),
                    ),
                    const PopupMenuDivider(),
                  ];

                  projectsAsync.whenData((projects) {
                    items.addAll(
                      projects.map(
                        (project) => PopupMenuItem<Project?>(
                          value: project,
                          child: Row(
                            children: [
                              const Icon(
                                Icons.folder_shared_outlined,
                                size: 20,
                              ),
                              const SizedBox(width: 10),
                              Text(project.title),
                            ],
                          ),
                        ),
                      ),
                    );
                  });

                  return items;
                },
              );
            },
          ),
          const SizedBox(width: 16),
          // Notifications
          PopupMenuButton<String>(
            offset: const Offset(0, 50),
            icon: Badge(
              label: const Text('3'),
              child: Icon(
                Icons.notifications_none_rounded,
                color: Theme.of(context).colorScheme.onSurface,
              ),
            ),
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'notification1',
                child: Text('You have a new message'),
              ),
              const PopupMenuItem(
                value: 'notification2',
                child: Text('Project updated'),
              ),
            ],
          ),
          const SizedBox(width: 16),
          // User Profile
          PopupMenuButton<String>(
            offset: const Offset(0, 50),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: Theme.of(
                    context,
                  ).colorScheme.primary.withOpacity(0.1),
                  child: Text(
                    'JD',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  'John Doe',
                  style: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
                ),
                const Icon(Icons.keyboard_arrow_down, size: 20),
              ],
            ),
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'profile',
                onTap: () {
                  // Navigate to profile
                },
                child: const Row(
                  children: [
                    Icon(Icons.person_outline, size: 20),
                    SizedBox(width: 10),
                    Text('Profile'),
                  ],
                ),
              ),
              PopupMenuItem(
                value: 'settings',
                child: const Row(
                  children: [
                    Icon(Icons.settings_outlined, size: 20),
                    SizedBox(width: 10),
                    Text('Settings'),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              PopupMenuItem(
                value: 'logout',
                onTap: () {
                  // Add logout logic here
                },
                child: Row(
                  children: [
                    Icon(
                      Icons.logout,
                      size: 20,
                      color: Theme.of(context).colorScheme.error,
                    ),
                    const SizedBox(width: 10),
                    const Text('Logout'),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
