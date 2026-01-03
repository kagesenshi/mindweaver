import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/ai_agent_provider.dart';
import '../providers/project_provider.dart';
import '../models/ai_agent.dart';

import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';
import '../widgets/dynamic_form.dart';
import '../providers/form_provider.dart';

class AiAgentsPage extends ConsumerWidget {
  const AiAgentsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final agentsAsync = ref.watch(aiAgentListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Agents'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(aiAgentListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: agentsAsync.when(
        data: (agents) => _AgentsList(agents: agents),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateAgentDialog(context, ref),
        label: const Text('New Agent'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateAgentDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final schemaAsync = ref.watch(
              createFormSchemaProvider('/api/v1/ai_agents'),
            );
            final formKey = GlobalKey<DynamicFormState>();

            return LargeDialog(
              title: 'Create AI Agent',
              actions: [
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () => formKey.currentState?.submit(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF646CFF),
                    foregroundColor: Colors.white,
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
                  },
                  onSaved: (data) async {
                    try {
                      final newAgent = AIAgent.fromJson(data);
                      await ref
                          .read(aiAgentListProvider.notifier)
                          .createAgent(newAgent);
                      ref.invalidate(aiAgentListProvider);
                      if (context.mounted) Navigator.pop(context);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Error creating agent: $e')),
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
      ),
    );
  }

  static void showEditAgentDialog(
    BuildContext context,
    WidgetRef ref,
    AIAgent agent,
  ) {
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final schemaAsync = ref.watch(
              editFormSchemaProvider('/api/v1/ai_agents'),
            );
            final formKey = GlobalKey<DynamicFormState>();

            return LargeDialog(
              title: 'Edit AI Agent',
              actions: [
                OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () => formKey.currentState?.submit(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF646CFF),
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Save'),
                ),
              ],
              child: schemaAsync.when(
                data: (schema) => DynamicForm(
                  key: formKey,
                  schema: schema,
                  isEdit: true,
                  initialValues: agent.toJson(),
                  onSaved: (data) async {
                    try {
                      final updatedAgent = AIAgent.fromJson(
                        data,
                      ).copyWith(id: agent.id);
                      await ref
                          .read(aiAgentListProvider.notifier)
                          .updateAgent(updatedAgent);
                      ref.invalidate(aiAgentListProvider);
                      if (context.mounted) Navigator.pop(context);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Error updating agent: $e')),
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
      ),
    );
  }
}

class _AgentsList extends ConsumerWidget {
  final List<AIAgent> agents;

  const _AgentsList({required this.agents});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (agents.isEmpty) {
      return const Center(child: Text('No AI agents found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: agents.length,
      itemBuilder: (context, index) {
        final agent = agents[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ListTile(
            leading: const FaIcon(FontAwesomeIcons.robot, color: Colors.purple),
            title: Text(agent.title),
            subtitle: Text('${agent.model} • ${agent.status}'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ProjectPill(projectId: agent.project_id),
                IconButton(
                  icon: const Icon(Icons.edit, color: Colors.grey),
                  onPressed: () =>
                      AiAgentsPage.showEditAgentDialog(context, ref, agent),
                ),
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _confirmDelete(context, agent),
                ),
              ],
            ),
            onTap: () {
              // TODO: Navigate to agent configuration/logs
            },
          ),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, AIAgent agent) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Agent'),
          content: Text('Are you sure you want to delete "${agent.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(aiAgentListProvider.notifier)
                      .deleteAgent(agent.id!);
                  ref.invalidate(aiAgentListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting agent: $e')),
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
