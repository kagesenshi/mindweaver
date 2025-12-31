import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/knowledge_db_provider.dart';
import '../providers/ontology_provider.dart';
import '../providers/project_provider.dart';
import '../models/knowledge_db.dart';

import '../widgets/large_dialog.dart';

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
            onPressed: () =>
                ref.read(knowledgeDBListProvider.notifier).loadDBs(),
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
    final nameController = TextEditingController();
    final titleController = TextEditingController();
    final descController = TextEditingController();
    String selectedType = 'passage-graph';
    int? selectedOntologyId;
    int? selectedProjectId = ref.read(currentProjectProvider)?.id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final ontologiesAsync = ref.watch(ontologyListProvider);
            final projectsAsync = ref.watch(projectListProvider);
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
                  onPressed: () async {
                    try {
                      final newDb = KnowledgeDB(
                        name: nameController.text,
                        title: titleController.text,
                        description: descController.text,
                        type: selectedType,
                        ontology_id: selectedOntologyId,
                        parameters: {},
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(knowledgeDBListProvider.notifier)
                          .createDB(newDb);
                      ref.invalidate(knowledgeDBListProvider);
                      if (context.mounted) Navigator.pop(context);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Error creating database: $e'),
                          ),
                        );
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
                  TextField(
                    controller: descController,
                    decoration: const InputDecoration(labelText: 'Description'),
                  ),
                  const SizedBox(height: 24),
                  const Divider(),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: selectedType,
                          decoration: const InputDecoration(labelText: 'Type'),
                          items: const [
                            DropdownMenuItem(
                              value: 'passage-graph',
                              child: Text('Passage Graph'),
                            ),
                            DropdownMenuItem(
                              value: 'tree-graph',
                              child: Text('Tree Graph'),
                            ),
                            DropdownMenuItem(
                              value: 'knowledge-graph',
                              child: Text('Knowledge Graph'),
                            ),
                            DropdownMenuItem(
                              value: 'textual-knowledge-graph',
                              child: Text('Textual Knowledge Graph'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => selectedType = val!),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: ontologiesAsync.when(
                          data: (ontologies) => DropdownButtonFormField<int?>(
                            value: selectedOntologyId,
                            decoration: const InputDecoration(
                              labelText: 'Ontology (Optional)',
                            ),
                            items: [
                              const DropdownMenuItem(
                                value: null,
                                child: Text('None'),
                              ),
                              ...ontologies.map(
                                (o) => DropdownMenuItem(
                                  value: o.id,
                                  child: Text(o.title),
                                ),
                              ),
                            ],
                            onChanged: (val) =>
                                setState(() => selectedOntologyId = val),
                          ),
                          loading: () => const LinearProgressIndicator(),
                          error: (err, _) =>
                              Text('Error loading ontologies: $err'),
                        ),
                      ),
                    ],
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

class _KnowledgeDBList extends StatelessWidget {
  final List<KnowledgeDB> dbs;

  const _KnowledgeDBList({required this.dbs});

  @override
  Widget build(BuildContext context) {
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
            trailing: IconButton(
              icon: const Icon(Icons.delete, color: Colors.red),
              onPressed: () => _confirmDelete(context, db),
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
