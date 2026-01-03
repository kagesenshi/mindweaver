// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ingestion.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Ingestion _$IngestionFromJson(Map<String, dynamic> json) => Ingestion(
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
  data_source_id: (json['data_source_id'] as num).toInt(),
  s3_storage_id: (json['s3_storage_id'] as num).toInt(),
  storage_path: json['storage_path'] as String,
  cron_schedule: json['cron_schedule'] as String,
  start_date: json['start_date'] == null
      ? null
      : DateTime.parse(json['start_date'] as String),
  end_date: json['end_date'] == null
      ? null
      : DateTime.parse(json['end_date'] as String),
  timezone: json['timezone'] as String? ?? 'UTC',
  ingestion_type: json['ingestion_type'] as String,
  config: json['config'] as Map<String, dynamic>,
);

Map<String, dynamic> _$IngestionToJson(Ingestion instance) => <String, dynamic>{
  'id': instance.id,
  'uuid': instance.uuid,
  'created': instance.created?.toIso8601String(),
  'modified': instance.modified?.toIso8601String(),
  'name': instance.name,
  'title': instance.title,
  'project_id': instance.project_id,
  'data_source_id': instance.data_source_id,
  's3_storage_id': instance.s3_storage_id,
  'storage_path': instance.storage_path,
  'cron_schedule': instance.cron_schedule,
  'start_date': instance.start_date?.toIso8601String(),
  'end_date': instance.end_date?.toIso8601String(),
  'timezone': instance.timezone,
  'ingestion_type': instance.ingestion_type,
  'config': instance.config,
};

IngestionRun _$IngestionRunFromJson(Map<String, dynamic> json) => IngestionRun(
  id: (json['id'] as num?)?.toInt(),
  ingestion_id: (json['ingestion_id'] as num).toInt(),
  status: json['status'] as String,
  started_at: json['started_at'] == null
      ? null
      : DateTime.parse(json['started_at'] as String),
  completed_at: json['completed_at'] == null
      ? null
      : DateTime.parse(json['completed_at'] as String),
  records_processed: (json['records_processed'] as num?)?.toInt() ?? 0,
  error_message: json['error_message'] as String?,
  watermark_metadata:
      json['watermark_metadata'] as Map<String, dynamic>? ?? const {},
);

Map<String, dynamic> _$IngestionRunToJson(IngestionRun instance) =>
    <String, dynamic>{
      'id': instance.id,
      'ingestion_id': instance.ingestion_id,
      'status': instance.status,
      'started_at': instance.started_at?.toIso8601String(),
      'completed_at': instance.completed_at?.toIso8601String(),
      'records_processed': instance.records_processed,
      'error_message': instance.error_message,
      'watermark_metadata': instance.watermark_metadata,
    };
