import 'package:json_annotation/json_annotation.dart';

part 'knowledge_db.g.dart';

@JsonSerializable()
class KnowledgeDB {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int? project_id;
  final String type;
  final String description;
  final Map<String, dynamic> parameters;
  final int? ontology_id;

  KnowledgeDB({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    required this.type,
    this.description = "",
    required this.parameters,
    this.ontology_id,
  });

  KnowledgeDB copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    String? type,
    String? description,
    Map<String, dynamic>? parameters,
    int? ontology_id,
  }) {
    return KnowledgeDB(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      project_id: project_id ?? this.project_id,
      type: type ?? this.type,
      description: description ?? this.description,
      parameters: parameters ?? this.parameters,
      ontology_id: ontology_id ?? this.ontology_id,
    );
  }

  factory KnowledgeDB.fromJson(Map<String, dynamic> json) =>
      _$KnowledgeDBFromJson(json);
  Map<String, dynamic> toJson() => _$KnowledgeDBToJson(this);
}
