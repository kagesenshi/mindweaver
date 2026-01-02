// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'k8s_cluster.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

K8sCluster _$K8sClusterFromJson(Map<String, dynamic> json) => K8sCluster(
  id: (json['id'] as num?)?.toInt(),
  uuid: json['uuid'] as String?,
  created: json['created'] == null
      ? null
      : DateTime.parse(json['created'] as String),
  modified: json['modified'] == null
      ? null
      : DateTime.parse(json['modified'] as String),
  name: json['name'] as String,
  title: json['title'] as String,
  type: json['type'] as String,
  kubeconfig: json['kubeconfig'] as String?,
  project_id: (json['project_id'] as num?)?.toInt(),
);

Map<String, dynamic> _$K8sClusterToJson(K8sCluster instance) =>
    <String, dynamic>{
      'id': instance.id,
      'uuid': instance.uuid,
      'created': instance.created?.toIso8601String(),
      'modified': instance.modified?.toIso8601String(),
      'name': instance.name,
      'title': instance.title,
      'type': instance.type,
      'kubeconfig': instance.kubeconfig,
      'project_id': instance.project_id,
    };
