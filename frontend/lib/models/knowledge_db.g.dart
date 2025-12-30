// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'knowledge_db.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

KnowledgeDB _$KnowledgeDBFromJson(Map<String, dynamic> json) => KnowledgeDB(
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
  project_id: (json['project_id'] as num?)?.toInt(),
  type: json['type'] as String,
  description: json['description'] as String? ?? "",
  parameters: json['parameters'] as Map<String, dynamic>,
  ontology_id: (json['ontology_id'] as num?)?.toInt(),
);

Map<String, dynamic> _$KnowledgeDBToJson(KnowledgeDB instance) =>
    <String, dynamic>{
      'id': instance.id,
      'uuid': instance.uuid,
      'created': instance.created?.toIso8601String(),
      'modified': instance.modified?.toIso8601String(),
      'name': instance.name,
      'title': instance.title,
      'project_id': instance.project_id,
      'type': instance.type,
      'description': instance.description,
      'parameters': instance.parameters,
      'ontology_id': instance.ontology_id,
    };
