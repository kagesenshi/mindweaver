import 'package:json_annotation/json_annotation.dart';

part 'ontology.g.dart';

@JsonSerializable()
class EntityAttribute {
  final int? id;
  final String name;
  final String data_type;
  final bool required;

  EntityAttribute({
    this.id,
    required this.name,
    this.data_type = "string",
    this.required = false,
  });

  factory EntityAttribute.fromJson(Map<String, dynamic> json) =>
      _$EntityAttributeFromJson(json);
  Map<String, dynamic> toJson() => _$EntityAttributeToJson(this);
}

@JsonSerializable()
class RelationshipAttribute {
  final int? id;
  final String name;
  final String data_type;
  final bool required;

  RelationshipAttribute({
    this.id,
    required this.name,
    this.data_type = "string",
    this.required = false,
  });

  factory RelationshipAttribute.fromJson(Map<String, dynamic> json) =>
      _$RelationshipAttributeFromJson(json);
  Map<String, dynamic> toJson() => _$RelationshipAttributeToJson(this);
}

@JsonSerializable()
class EntityType {
  final int? id;
  final String name;
  final String description;
  final List<EntityAttribute> attributes;

  EntityType({
    this.id,
    required this.name,
    this.description = "",
    required this.attributes,
  });

  factory EntityType.fromJson(Map<String, dynamic> json) =>
      _$EntityTypeFromJson(json);
  Map<String, dynamic> toJson() => _$EntityTypeToJson(this);
}

@JsonSerializable()
class RelationshipType {
  final int? id;
  final String name;
  final String description;
  final String source_entity_type;
  final String target_entity_type;
  final List<RelationshipAttribute> attributes;

  RelationshipType({
    this.id,
    required this.name,
    this.description = "",
    this.source_entity_type = "",
    this.target_entity_type = "",
    required this.attributes,
  });

  factory RelationshipType.fromJson(Map<String, dynamic> json) =>
      _$RelationshipTypeFromJson(json);
  Map<String, dynamic> toJson() => _$RelationshipTypeToJson(this);
}

@JsonSerializable()
class Ontology {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int? project_id;
  final String description;
  final List<EntityType>? entity_types;
  final List<RelationshipType>? relationship_types;

  Ontology({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    this.description = "",
    this.entity_types,
    this.relationship_types,
  });

  Ontology copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    String? description,
    List<EntityType>? entity_types,
    List<RelationshipType>? relationship_types,
  }) {
    return Ontology(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      project_id: project_id ?? this.project_id,
      description: description ?? this.description,
      entity_types: entity_types ?? this.entity_types,
      relationship_types: relationship_types ?? this.relationship_types,
    );
  }

  factory Ontology.fromJson(Map<String, dynamic> json) =>
      _$OntologyFromJson(json);
  Map<String, dynamic> toJson() => _$OntologyToJson(this);
}
