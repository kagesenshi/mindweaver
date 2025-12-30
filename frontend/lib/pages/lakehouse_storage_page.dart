import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/lakehouse_storage_provider.dart';
import '../models/lakehouse_storage.dart';

class LakehouseStoragePage extends ConsumerWidget {
  const LakehouseStoragePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storagesAsync = ref.watch(lakehouseStorageListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Lakehouse Storage'),
        actions: [
          IconButton(
            onPressed: () =>
                ref.read(lakehouseStorageListProvider.notifier).loadStorages(),
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
    final bucketController = TextEditingController();
    final regionController = TextEditingController(text: 'us-east-1');
    final accessKeyController = TextEditingController();
    final secretKeyController = TextEditingController();
    final endpointController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New Lakehouse Storage'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameController,
                decoration: const InputDecoration(labelText: 'Name (ID)'),
              ),
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Title'),
              ),
              const Divider(height: 40),
              TextField(
                controller: bucketController,
                decoration: const InputDecoration(labelText: 'Bucket'),
              ),
              TextField(
                controller: regionController,
                decoration: const InputDecoration(labelText: 'Region'),
              ),
              TextField(
                controller: accessKeyController,
                decoration: const InputDecoration(labelText: 'Access Key'),
              ),
              TextField(
                controller: secretKeyController,
                decoration: const InputDecoration(labelText: 'Secret Key'),
                obscureText: true,
              ),
              TextField(
                controller: endpointController,
                decoration: const InputDecoration(
                  labelText: 'Endpoint URL (Optional)',
                  hintText: 'e.g. https://minio.example.com',
                ),
              ),
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
              final params = {
                'bucket': bucketController.text,
                'region': regionController.text,
                'access_key': accessKeyController.text,
                'secret_key': secretKeyController.text,
                'endpoint_url': endpointController.text.isEmpty
                    ? null
                    : endpointController.text,
              };
              try {
                final result = await ref
                    .read(lakehouseStorageListProvider.notifier)
                    .testConnection(params);
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(result['message'] ?? 'Connected!')),
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
              final storage = LakehouseStorage(
                name: nameController.text,
                title: titleController.text,
                parameters: {
                  'bucket': bucketController.text,
                  'region': regionController.text,
                  'access_key': accessKeyController.text,
                  'secret_key': secretKeyController.text,
                  'endpoint_url': endpointController.text.isEmpty
                      ? null
                      : endpointController.text,
                },
              );
              try {
                await ref
                    .read(lakehouseStorageListProvider.notifier)
                    .createStorage(storage);
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
    );
  }
}

class _StoragesList extends StatelessWidget {
  final List<LakehouseStorage> storages;

  const _StoragesList({required this.storages});

  @override
  Widget build(BuildContext context) {
    if (storages.isEmpty)
      return const Center(child: Text('No lakehouse storages found.'));

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
            subtitle: Text(
              'S3 Bucket: ${st.parameters['bucket']} • ${st.name}',
            ),
            trailing: IconButton(
              icon: const Icon(Icons.delete, color: Colors.red),
              onPressed: () => _confirmDelete(context, st),
            ),
          ),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, LakehouseStorage st) {
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
                await ref
                    .read(lakehouseStorageListProvider.notifier)
                    .deleteStorage(st.id!);
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Delete', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      ),
    );
  }
}
