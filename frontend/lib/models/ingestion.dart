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
  final int lakehouse_storage_id;
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
    required this.lakehouse_storage_id,
    required this.storage_path,
    required this.cron_schedule,
    this.start_date,
    this.end_date,
    this.timezone = 'UTC',
    required this.ingestion_type,
    required this.config,
  });

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
