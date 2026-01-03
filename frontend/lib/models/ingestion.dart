import 'package:json_annotation/json_annotation.dart';

part 'ingestion.g.dart';

@JsonSerializable()
class Ingestion {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int? project_id;
  final int data_source_id;
  final int s3_storage_id;
  final String storage_path;
  final String cron_schedule;
  final DateTime? start_date;
  final DateTime? end_date;
  final String timezone;
  final String ingestion_type;
  final Map<String, dynamic> config;

  Ingestion({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    required this.data_source_id,
    required this.s3_storage_id,
    required this.storage_path,
    required this.cron_schedule,
    this.start_date,
    this.end_date,
    this.timezone = 'UTC',
    required this.ingestion_type,
    required this.config,
  });

  Ingestion copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    int? data_source_id,
    int? s3_storage_id,
    String? storage_path,
    String? cron_schedule,
    DateTime? start_date,
    DateTime? end_date,
    String? timezone,
    String? ingestion_type,
    Map<String, dynamic>? config,
  }) {
    return Ingestion(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      project_id: project_id ?? this.project_id,
      data_source_id: data_source_id ?? this.data_source_id,
      s3_storage_id: s3_storage_id ?? this.s3_storage_id,
      storage_path: storage_path ?? this.storage_path,
      cron_schedule: cron_schedule ?? this.cron_schedule,
      start_date: start_date ?? this.start_date,
      end_date: end_date ?? this.end_date,
      timezone: timezone ?? this.timezone,
      ingestion_type: ingestion_type ?? this.ingestion_type,
      config: config ?? this.config,
    );
  }

  factory Ingestion.fromJson(Map<String, dynamic> json) =>
      _$IngestionFromJson(json);
  Map<String, dynamic> toJson() => _$IngestionToJson(this);
}

@JsonSerializable()
class IngestionRun {
  final int? id;
  final int ingestion_id;
  final String status;
  final DateTime? started_at;
  final DateTime? completed_at;
  final int records_processed;
  final String? error_message;
  final Map<String, dynamic> watermark_metadata;

  IngestionRun({
    this.id,
    required this.ingestion_id,
    required this.status,
    this.started_at,
    this.completed_at,
    this.records_processed = 0,
    this.error_message,
    this.watermark_metadata = const {},
  });

  factory IngestionRun.fromJson(Map<String, dynamic> json) =>
      _$IngestionRunFromJson(json);
  Map<String, dynamic> toJson() => _$IngestionRunToJson(this);
}
