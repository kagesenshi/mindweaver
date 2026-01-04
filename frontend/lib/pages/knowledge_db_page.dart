import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/knowledge_db_provider.dart';
import '../providers/project_provider.dart';
import '../models/knowledge_db.dart';

import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';
import '../widgets/dynamic_form.dart';
import '../providers/form_provider.dart';

class KnowledgeDbPage extends ConsumerWidget {
  const KnowledgeDbPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dbsAsync = ref.watch(knowledgeDBListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Knowledge Databases'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(knowledgeDBListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: dbsAsync.when(
        data: (dbs) => _KnowledgeDBList(dbs: dbs),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDBDialog(context, ref),
        label: const Text('New Database'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateDBDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            createFormSchemaProvider('/api/v1/knowledge_dbs'),
          );
          final formKey = GlobalKey<DynamicFormState>();

          return LargeDialog(
            title: 'Create Knowledge Database',
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
                  'parameters': <String, dynamic>{},
                },
                onSaved: (data) async {
                  try {
                    final newDb = KnowledgeDB.fromJson({
                      ...data,
                      if (!data.containsKey('parameters'))
                        'parameters': <String, dynamic>{},
                    });
                    await ref
                        .read(knowledgeDBListProvider.notifier)
                        .createDB(newDb);
                    ref.invalidate(knowledgeDBListProvider);
                    if (context.mounted) Navigator.pop(context);
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error creating database: $e')),
                      );
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

  static void showEditDBDialog(
    BuildContext context,
    WidgetRef ref,
    KnowledgeDB db,
  ) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            editFormSchemaProvider('/api/v1/knowledge_dbs'),
          );
          final formKey = GlobalKey<DynamicFormState>();

          return LargeDialog(
            title: 'Edit Knowledge Database',
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
                initialValues: db.toJson(),
                onSaved: (data) async {
                  try {
                    final updatedDb = KnowledgeDB.fromJson({
                      ...db.toJson(),
                      ...data,
                    });
                    await ref
                        .read(knowledgeDBListProvider.notifier)
                        .updateDB(updatedDb);
                    ref.invalidate(knowledgeDBListProvider);
                    if (context.mounted) Navigator.pop(context);
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error updating database: $e')),
                      );
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

class _KnowledgeDBList extends ConsumerWidget {
  final List<KnowledgeDB> dbs;

  const _KnowledgeDBList({required this.dbs});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (dbs.isEmpty) {
      return const Center(child: Text('No knowledge databases found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: dbs.length,
      itemBuilder: (context, index) {
        final db = dbs[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ListTile(
            leading: const FaIcon(
              FontAwesomeIcons.database,
              color: Colors.blue,
            ),
            title: Text(db.title),
            subtitle: Text('${db.type} • ${db.name}'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ProjectPill(projectId: db.project_id),
                IconButton(
                  icon: const Icon(Icons.edit, color: Colors.grey),
                  onPressed: () =>
                      KnowledgeDbPage.showEditDBDialog(context, ref, db),
                ),
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _confirmDelete(context, db),
                ),
              ],
            ),
            onTap: () {
              // TODO: Navigate to DB details/management
            },
          ),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, KnowledgeDB db) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Database'),
          content: Text('Are you sure you want to delete "${db.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(knowledgeDBListProvider.notifier)
                      .deleteDB(db.id!);
                  ref.invalidate(knowledgeDBListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting database: $e')),
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
