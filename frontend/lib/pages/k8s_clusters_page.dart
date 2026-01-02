import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import '../providers/k8s_cluster_provider.dart';
import '../providers/project_provider.dart';
import '../models/k8s_cluster.dart';
import '../widgets/large_dialog.dart';
import '../widgets/project_pill.dart';

class K8sClustersPage extends ConsumerWidget {
  const K8sClustersPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final clustersAsync = ref.watch(k8sClusterListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Kubernetes Clusters'),
        actions: [
          IconButton(
            onPressed: () => ref.invalidate(k8sClusterListProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: clustersAsync.when(
        data: (clusters) => _ClustersList(clusters: clusters),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateClusterDialog(context, ref),
        label: const Text('Add Cluster'),
        icon: const Icon(Icons.add),
      ),
    );
  }

  void _showCreateClusterDialog(BuildContext context, WidgetRef ref) {
    final nameController = TextEditingController();
    final titleController = TextEditingController();
    final kubeconfigController = TextEditingController();
    String selectedType = 'remote';

    int? selectedProjectId = ref.read(currentProjectProvider)?.id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'Add Kubernetes Cluster',
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
                      final cluster = K8sCluster(
                        name: nameController.text,
                        title: titleController.text,
                        type: selectedType,
                        kubeconfig: selectedType == 'remote'
                            ? kubeconfigController.text
                            : null,
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(k8sClusterListProvider.notifier)
                          .createCluster(cluster);
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
                  DropdownButtonFormField<String>(
                    value: selectedType,
                    decoration: const InputDecoration(labelText: 'Type'),
                    items: const [
                      DropdownMenuItem(value: 'remote', child: Text('Remote')),
                      DropdownMenuItem(
                        value: 'in-cluster',
                        child: Text('In-Cluster'),
                      ),
                    ],
                    onChanged: (val) =>
                        setState(() => selectedType = val ?? 'remote'),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: nameController,
                          decoration: const InputDecoration(
                            labelText: 'Name (e.g. prod-cluster)',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: titleController,
                          decoration: const InputDecoration(
                            labelText: 'Human Readable Title',
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (selectedType == 'remote') ...[
                    const SizedBox(height: 16),
                    TextField(
                      controller: kubeconfigController,
                      decoration: const InputDecoration(
                        labelText: 'Kubeconfig (YAML)',
                        alignLabelWithHint: true,
                      ),
                      maxLines: 10,
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  static void showEditClusterDialog(
    BuildContext context,
    WidgetRef ref,
    K8sCluster cluster,
  ) {
    final nameController = TextEditingController(text: cluster.name);
    final titleController = TextEditingController(text: cluster.title);
    final kubeconfigController = TextEditingController(
      text: cluster.kubeconfig,
    );
    String selectedType = cluster.type;

    int? selectedProjectId = cluster.project_id;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            final projectsAsync = ref.watch(projectListProvider);

            return LargeDialog(
              title: 'Edit Kubernetes Cluster',
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
                      final updatedCluster = cluster.copyWith(
                        title: titleController.text,
                        type: selectedType,
                        kubeconfig: selectedType == 'remote'
                            ? kubeconfigController.text
                            : null,
                        project_id: selectedProjectId,
                      );
                      await ref
                          .read(k8sClusterListProvider.notifier)
                          .updateCluster(updatedCluster);
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
                  DropdownButtonFormField<String>(
                    value: selectedType,
                    decoration: const InputDecoration(labelText: 'Type'),
                    items: const [
                      DropdownMenuItem(value: 'remote', child: Text('Remote')),
                      DropdownMenuItem(
                        value: 'in-cluster',
                        child: Text('In-Cluster'),
                      ),
                    ],
                    onChanged: (val) =>
                        setState(() => selectedType = val ?? 'remote'),
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
                  if (selectedType == 'remote') ...[
                    const SizedBox(height: 16),
                    TextField(
                      controller: kubeconfigController,
                      decoration: const InputDecoration(
                        labelText: 'Kubeconfig (YAML)',
                        alignLabelWithHint: true,
                      ),
                      maxLines: 10,
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _ClustersList extends ConsumerWidget {
  final List<K8sCluster> clusters;

  const _ClustersList({required this.clusters});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (clusters.isEmpty) {
      return const Center(child: Text('No Kubernetes clusters found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(20),
      itemCount: clusters.length,
      itemBuilder: (context, index) {
        final cluster = clusters[index];

        return Card(
          margin: const EdgeInsets.only(bottom: 15),
          child: ListTile(
            leading: const FaIcon(
              FontAwesomeIcons.dharmachakra,
              color: Colors.blue,
            ),
            title: Text(cluster.title),
            subtitle: Text('${cluster.name} (${cluster.type})'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                ProjectPill(projectId: cluster.project_id),
                IconButton(
                  icon: const Icon(Icons.edit, color: Colors.grey),
                  onPressed: () => K8sClustersPage.showEditClusterDialog(
                    context,
                    ref,
                    cluster,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _confirmDelete(context, cluster),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _confirmDelete(BuildContext context, K8sCluster cluster) {
    showDialog(
      context: context,
      builder: (context) => Consumer(
        builder: (context, ref, _) => AlertDialog(
          title: const Text('Delete Cluster'),
          content: Text('Delete "${cluster.title}"?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () async {
                try {
                  await ref
                      .read(k8sClusterListProvider.notifier)
                      .deleteCluster(cluster.id!);
                  if (context.mounted) Navigator.pop(context);
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Error deleting cluster: $e')),
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
