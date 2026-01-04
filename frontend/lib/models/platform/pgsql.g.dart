// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pgsql.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PgSqlPlatform _$PgSqlPlatformFromJson(Map<String, dynamic> json) =>
    PgSqlPlatform(
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
      instances: (json['instances'] as num).toInt(),
      storage_size: json['storage_size'] as String,
      backup_destination: json['backup_destination'] as String?,
      backup_retention_policy: json['backup_retention_policy'] as String,
      s3_storage_id: (json['s3_storage_id'] as num?)?.toInt(),
      enable_citus: json['enable_citus'] as bool,
      enable_postgis: json['enable_postgis'] as bool,
      project_id: (json['project_id'] as num?)?.toInt(),
      k8s_cluster_id: (json['k8s_cluster_id'] as num).toInt(),
    );

Map<String, dynamic> _$PgSqlPlatformToJson(PgSqlPlatform instance) =>
    <String, dynamic>{
      'id': instance.id,
      'uuid': instance.uuid,
      'created': instance.created?.toIso8601String(),
      'modified': instance.modified?.toIso8601String(),
      'name': instance.name,
      'title': instance.title,
      'instances': instance.instances,
      'storage_size': instance.storage_size,
      'backup_destination': instance.backup_destination,
      'backup_retention_policy': instance.backup_retention_policy,
      's3_storage_id': instance.s3_storage_id,
      'enable_citus': instance.enable_citus,
      'enable_postgis': instance.enable_postgis,
      'project_id': instance.project_id,
      'k8s_cluster_id': instance.k8s_cluster_id,
    };
