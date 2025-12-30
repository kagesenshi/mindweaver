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

  factory KnowledgeDB.fromJson(Map<String, dynamic> json) =>
      _$KnowledgeDBFromJson(json);
  Map<String, dynamic> toJson() => _$KnowledgeDBToJson(this);
}
