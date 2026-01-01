import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/ingestion_provider.dart';
import '../providers/data_source_provider.dart';
import '../providers/lakehouse_storage_provider.dart';
import '../providers/project_provider.dart';
import '../models/ingestion.dart';
import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';

class IngestionPage extends ConsumerWidget {
  const IngestionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ingestionsAsync = ref.watch(ingestionListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Data Ingestion'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(ingestionListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ingestionsAsync.when(
        data: (ingestions) => _IngestionsList(ingestions: ingestions),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateIngestionDialog(context, ref),
        label: const Text('New Ingestion'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateIngestionDialog(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final titleController = TextEditingController();
    final pathController = TextEditingController(text: '/lakehouse/data');
    final cronController = TextEditingController(text: '0 0 * * *');
    String ingestionType = 'full_refresh';
    int? selectedSourceId;
    int? selectedStorageId;
    int? selectedProjectId = ref.read(currentProjectProvider)?.id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final sourcesAsync = ref.watch(dataSourceListProvider);
            final storagesAsync = ref.watch(lakehouseStorageListProvider);
            final projectsAsync = ref.watch(projectListProvider);
            return LargeDialog(
              title: 'New Ingestion Job',
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
                    if (selectedSourceId == null || selectedStorageId == null) {
                      return;
                    }
                    final ingestion = Ingestion(
                      name: nameController.text,
                      title: titleController.text,
                      data_source_id: selectedSourceId!,
                      lakehouse_storage_id: selectedStorageId!,
                      storage_path: pathController.text,
                      cron_schedule: cronController.text,
                      ingestion_type: ingestionType,
                      config: {},
                      project_id: selectedProjectId,
                    );
                    try {
                      await ref
                          .read(ingestionListProvider.notifier)
                          .createIngestion(ingestion);
                      ref.invalidate(ingestionListProvider);
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
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: sourcesAsync.when(
                          data: (sources) => DropdownButtonFormField<int?>(
                            value: selectedSourceId,
                            decoration: const InputDecoration(
                              labelText: 'Data Source',
                            ),
                            items: sources
                                .map(
                                  (s) => DropdownMenuItem(
                                    value: s.id,
                                    child: Text(s.title),
                                  ),
                                )
                                .toList(),
                            onChanged: (val) =>
                                setState(() => selectedSourceId = val),
                          ),
                          loading: () => const LinearProgressIndicator(),
                          error: (err, _) => Text('Error: $err'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: storagesAsync.when(
                          data: (storages) => DropdownButtonFormField<int?>(
                            value: selectedStorageId,
                            decoration: const InputDecoration(
                              labelText: 'Lakehouse Storage',
                            ),
                            items: storages
                                .map(
                                  (s) => DropdownMenuItem(
                                    value: s.id,
                                    child: Text(s.title),
                                  ),
                                )
                                .toList(),
                            onChanged: (val) =>
                                setState(() => selectedStorageId = val),
                          ),
                          loading: () => const LinearProgressIndicator(),
                          error: (err, _) => Text('Error: $err'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: pathController,
                          decoration: const InputDecoration(
                            labelText: 'Storage Path',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: ingestionType,
                          decoration: const InputDecoration(
                            labelText: 'Ingestion Type',
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'full_refresh',
                              child: Text('Full Refresh'),
                            ),
                            DropdownMenuItem(
                              value: 'incremental',
                              child: Text('Incremental'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => ingestionType = val!),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: cronController,
                    decoration: const InputDecoration(
                      labelText: 'Cron Schedule',
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

  static void showEditIngestionDialog(
    BuildContext context,
    WidgetRef ref,
    Ingestion ingestion,
  ) {
    final nameController = TextEditingController(text: ingestion.name);
    final titleController = TextEditingController(text: ingestion.title);
    final pathController = TextEditingController(text: ingestion.storage_path);
    final cronController = TextEditingController(text: ingestion.cron_schedule);
    String ingestionType = ingestion.ingestion_type;
    int? selectedSourceId = ingestion.data_source_id;
    int? selectedStorageId = ingestion.lakehouse_storage_id;
    int? selectedProjectId = ingestion.project_id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final sourcesAsync = ref.watch(dataSourceListProvider);
            final storagesAsync = ref.watch(lakehouseStorageListProvider);
            final projectsAsync = ref.watch(projectListProvider);
            return LargeDialog(
              title: 'Edit Ingestion Job',
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
                    if (selectedSourceId == null || selectedStorageId == null) {
                      return;
                    }
                    try {
                      final updatedIngestion = ingestion.copyWith(
                        title: titleController.text,
                        data_source_id: selectedSourceId,
                        lakehouse_storage_id: selectedStorageId,
                        storage_path: pathController.text,
                        cron_schedule: cronController.text,
                        ingestion_type: ingestionType,
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(ingestionListProvider.notifier)
                          .updateIngestion(updatedIngestion);
                      ref.invalidate(ingestionListProvider);
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
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: sourcesAsync.when(
                          data: (sources) => DropdownButtonFormField<int?>(
                            value: selectedSourceId,
                            decoration: const InputDecoration(
                              labelText: 'Data Source',
                            ),
                            items: sources
                                .map(
                                  (s) => DropdownMenuItem(
                                    value: s.id,
                                    child: Text(s.title),
                                  ),
                                )
                                .toList(),
                            onChanged: (val) =>
                                setState(() => selectedSourceId = val),
                          ),
                          loading: () => const LinearProgressIndicator(),
                          error: (err, _) => Text('Error: $err'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: storagesAsync.when(
                          data: (storages) => DropdownButtonFormField<int?>(
                            value: selectedStorageId,
                            decoration: const InputDecoration(
                              labelText: 'Lakehouse Storage',
                            ),
                            items: storages
                                .map(
                                  (s) => DropdownMenuItem(
                                    value: s.id,
                                    child: Text(s.title),
                                  ),
                                )
                                .toList(),
                            onChanged: (val) =>
                                setState(() => selectedStorageId = val),
                          ),
                          loading: () => const LinearProgressIndicator(),
                          error: (err, _) => Text('Error: $err'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: pathController,
                          decoration: const InputDecoration(
                            labelText: 'Storage Path',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: ingestionType,
                          decoration: const InputDecoration(
                            labelText: 'Ingestion Type',
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'full_refresh',
                              child: Text('Full Refresh'),
                            ),
                            DropdownMenuItem(
                              value: 'incremental',
                              child: Text('Incremental'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => ingestionType = val!),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: cronController,
                    decoration: const InputDecoration(
                      labelText: 'Cron Schedule',
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

class _IngestionsList extends ConsumerWidget {
  final List<Ingestion> ingestions;

  const _IngestionsList({required this.ingestions});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (ingestions.isEmpty) {
      return const Center(child: Text('No ingestion jobs found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: ingestions.length,
      itemBuilder: (context, index) {
        final ing = ingestions[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ExpansionTile(
            leading: const FaIcon(
              FontAwesomeIcons.truckLoading,
              color: Colors.blue,
            ),
            title: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(ing.title),
                      Text(
                        'Schedule: ${ing.cron_schedule} • Type: ${ing.ingestion_type}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                ProjectPill(projectId: ing.project_id),
              ],
            ),
            children: [
              Padding(
                padding: const EdgeInsets.all(15),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        ElevatedButton.icon(
                          onPressed: () => _execute(context, ing),
                          icon: const Icon(Icons.play_arrow),
                          label: const Text('Execute Now'),
                        ),
                        TextButton.icon(
                          onPressed: () => _showHistory(context, ing),
                          icon: const Icon(Icons.history),
                          label: const Text('View History'),
                        ),
                        TextButton.icon(
                          onPressed: () =>
                              IngestionPage.showEditIngestionDialog(
                                context,
                                ref,
                                ing,
                              ),
                          icon: const Icon(Icons.edit),
                          label: const Text('Edit'),
                        ),
                        IconButton(
                          onPressed: () => _confirmDelete(context, ing),
                          icon: const Icon(Icons.delete, color: Colors.red),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _execute(BuildContext context, Ingestion ing) async {
    final ref = ProviderScope.containerOf(context);
    try {
      await ref.read(ingestionListProvider.notifier).executeIngestion(ing.id!);
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Execution triggered!')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  void _showHistory(BuildContext context, Ingestion ing) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final runsFuture = ref
              .read(ingestionListProvider.notifier)
              .getRuns(ing.id!);
          return LargeDialog(
            title: 'History: ${ing.title}',
            actions: [
              OutlinedButton(
                onPressed: () => Navigator.pop(context),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                ),
                child: const Text('Close'),
              ),
            ],
            child: FutureBuilder<List<IngestionRun>>(
              future: runsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return Center(child: Text('Error: ${snapshot.error}'));
                }
                final runs = snapshot.data ?? [];
                if (runs.isEmpty) {
                  return const Center(child: Text('No runs yet.'));
                }
                return ListView.builder(
                  shrinkWrap: true,
                  itemCount: runs.length,
                  itemBuilder: (context, index) {
                    final run = runs[index];
                    return ListTile(
                      leading: _getStatusIcon(run.status),
                      title: Text('Run ID: ${run.id} • ${run.status}'),
                      subtitle: Text(
                        'Processed: ${run.records_processed} • ${run.started_at}',
                      ),
                    );
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }

  Widget _getStatusIcon(String status) {
    switch (status) {
      case 'completed':
        return const Icon(Icons.check_circle, color: Colors.green);
      case 'failed':
        return const Icon(Icons.error, color: Colors.red);
      case 'running':
        return const SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(strokeWidth: 2),
        );
      default:
        return const Icon(Icons.pending, color: Colors.grey);
    }
  }

  void _confirmDelete(BuildContext context, Ingestion ing) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Ingestion'),
          content: Text('Delete "${ing.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(ingestionListProvider.notifier)
                      .deleteIngestion(ing.id!);
                  ref.invalidate(ingestionListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting ingestion: $e')),
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
