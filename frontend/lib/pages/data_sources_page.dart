import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/data_source_provider.dart';
import '../providers/project_provider.dart';
import '../models/data_source.dart';
import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';

class DataSourcesPage extends ConsumerWidget {
  const DataSourcesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sourcesAsync = ref.watch(dataSourceListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Data Sources'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(dataSourceListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: sourcesAsync.when(
        data: (sources) => _SourcesList(sources: sources),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateSourceDialog(context, ref),
        label: const Text('New Source'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateSourceDialog(BuildContext context, WidgetRef ref) {
    String selectedType = 'API';
    final nameController = TextEditingController();
    final titleController = TextEditingController();

    // API specific
    final baseUrlController = TextEditingController();
    final apiKeyController = TextEditingController();

    // DB specific
    final hostController = TextEditingController();
    final portController = TextEditingController(text: '5432');
    final userController = TextEditingController();
    final passController = TextEditingController();
    final dbNameController = TextEditingController();
    String dbType = 'postgresql';

    // Web Scraper specific
    final startUrlController = TextEditingController();

    int? selectedProjectId = ref.read(currentProjectProvider)?.id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final theme = Theme.of(context);
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'Create Data Source',
              actions: [
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 16,
                    ),
                  ),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () async {
                    Map<String, dynamic> params = {};
                    if (selectedType == 'API') {
                      params = {
                        'base_url': baseUrlController.text,
                        'api_key': apiKeyController.text,
                      };
                    } else if (selectedType == 'Database') {
                      params = {
                        'host': hostController.text,
                        'port': int.tryParse(portController.text) ?? 5432,
                        'username': userController.text,
                        'password': passController.text,
                        'database_type': dbType,
                        'database': dbNameController.text,
                      };
                    } else if (selectedType == 'Web Scraper') {
                      params = {'start_url': startUrlController.text};
                    }

                    try {
                      final result = await ref
                          .read(dataSourceListProvider.notifier)
                          .testConnection(selectedType, params);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(
                              result['message'] ?? 'Connection test passed!',
                            ),
                          ),
                        );
                      }
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Test failed: $e'),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade700,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 16,
                    ),
                  ),
                  child: const Text('Test Connection'),
                ),
                ElevatedButton(
                  onPressed: () async {
                    Map<String, dynamic> params = {};
                    if (selectedType == 'API') {
                      params = {
                        'base_url': baseUrlController.text,
                        'api_key': apiKeyController.text,
                      };
                    } else if (selectedType == 'Database') {
                      params = {
                        'host': hostController.text,
                        'port': int.tryParse(portController.text) ?? 5432,
                        'username': userController.text,
                        'password': passController.text,
                        'database_type': dbType,
                        'database': dbNameController.text,
                      };
                    } else if (selectedType == 'Web Scraper') {
                      params = {'start_url': startUrlController.text};
                    }

                    try {
                      final source = DataSource(
                        name: nameController.text,
                        title: titleController.text,
                        type: selectedType,
                        parameters: params,
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(dataSourceListProvider.notifier)
                          .createSource(source);
                      ref.invalidate(dataSourceListProvider);
                      if (context.mounted) Navigator.pop(context);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(
                          context,
                        ).showSnackBar(SnackBar(content: Text('Error: $e')));
                      }
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF646CFF),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 16,
                    ),
                  ),
                  child: const Text('Create'),
                ),
              ],
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  projectsAsync.when(
                    data: (projects) => DropdownButtonFormField<int>(
                      value: selectedProjectId,
                      decoration: const InputDecoration(labelText: 'Project'),
                      items: projects
                          .map(
                            (p) => DropdownMenuItem(
                              value: p.id,
                              child: Text(p.title),
                            ),
                          )
                          .toList(),
                      onChanged: (val) =>
                          setState(() => selectedProjectId = val),
                    ),
                    loading: () => const LinearProgressIndicator(),
                    error: (err, _) => Text('Error loading projects: $err'),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: selectedType,
                          decoration: const InputDecoration(
                            labelText: 'Source Type',
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'API',
                              child: Text('REST API'),
                            ),
                            DropdownMenuItem(
                              value: 'Database',
                              child: Text('Database'),
                            ),
                            DropdownMenuItem(
                              value: 'Web Scraper',
                              child: Text('Web Scraper'),
                            ),
                            DropdownMenuItem(
                              value: 'File Upload',
                              child: Text('File Upload'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => selectedType = val!),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: nameController,
                          decoration: const InputDecoration(
                            labelText: 'Name (ID)',
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: titleController,
                    decoration: const InputDecoration(labelText: 'Title'),
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Divider(),
                  ),
                  Text(
                    'Configuration',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (selectedType == 'API') ...[
                    TextField(
                      controller: baseUrlController,
                      decoration: const InputDecoration(labelText: 'Base URL'),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: apiKeyController,
                      decoration: const InputDecoration(labelText: 'API Key'),
                      obscureText: true,
                    ),
                  ] else if (selectedType == 'Database') ...[
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: dbType,
                            decoration: const InputDecoration(
                              labelText: 'DB Type',
                            ),
                            items: const [
                              DropdownMenuItem(
                                value: 'postgresql',
                                child: Text('PostgreSQL'),
                              ),
                              DropdownMenuItem(
                                value: 'mysql',
                                child: Text('MySQL'),
                              ),
                            ],
                            onChanged: (val) => setState(() => dbType = val!),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: hostController,
                            decoration: const InputDecoration(
                              labelText: 'Host',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: portController,
                            decoration: const InputDecoration(
                              labelText: 'Port',
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: userController,
                            decoration: const InputDecoration(
                              labelText: 'Username',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: passController,
                            decoration: const InputDecoration(
                              labelText: 'Password',
                            ),
                            obscureText: true,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: dbNameController,
                            decoration: const InputDecoration(
                              labelText: 'Database Name',
                            ),
                          ),
                        ),
                      ],
                    ),
                  ] else if (selectedType == 'Web Scraper') ...[
                    TextField(
                      controller: startUrlController,
                      decoration: const InputDecoration(labelText: 'Start URL'),
                    ),
                  ] else if (selectedType == 'File Upload') ...[
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(20.0),
                        child: Text(
                          'File upload configuration will appear here.',
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  static void showEditSourceDialog(
    BuildContext context,
    WidgetRef ref,
    DataSource source,
  ) {
    String selectedType = source.type;
    final nameController = TextEditingController(text: source.name);
    final titleController = TextEditingController(text: source.title);

    // API specific
    final baseUrlController = TextEditingController(
      text: source.parameters['base_url']?.toString(),
    );
    final apiKeyController = TextEditingController(
      text: source.parameters['api_key']?.toString(),
    );

    // DB specific
    final hostController = TextEditingController(
      text: source.parameters['host']?.toString(),
    );
    final portController = TextEditingController(
      text: source.parameters['port']?.toString() ?? '5432',
    );
    final userController = TextEditingController(
      text: source.parameters['username']?.toString(),
    );
    final passController = TextEditingController(); // Password kept empty
    final dbNameController = TextEditingController(
      text: source.parameters['database']?.toString(),
    );
    String dbType =
        source.parameters['database_type']?.toString() ?? 'postgresql';

    // Web Scraper specific
    final startUrlController = TextEditingController(
      text: source.parameters['start_url']?.toString(),
    );

    int? selectedProjectId = source.project_id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final theme = Theme.of(context);
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'Edit Data Source',
              actions: [
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 16,
                    ),
                  ),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () async {
                    Map<String, dynamic> params = {};
                    if (selectedType == 'API') {
                      params = {
                        'base_url': baseUrlController.text,
                        'api_key': apiKeyController.text,
                      };
                    } else if (selectedType == 'Database') {
                      params = {
                        'host': hostController.text,
                        'port': int.tryParse(portController.text) ?? 5432,
                        'username': userController.text,
                        'password': passController.text.isEmpty
                            ? null
                            : passController.text,
                        'database_type': dbType,
                        'database': dbNameController.text,
                      };
                    } else if (selectedType == 'Web Scraper') {
                      params = {'start_url': startUrlController.text};
                    }

                    try {
                      final updatedSource = source.copyWith(
                        title: titleController.text,
                        parameters: params,
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(dataSourceListProvider.notifier)
                          .updateSource(updatedSource);
                      ref.invalidate(dataSourceListProvider);
                      if (context.mounted) Navigator.pop(context);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(
                          context,
                        ).showSnackBar(SnackBar(content: Text('Error: $e')));
                      }
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF646CFF),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 24,
                      vertical: 16,
                    ),
                  ),
                  child: const Text('Save'),
                ),
              ],
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  projectsAsync.when(
                    data: (projects) => DropdownButtonFormField<int>(
                      value: selectedProjectId,
                      decoration: const InputDecoration(labelText: 'Project'),
                      items: projects
                          .map(
                            (p) => DropdownMenuItem(
                              value: p.id,
                              child: Text(p.title),
                            ),
                          )
                          .toList(),
                      onChanged: (val) =>
                          setState(() => selectedProjectId = val),
                    ),
                    loading: () => const LinearProgressIndicator(),
                    error: (err, _) => Text('Error loading projects: $err'),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: selectedType,
                          decoration: const InputDecoration(
                            labelText: 'Source Type',
                            filled: true,
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'API',
                              child: Text('REST API'),
                            ),
                            DropdownMenuItem(
                              value: 'Database',
                              child: Text('Database'),
                            ),
                            DropdownMenuItem(
                              value: 'Web Scraper',
                              child: Text('Web Scraper'),
                            ),
                            DropdownMenuItem(
                              value: 'File Upload',
                              child: Text('File Upload'),
                            ),
                          ],
                          onChanged: null, // Disable type change on edit
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: nameController,
                          enabled: false,
                          decoration: const InputDecoration(
                            labelText: 'Name (ID)',
                            filled: true,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: titleController,
                    decoration: const InputDecoration(labelText: 'Title'),
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Divider(),
                  ),
                  Text(
                    'Configuration',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (selectedType == 'API') ...[
                    TextField(
                      controller: baseUrlController,
                      decoration: const InputDecoration(labelText: 'Base URL'),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: apiKeyController,
                      decoration: const InputDecoration(labelText: 'API Key'),
                      obscureText: true,
                    ),
                  ] else if (selectedType == 'Database') ...[
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: dbType,
                            decoration: const InputDecoration(
                              labelText: 'DB Type',
                            ),
                            items: const [
                              DropdownMenuItem(
                                value: 'postgresql',
                                child: Text('PostgreSQL'),
                              ),
                              DropdownMenuItem(
                                value: 'mysql',
                                child: Text('MySQL'),
                              ),
                            ],
                            onChanged: (val) => setState(() => dbType = val!),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: hostController,
                            decoration: const InputDecoration(
                              labelText: 'Host',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: portController,
                            decoration: const InputDecoration(
                              labelText: 'Port',
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: userController,
                            decoration: const InputDecoration(
                              labelText: 'Username',
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: passController,
                            decoration: const InputDecoration(
                              labelText:
                                  'Password (leave empty to keep current)',
                            ),
                            obscureText: true,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: dbNameController,
                            decoration: const InputDecoration(
                              labelText: 'Database Name',
                            ),
                          ),
                        ),
                      ],
                    ),
                  ] else if (selectedType == 'Web Scraper') ...[
                    TextField(
                      controller: startUrlController,
                      decoration: const InputDecoration(labelText: 'Start URL'),
                    ),
                  ] else if (selectedType == 'File Upload') ...[
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(20.0),
                        child: Text(
                          'File upload configuration will appear here.',
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _SourcesList extends ConsumerWidget {
  final List<DataSource> sources;

  const _SourcesList({required this.sources});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (sources.isEmpty) {
      return const Center(child: Text('No data sources found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: sources.length,
      itemBuilder: (context, index) {
        final src = sources[index];
        IconData icon = FontAwesomeIcons.plug;
        if (src.type == 'Database') icon = FontAwesomeIcons.database;
        if (src.type == 'Web Scraper') icon = FontAwesomeIcons.globe;
        if (src.type == 'File Upload') icon = FontAwesomeIcons.fileUpload;

        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ListTile(
            leading: FaIcon(icon, color: Colors.blue),
            title: Text(src.title),
            subtitle: Text('${src.type} • ${src.name}'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ProjectPill(projectId: src.project_id),
                IconButton(
                  icon: const Icon(Icons.edit, color: Colors.grey),
                  onPressed: () =>
                      DataSourcesPage.showEditSourceDialog(context, ref, src),
                ),
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _confirmDelete(context, src),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, DataSource src) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Source'),
          content: Text('Delete "${src.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(dataSourceListProvider.notifier)
                      .deleteSource(src.id!);
                  ref.invalidate(dataSourceListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting source: $e')),
                    );
                  }
                }
              },
              child: const Text('Delete', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      ),
    );
  }
}
