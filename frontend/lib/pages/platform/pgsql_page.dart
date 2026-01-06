import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../../providers/platform/pgsql_provider.dart';
import '../../providers/project_provider.dart';
import '../../models/platform/pgsql.dart';

import '../../widgets/large_dialog.dart';
import '../../widgets/project_pill.dart';
import '../../widgets/dynamic_form.dart';
import '../../providers/form_provider.dart';

class PgSqlPage extends ConsumerWidget {
  const PgSqlPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final platformsAsync = ref.watch(pgsqlPlatformListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('PostgreSQL Platforms'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(pgsqlPlatformListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: platformsAsync.when(
        data: (platforms) => _PlatformsList(platforms: platforms),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreatePlatformDialog(context, ref),
        label: const Text('New PostgreSQL'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreatePlatformDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            createFormSchemaProvider('/api/v1/platform/pgsql'),
          );
          final formKey = GlobalKey<DynamicFormState>();

          return LargeDialog(
            title: 'New PostgreSQL Platform',
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
                  'instances': 3,
                  'storage_size': '1Gi',
                  'backup_retention_policy': '30d',
                },
                onSaved: (data) async {
                  try {
                    final newPlatform = PgSqlPlatform.fromJson(data);
                    await ref
                        .read(pgsqlPlatformListProvider.notifier)
                        .createPlatform(newPlatform);
                    ref.invalidate(pgsqlPlatformListProvider);
                    if (context.mounted) Navigator.pop(context);
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error creating platform: $e')),
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

  static void showEditPlatformDialog(
    BuildContext context,
    WidgetRef ref,
    PgSqlPlatform platform,
  ) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) {
          final schemaAsync = ref.watch(
            editFormSchemaProvider('/api/v1/platform/pgsql'),
          );
          final formKey = GlobalKey<DynamicFormState>();

          return LargeDialog(
            title: 'Edit PostgreSQL Platform',
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
                initialValues: platform.toJson(),
                onSaved: (data) async {
                  try {
                    final updatedPlatform = PgSqlPlatform.fromJson({
                      ...platform.toJson(),
                      ...data,
                    });
                    await ref
                        .read(pgsqlPlatformListProvider.notifier)
                        .updatePlatform(updatedPlatform);
                    ref.invalidate(pgsqlPlatformListProvider);
                    if (context.mounted) Navigator.pop(context);
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error updating platform: $e')),
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

class _PlatformsList extends ConsumerWidget {
  final List<PgSqlPlatform> platforms;

  const _PlatformsList({required this.platforms});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (platforms.isEmpty) {
      return const Center(child: Text('No PostgreSQL platforms found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: platforms.length,
      itemBuilder: (context, index) {
        final st = platforms[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: Consumer(
            builder: (context, ref, _) {
              final stateAsync = ref.watch(pgsqlPlatformStateProvider(st.id!));

              return ListTile(
                leading: const FaIcon(
                  FontAwesomeIcons.database,
                  color: Colors.blue,
                ),
                title: Row(
                  children: [
                    Expanded(
                      child: Text(st.title, overflow: TextOverflow.ellipsis),
                    ),
                    const SizedBox(width: 8),
                    stateAsync.when(
                      data: (state) => Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: _getStatusColor(state.status).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: _getStatusColor(state.status),
                          ),
                        ),
                        child: Text(
                          state.status.toUpperCase(),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: _getStatusColor(state.status),
                          ),
                        ),
                      ),
                      loading: () => const SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      error: (_, __) =>
                          const Icon(Icons.error, color: Colors.red, size: 16),
                    ),
                  ],
                ),
                subtitle: Text('Instances: ${st.instances} • ${st.name}'),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    ProjectPill(projectId: st.project_id),
                    IconButton(
                      icon: const Icon(Icons.edit, color: Colors.grey),
                      onPressed: () =>
                          PgSqlPage.showEditPlatformDialog(context, ref, st),
                    ),
                    stateAsync.maybeWhen(
                      data: (state) => Switch(
                        value: state.active,
                        onChanged: (value) async {
                          try {
                            await ref
                                .read(pgsqlPlatformListProvider.notifier)
                                .updatePlatformState(st.id!, active: value);
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('Error updating state: $e'),
                                ),
                              );
                            }
                          }
                        },
                      ),
                      loading: () => stateAsync.hasValue
                          ? Switch(
                              value: stateAsync.value!.active,
                              onChanged: null,
                            )
                          : const Switch(value: false, onChanged: null),
                      orElse: () => const Switch(value: false, onChanged: null),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete, color: Colors.red),
                      onPressed: () => _confirmDelete(context, st),
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'online':
        return Colors.green;
      case 'offline':
        return Colors.grey;
      case 'pending':
        return Colors.orange;
      case 'error':
        return Colors.red;
      default:
        return Colors.blueGrey;
    }
  }

  void _confirmDelete(BuildContext context, PgSqlPlatform st) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Platform'),
          content: Text('Are you sure you want to delete "${st.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(pgsqlPlatformListProvider.notifier)
                      .deletePlatform(st.id!);
                  ref.invalidate(pgsqlPlatformListProvider);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting platform: $e')),
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
