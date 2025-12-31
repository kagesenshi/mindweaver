import 'package:json_annotation/json_annotation.dart';

part 'lakehouse_storage.g.dart';

@JsonSerializable()
class LakehouseStorage {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int? project_id;
  final Map<String, dynamic> parameters;

  LakehouseStorage({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    required this.parameters,
  });

  LakehouseStorage copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    Map<String, dynamic>? parameters,
  }) {
    return LakehouseStorage(
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

  factory LakehouseStorage.fromJson(Map<String, dynamic> json) =>
      _$LakehouseStorageFromJson(json);
  Map<String, dynamic> toJson() => _$LakehouseStorageToJson(this);
}
