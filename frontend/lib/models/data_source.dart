import 'package:json_annotation/json_annotation.dart';

part 'data_source.g.dart';

@JsonSerializable()
class DataSource {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int? project_id;
  final String type;
  final Map<String, dynamic> parameters;

  DataSource({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    required this.type,
    required this.parameters,
  });

  DataSource copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    String? type,
    Map<String, dynamic>? parameters,
  }) {
    return DataSource(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      project_id: project_id ?? this.project_id,
      type: type ?? this.type,
      parameters: parameters ?? this.parameters,
    );
  }

  factory DataSource.fromJson(Map<String, dynamic> json) =>
      _$DataSourceFromJson(json);
  Map<String, dynamic> toJson() => _$DataSourceToJson(this);
}
