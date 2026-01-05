import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../models/s3_storage.dart';
import '../providers/s3_storage_provider.dart';
import '../providers/project_provider.dart';

import '../providers/form_provider.dart';
import '../widgets/large_dialog.dart';
import '../widgets/dynamic_form.dart';
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
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(s3StorageListProvider),
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: storagesAsync.when(
        data: (storages) => _StoragesList(storages: storages),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err\n$stack')),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => showCreateStorageDialog(context, ref),
        child: const Icon(Icons.add),
      ),
    );
  }

  void showCreateStorageDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            createFormSchemaProvider('/api/v1/s3_storages'),
          );
          final formKey = GlobalKey<DynamicFormState>();

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
                  final data = formKey.currentState?.getFormData();
                  if (data == null) return;
                  try {
                    final result = await ref
                        .read(s3StorageListProvider.notifier)
                        .testConnection(data);
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
                onPressed: () => formKey.currentState?.submit(),
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
            child: schemaAsync.when(
              data: (schema) => DynamicForm(
                key: formKey,
                schema: schema,
                initialValues: {
                  'project_id': ref.read(currentProjectProvider)?.id,
                  'region': 'us-east-1',
                },
                onSaved: (data) async {
                  try {
                    final storage = S3Storage.fromJson(data);
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
              ),
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.all(32.0),
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (err, _) =>
                  Center(child: Text('Error loading form: $err')),
            ),
          );
        },
      ),
    );
  }

  static void showEditStorageDialog(
    BuildContext context,
    WidgetRef ref,
    S3Storage storage,
  ) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            editFormSchemaProvider('/api/v1/s3_storages'),
          );
          final formKey = GlobalKey<DynamicFormState>();

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
                  final data = formKey.currentState?.getFormData();
                  if (data == null) return;
                  try {
                    final testData = {
                      ...data,
                      if (storage.id != null) 'storage_id': storage.id,
                    };
                    final result = await ref
                        .read(s3StorageListProvider.notifier)
                        .testConnection(testData);
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
                onPressed: () => formKey.currentState?.submit(),
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
            child: schemaAsync.when(
              data: (schema) => DynamicForm(
                key: formKey,
                schema: schema,
                isEdit: true,
                initialValues: storage.toJson(),
                onSaved: (data) async {
                  try {
                    final updatedStorage = S3Storage.fromJson({
                      ...storage.toJson(),
                      ...data,
                    });
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
              ),
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.all(32.0),
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (err, _) =>
                  Center(child: Text('Error loading form: $err')),
            ),
          );
        },
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
