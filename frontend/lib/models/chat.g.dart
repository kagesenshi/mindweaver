// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'chat.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Chat _$ChatFromJson(Map<String, dynamic> json) => Chat(
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
  messages: (json['messages'] as List<dynamic>)
      .map((e) => e as Map<String, dynamic>)
      .toList(),
  agent_id: json['agent_id'] as String?,
);

Map<String, dynamic> _$ChatToJson(Chat instance) => <String, dynamic>{
  'id': instance.id,
  'uuid': instance.uuid,
  'created': instance.created?.toIso8601String(),
  'modified': instance.modified?.toIso8601String(),
  'name': instance.name,
  'title': instance.title,
  'project_id': instance.project_id,
  'messages': instance.messages,
  'agent_id': instance.agent_id,
};
