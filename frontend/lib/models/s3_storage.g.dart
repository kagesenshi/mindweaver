// GENERATED CODE - DO NOT MODIFY BY HAND

part of 's3_storage.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

S3Storage _$S3StorageFromJson(Map<String, dynamic> json) => S3Storage(
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
  region: json['region'] as String,
  access_key: json['access_key'] as String,
  secret_key: json['secret_key'] as String?,
  endpoint_url: json['endpoint_url'] as String?,
  project_id: (json['project_id'] as num?)?.toInt(),
);

Map<String, dynamic> _$S3StorageToJson(S3Storage instance) => <String, dynamic>{
  'id': instance.id,
  'uuid': instance.uuid,
  'created': instance.created?.toIso8601String(),
  'modified': instance.modified?.toIso8601String(),
  'name': instance.name,
  'title': instance.title,
  'region': instance.region,
  'access_key': instance.access_key,
  'secret_key': instance.secret_key,
  'endpoint_url': instance.endpoint_url,
  'project_id': instance.project_id,
};
