import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/ai_agent_provider.dart';
import '../providers/knowledge_db_provider.dart';
import '../providers/project_provider.dart';
import '../models/ai_agent.dart';

import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';

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
    final nameController = TextEditingController();
    final titleController = TextEditingController();
    final systemPromptController = TextEditingController();
    String selectedModel = 'gpt-4-turbo';
    double selectedTemp = 0.7;
    List<String> selectedDBIds = [];
    int? selectedProjectId = ref.read(currentProjectProvider)?.id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final dbsAsync = ref.watch(knowledgeDBListProvider);
            final projectsAsync = ref.watch(projectListProvider);
            return LargeDialog(
              title: 'Create AI Agent',
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
                      final newAgent = AIAgent(
                        name: nameController.text,
                        title: titleController.text,
                        model: selectedModel,
                        temperature: selectedTemp,
                        system_prompt: systemPromptController.text,
                        knowledge_db_ids: selectedDBIds,
                        project_id: selectedProjectId,
                      );
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
                        child: DropdownButtonFormField<String>(
                          value: selectedModel,
                          decoration: const InputDecoration(labelText: 'Model'),
                          items: const [
                            DropdownMenuItem(
                              value: 'gpt-4-turbo',
                              child: Text('GPT-4 Turbo'),
                            ),
                            DropdownMenuItem(
                              value: 'gpt-3.5-turbo',
                              child: Text('GPT-3.5 Turbo'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => selectedModel = val!),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Temperature: ${selectedTemp.toStringAsFixed(1)}',
                              style: const TextStyle(fontSize: 10),
                            ),
                            Slider(
                              value: selectedTemp,
                              onChanged: (val) =>
                                  setState(() => selectedTemp = val),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: systemPromptController,
                    decoration: const InputDecoration(
                      labelText: 'System Prompt',
                    ),
                    maxLines: 5,
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Knowledge Databases',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 12),
                  dbsAsync.when(
                    data: (dbs) => Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: dbs.map((db) {
                        final isSelected = selectedDBIds.contains(db.uuid);
                        return FilterChip(
                          label: Text(db.title),
                          selected: isSelected,
                          onSelected: (selected) {
                            setState(() {
                              if (selected) {
                                selectedDBIds.add(db.uuid!);
                              } else {
                                selectedDBIds.remove(db.uuid!);
                              }
                            });
                          },
                        );
                      }).toList(),
                    ),
                    loading: () => const LinearProgressIndicator(),
                    error: (err, _) => Text('Error loading databases: $err'),
                  ),
                ],
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
    final nameController = TextEditingController(text: agent.name);
    final titleController = TextEditingController(text: agent.title);
    final systemPromptController = TextEditingController(
      text: agent.system_prompt,
    );
    String selectedModel = agent.model;
    double selectedTemperature = agent.temperature;
    String selectedStatus = agent.status;
    List<String> selectedKnowledgeDBNames = List.from(agent.knowledge_db_ids);
    int? selectedProjectId = agent.project_id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final knowledgeDBsAsync = ref.watch(knowledgeDBListProvider);
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'Edit AI Agent',
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
                      final updatedAgent = agent.copyWith(
                        title: titleController.text,
                        model: selectedModel,
                        temperature: selectedTemperature,
                        system_prompt: systemPromptController.text,
                        status: selectedStatus,
                        knowledge_db_ids: selectedKnowledgeDBNames,
                        project_id: selectedProjectId,
                      );
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
                        child: DropdownButtonFormField<String>(
                          value: selectedModel,
                          decoration: const InputDecoration(labelText: 'Model'),
                          items: const [
                            DropdownMenuItem(
                              value: 'gpt-4-turbo',
                              child: Text('GPT-4 Turbo'),
                            ),
                            DropdownMenuItem(
                              value: 'gpt-4',
                              child: Text('GPT-4'),
                            ),
                            DropdownMenuItem(
                              value: 'gpt-3.5-turbo',
                              child: Text('GPT-3.5 Turbo'),
                            ),
                            DropdownMenuItem(
                              value: 'claude-3-opus',
                              child: Text('Claude 3 Opus'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => selectedModel = val!),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: selectedStatus,
                          decoration: const InputDecoration(
                            labelText: 'Status',
                            filled: true,
                          ),
                          items: const [
                            DropdownMenuItem(
                              value: 'Active',
                              child: Text('Active'),
                            ),
                            DropdownMenuItem(
                              value: 'Inactive',
                              child: Text('Inactive'),
                            ),
                          ],
                          onChanged: (val) =>
                              setState(() => selectedStatus = val!),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Temperature: ${selectedTemperature.toStringAsFixed(1)}',
                  ),
                  Slider(
                    value: selectedTemperature,
                    min: 0,
                    max: 1,
                    onChanged: (val) =>
                        setState(() => selectedTemperature = val),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: systemPromptController,
                    decoration: const InputDecoration(
                      labelText: 'System Prompt',
                    ),
                    maxLines: 4,
                  ),
                  const SizedBox(height: 16),
                  knowledgeDBsAsync.when(
                    data: (dbs) => Wrap(
                      spacing: 8,
                      children: dbs.map((db) {
                        final isSelected = selectedKnowledgeDBNames.contains(
                          db.name,
                        );
                        return FilterChip(
                          label: Text(db.title),
                          selected: isSelected,
                          onSelected: (selected) {
                            setState(() {
                              if (selected) {
                                selectedKnowledgeDBNames.add(db.name);
                              } else {
                                selectedKnowledgeDBNames.remove(db.name);
                              }
                            });
                          },
                        );
                      }).toList(),
                    ),
                    loading: () => const LinearProgressIndicator(),
                    error: (err, _) => Text('Error loading DBs: $err'),
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
