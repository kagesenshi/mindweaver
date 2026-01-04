import 'package:json_annotation/json_annotation.dart';

part 'pgsql.g.dart';

@JsonSerializable()
class PgSqlPlatform {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int instances;
  final String storage_size;
  final String? backup_destination;
  final String backup_retention_policy;
  final int? s3_storage_id;
  final bool enable_citus;
  final bool enable_postgis;
  final int? project_id;
  final int k8s_cluster_id;

  PgSqlPlatform({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    required this.instances,
    required this.storage_size,
    this.backup_destination,
    required this.backup_retention_policy,
    this.s3_storage_id,
    required this.enable_citus,
    required this.enable_postgis,
    this.project_id,
    required this.k8s_cluster_id,
  });

  PgSqlPlatform copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? instances,
    String? storage_size,
    String? backup_destination,
    String? backup_retention_policy,
    int? s3_storage_id,
    bool? enable_citus,
    bool? enable_postgis,
    int? project_id,
    int? k8s_cluster_id,
  }) {
    return PgSqlPlatform(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      instances: instances ?? this.instances,
      storage_size: storage_size ?? this.storage_size,
      backup_destination: backup_destination ?? this.backup_destination,
      backup_retention_policy:
          backup_retention_policy ?? this.backup_retention_policy,
      s3_storage_id: s3_storage_id ?? this.s3_storage_id,
      enable_citus: enable_citus ?? this.enable_citus,
      enable_postgis: enable_postgis ?? this.enable_postgis,
      project_id: project_id ?? this.project_id,
      k8s_cluster_id: k8s_cluster_id ?? this.k8s_cluster_id,
    );
  }

  factory PgSqlPlatform.fromJson(Map<String, dynamic> json) =>
      _$PgSqlPlatformFromJson(json);
  Map<String, dynamic> toJson() => _$PgSqlPlatformToJson(this);
}
