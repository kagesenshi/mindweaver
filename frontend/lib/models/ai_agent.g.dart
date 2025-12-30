// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ai_agent.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AIAgent _$AIAgentFromJson(Map<String, dynamic> json) => AIAgent(
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
  model: json['model'] as String? ?? "gpt-4-turbo",
  temperature: (json['temperature'] as num?)?.toDouble() ?? 0.7,
  system_prompt: json['system_prompt'] as String? ?? "",
  status: json['status'] as String? ?? "Inactive",
  knowledge_db_ids: (json['knowledge_db_ids'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$AIAgentToJson(AIAgent instance) => <String, dynamic>{
  'id': instance.id,
  'uuid': instance.uuid,
  'created': instance.created?.toIso8601String(),
  'modified': instance.modified?.toIso8601String(),
  'name': instance.name,
  'title': instance.title,
  'project_id': instance.project_id,
  'model': instance.model,
  'temperature': instance.temperature,
  'system_prompt': instance.system_prompt,
  'status': instance.status,
  'knowledge_db_ids': instance.knowledge_db_ids,
};
