import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/data_source_provider.dart';
import '../models/data_source.dart';

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
            onPressed: () =>
                ref.read(dataSourceListProvider.notifier).loadSources(),
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

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Create Data Source'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  initialValue: selectedType,
                  decoration: const InputDecoration(labelText: 'Source Type'),
                  items: const [
                    DropdownMenuItem(value: 'API', child: Text('REST API')),
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
                  onChanged: (val) => setState(() => selectedType = val!),
                ),
                TextField(
                  controller: nameController,
                  decoration: const InputDecoration(labelText: 'Name (ID)'),
                ),
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(labelText: 'Title'),
                ),
                const Divider(height: 40),
                if (selectedType == 'API') ...[
                  TextField(
                    controller: baseUrlController,
                    decoration: const InputDecoration(labelText: 'Base URL'),
                  ),
                  TextField(
                    controller: apiKeyController,
                    decoration: const InputDecoration(labelText: 'API Key'),
                    obscureText: true,
                  ),
                ] else if (selectedType == 'Database') ...[
                  DropdownButtonFormField<String>(
                    initialValue: dbType,
                    decoration: const InputDecoration(labelText: 'DB Type'),
                    items: const [
                      DropdownMenuItem(
                        value: 'postgresql',
                        child: Text('PostgreSQL'),
                      ),
                      DropdownMenuItem(value: 'mysql', child: Text('MySQL')),
                    ],
                    onChanged: (val) => setState(() => dbType = val!),
                  ),
                  TextField(
                    controller: hostController,
                    decoration: const InputDecoration(labelText: 'Host'),
                  ),
                  TextField(
                    controller: portController,
                    decoration: const InputDecoration(labelText: 'Port'),
                    keyboardType: TextInputType.number,
                  ),
                  TextField(
                    controller: userController,
                    decoration: const InputDecoration(labelText: 'Username'),
                  ),
                  TextField(
                    controller: passController,
                    decoration: const InputDecoration(labelText: 'Password'),
                    obscureText: true,
                  ),
                  TextField(
                    controller: dbNameController,
                    decoration: const InputDecoration(
                      labelText: 'Database Name',
                    ),
                  ),
                ] else if (selectedType == 'Web Scraper') ...[
                  TextField(
                    controller: startUrlController,
                    decoration: const InputDecoration(labelText: 'Start URL'),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
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
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SourcesList extends StatelessWidget {
  final List<DataSource> sources;

  const _SourcesList({required this.sources});

  @override
  Widget build(BuildContext context) {
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
            trailing: IconButton(
              icon: const Icon(Icons.delete, color: Colors.red),
              onPressed: () => _confirmDelete(context, src),
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
