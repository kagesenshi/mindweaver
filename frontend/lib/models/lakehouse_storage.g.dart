// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'lakehouse_storage.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LakehouseStorage _$LakehouseStorageFromJson(Map<String, dynamic> json) =>
    LakehouseStorage(
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
      parameters: json['parameters'] as Map<String, dynamic>,
    );

Map<String, dynamic> _$LakehouseStorageToJson(LakehouseStorage instance) =>
    <String, dynamic>{
      'id': instance.id,
      'uuid': instance.uuid,
      'created': instance.created?.toIso8601String(),
      'modified': instance.modified?.toIso8601String(),
      'name': instance.name,
      'title': instance.title,
      'project_id': instance.project_id,
      'parameters': instance.parameters,
    };
