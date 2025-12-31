import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/ontology_provider.dart';
import '../providers/project_provider.dart';
import '../models/ontology.dart';

import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';

class OntologyPage extends ConsumerWidget {
  const OntologyPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ontologiesAsync = ref.watch(ontologyListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ontologies'),
        actions: [
          IconButton(
            onPressed: () =>
                ref.read(ontologyListProvider.notifier).loadOntologies(),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ontologiesAsync.when(
        data: (ontologies) => _OntologyList(ontologies: ontologies),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateOntologyDialog(context, ref),
        label: const Text('New Ontology'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateOntologyDialog(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final titleController = TextEditingController();
    final descController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final projectsAsync = ref.watch(projectListProvider);
            int? selectedProjectId = ref.read(currentProjectProvider)?.id;

            return LargeDialog(
              title: 'Create Ontology',
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
                    final ontology = Ontology(
                      name: nameController.text,
                      title: titleController.text,
                      description: descController.text,
                      entity_types: [],
                      relationship_types: [],
                      project_id: selectedProjectId,
                    );
                    try {
                      await ref
                          .read(ontologyListProvider.notifier)
                          .createOntology(ontology);
                      ref.invalidate(ontologyListProvider);
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
                  TextField(
                    controller: descController,
                    decoration: const InputDecoration(labelText: 'Description'),
                    maxLines: 4,
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

class _OntologyList extends StatelessWidget {
  final List<Ontology> ontologies;

  const _OntologyList({required this.ontologies});

  @override
  Widget build(BuildContext context) {
    if (ontologies.isEmpty) {
      return const Center(child: Text('No ontologies found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: ontologies.length,
      itemBuilder: (context, index) {
        final o = ontologies[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ExpansionTile(
            leading: const FaIcon(
              FontAwesomeIcons.diagramProject,
              color: Colors.blue,
            ),
            title: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(o.title),
                      Text(
                        '${o.entity_types?.length ?? 0} Entities • ${o.relationship_types?.length ?? 0} Relationships',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                ProjectPill(projectId: o.project_id),
              ],
            ),
            children: [
              Padding(
                padding: const EdgeInsets.all(15),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Entity Types:',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.grey.shade700,
                      ),
                    ),
                    Wrap(
                      spacing: 8,
                      children:
                          o.entity_types
                              ?.map((et) => Chip(label: Text(et.name)))
                              .toList() ??
                          [],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      'Relationship Types:',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.grey.shade700,
                      ),
                    ),
                    Wrap(
                      spacing: 8,
                      children:
                          o.relationship_types
                              ?.map((rt) => Chip(label: Text(rt.name)))
                              .toList() ??
                          [],
                    ),
                    const SizedBox(height: 10),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton.icon(
                          onPressed: () {
                            // TODO: Manage detailed ontology schema
                          },
                          icon: const Icon(Icons.edit),
                          label: const Text('Manage Schema'),
                        ),
                        IconButton(
                          onPressed: () => _confirmDelete(context, o),
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

  void _confirmDelete(BuildContext context, Ontology o) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Ontology'),
          content: Text('Delete "${o.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(ontologyListProvider.notifier)
                      .deleteOntology(o.id!);
                  ref.invalidate(ontologyListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting ontology: $e')),
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
