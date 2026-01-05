import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/s3_storage_provider.dart';
import '../providers/project_provider.dart';
import '../models/s3_storage.dart';

import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';

class S3StoragePage extends ConsumerWidget {
  const S3StoragePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storagesAsync = ref.watch(s3StorageListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('S3 Storage'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(s3StorageListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: storagesAsync.when(
        data: (storages) => _StoragesList(storages: storages),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateStorageDialog(context, ref),
        label: const Text('New Storage'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateStorageDialog(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final titleController = TextEditingController();
    final regionController = TextEditingController(text: 'us-east-1');
    final accessKeyController = TextEditingController();
    final secretKeyController = TextEditingController();
    final endpointController = TextEditingController();

    int? selectedProjectId = ref.read(currentProjectProvider)?.id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'New S3 Storage',
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
                    final params = {
                      'region': regionController.text,
                      'access_key': accessKeyController.text,
                      'secret_key': secretKeyController.text,
                      'endpoint_url': endpointController.text.isEmpty
                          ? null
                          : endpointController.text,
                    };
                    try {
                      final result = await ref
                          .read(s3StorageListProvider.notifier)
                          .testConnection(params);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(result['message'] ?? 'Connected!'),
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
                    final storage = S3Storage(
                      name: nameController.text,
                      title: titleController.text,
                      region: regionController.text,
                      access_key: accessKeyController.text,
                      secret_key: secretKeyController.text,
                      endpoint_url: endpointController.text.isEmpty
                          ? null
                          : endpointController.text,
                      project_id: selectedProjectId,
                      parameters: {},
                    );
                    try {
                      await ref
                          .read(s3StorageListProvider.notifier)
                          .createStorage(storage);
                      ref.invalidate(s3StorageListProvider);
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
                        child: TextField(
                          controller: nameController,
                          decoration: const InputDecoration(
                            labelText: 'Name (ID)',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: titleController,
                          decoration: const InputDecoration(labelText: 'Title'),
                        ),
                      ),
                    ],
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Divider(),
                  ),
                  const Text(
                    'S3 Configuration',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: regionController,
                    decoration: const InputDecoration(labelText: 'Region'),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: accessKeyController,
                          decoration: const InputDecoration(
                            labelText: 'Access Key',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: secretKeyController,
                          decoration: const InputDecoration(
                            labelText: 'Secret Key',
                          ),
                          obscureText: true,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: endpointController,
                    decoration: const InputDecoration(
                      labelText: 'Endpoint URL (Optional)',
                      hintText: 'e.g. https://minio.example.com',
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  static void showEditStorageDialog(
    BuildContext context,
    WidgetRef ref,
    S3Storage storage,
  ) {
    final nameController = TextEditingController(text: storage.name);
    final titleController = TextEditingController(text: storage.title);
    final regionController = TextEditingController(text: storage.region);
    final accessKeyController = TextEditingController(text: storage.access_key);
    final secretKeyController = TextEditingController(); // Empty for security
    final endpointController = TextEditingController(
      text: storage.endpoint_url,
    );

    int? selectedProjectId = storage.project_id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'Edit S3 Storage',
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
                    try {
                      final updatedStorage = storage.copyWith(
                        title: titleController.text,
                        region: regionController.text,
                        access_key: accessKeyController.text,
                        secret_key: secretKeyController.text.isEmpty
                            ? null
                            : secretKeyController.text,
                        endpoint_url: endpointController.text.isEmpty
                            ? null
                            : endpointController.text,
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(s3StorageListProvider.notifier)
                          .updateStorage(updatedStorage);
                      ref.invalidate(s3StorageListProvider);
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
                        child: TextField(
                          controller: nameController,
                          enabled: false,
                          decoration: const InputDecoration(
                            labelText: 'Name (ID)',
                            filled: true,
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: titleController,
                          decoration: const InputDecoration(labelText: 'Title'),
                        ),
                      ),
                    ],
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Divider(),
                  ),
                  const Text(
                    'S3 Configuration',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: regionController,
                    decoration: const InputDecoration(labelText: 'Region'),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: accessKeyController,
                          decoration: const InputDecoration(
                            labelText: 'Access Key',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: secretKeyController,
                          decoration: const InputDecoration(
                            labelText:
                                'Secret Key (leave empty to keep current)',
                          ),
                          obscureText: true,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: endpointController,
                    decoration: const InputDecoration(
                      labelText: 'Endpoint URL (Optional)',
                      hintText: 'e.g. https://minio.example.com',
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _StoragesList extends ConsumerWidget {
  final List<S3Storage> storages;

  const _StoragesList({required this.storages});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (storages.isEmpty) {
      return const Center(child: Text('No S3 storages found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: storages.length,
      itemBuilder: (context, index) {
        final st = storages[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ListTile(
            leading: const FaIcon(FontAwesomeIcons.server, color: Colors.blue),
            title: Text(st.title),
            subtitle: Text('Region: ${st.region} • ${st.name}'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ProjectPill(projectId: st.project_id),
                IconButton(
                  icon: const Icon(Icons.edit, color: Colors.grey),
                  onPressed: () =>
                      S3StoragePage.showEditStorageDialog(context, ref, st),
                ),
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _confirmDelete(context, st),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, S3Storage st) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Storage'),
          content: Text('Delete "${st.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(s3StorageListProvider.notifier)
                      .deleteStorage(st.id!);
                  ref.invalidate(s3StorageListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting storage: $e')),
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
