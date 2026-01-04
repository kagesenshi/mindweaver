import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/ingestion_provider.dart';
import '../providers/project_provider.dart';
import '../models/ingestion.dart';
import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';
import '../widgets/dynamic_form.dart';
import '../providers/form_provider.dart';

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
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            createFormSchemaProvider('/api/v1/ingestions'),
          );
          final formKey = GlobalKey<DynamicFormState>();

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
                  'config': <String, dynamic>{},
                  'storage_path': '/s3/data',
                  'cron_schedule': '0 0 * * *',
                  'ingestion_type': 'full_refresh',
                },
                onSaved: (data) async {
                  try {
                    final ingestion = Ingestion.fromJson({
                      ...data,
                      if (!data.containsKey('config'))
                        'config': <String, dynamic>{},
                    });
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

  static void showEditIngestionDialog(
    BuildContext context,
    WidgetRef ref,
    Ingestion ingestion,
  ) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            editFormSchemaProvider('/api/v1/ingestions'),
          );
          final formKey = GlobalKey<DynamicFormState>();

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
                initialValues: ingestion.toJson(),
                onSaved: (data) async {
                  try {
                    final updatedIngestion = Ingestion.fromJson({
                      ...ingestion.toJson(),
                      ...data,
                    });
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
