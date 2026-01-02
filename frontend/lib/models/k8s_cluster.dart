import 'package:json_annotation/json_annotation.dart';

part 'k8s_cluster.g.dart';

@JsonSerializable()
class K8sCluster {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final String type;
  final String? kubeconfig;
  final int? project_id;

  K8sCluster({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    required this.type,
    this.kubeconfig,
    this.project_id,
  });

  factory K8sCluster.fromJson(Map<String, dynamic> json) =>
      _$K8sClusterFromJson(json);
  Map<String, dynamic> toJson() => _$K8sClusterToJson(this);

  K8sCluster copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    String? type,
    String? kubeconfig,
    int? project_id,
  }) {
    return K8sCluster(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      type: type ?? this.type,
      kubeconfig: kubeconfig ?? this.kubeconfig,
      project_id: project_id ?? this.project_id,
    );
  }
}
