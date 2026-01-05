import 'package:json_annotation/json_annotation.dart';

part 's3_storage.g.dart';

@JsonSerializable()
class S3Storage {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final String region;
  final String access_key;
  final String? secret_key;
  final String? endpoint_url;
  final int? project_id;

  S3Storage({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    required this.region,
    required this.access_key,
    this.secret_key,
    this.endpoint_url,
    this.project_id,
  });

  S3Storage copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    String? region,
    String? access_key,
    String? secret_key,
    String? endpoint_url,
    int? project_id,
  }) {
    return S3Storage(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      region: region ?? this.region,
      access_key: access_key ?? this.access_key,
      secret_key: secret_key ?? this.secret_key,
      endpoint_url: endpoint_url ?? this.endpoint_url,
      project_id: project_id ?? this.project_id,
    );
  }

  factory S3Storage.fromJson(Map<String, dynamic> json) =>
      _$S3StorageFromJson(json);
  Map<String, dynamic> toJson() => _$S3StorageToJson(this);
}
