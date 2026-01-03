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
  final int? project_id;
  final Map<String, dynamic> parameters;

  S3Storage({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    required this.parameters,
  });

  S3Storage copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    Map<String, dynamic>? parameters,
  }) {
    return S3Storage(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      project_id: project_id ?? this.project_id,
      parameters: parameters ?? this.parameters,
    );
  }

  factory S3Storage.fromJson(Map<String, dynamic> json) =>
      _$S3StorageFromJson(json);
  Map<String, dynamic> toJson() => _$S3StorageToJson(this);
}
