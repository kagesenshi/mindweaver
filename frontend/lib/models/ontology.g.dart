// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ontology.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

EntityAttribute _$EntityAttributeFromJson(Map<String, dynamic> json) =>
    EntityAttribute(
      id: (json['id'] as num?)?.toInt(),
      name: json['name'] as String,
      data_type: json['data_type'] as String? ?? "string",
      required: json['required'] as bool? ?? false,
    );

Map<String, dynamic> _$EntityAttributeToJson(EntityAttribute instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'data_type': instance.data_type,
      'required': instance.required,
    };

RelationshipAttribute _$RelationshipAttributeFromJson(
  Map<String, dynamic> json,
) => RelationshipAttribute(
  id: (json['id'] as num?)?.toInt(),
  name: json['name'] as String,
  data_type: json['data_type'] as String? ?? "string",
  required: json['required'] as bool? ?? false,
);

Map<String, dynamic> _$RelationshipAttributeToJson(
  RelationshipAttribute instance,
) => <String, dynamic>{
  'id': instance.id,
  'name': instance.name,
  'data_type': instance.data_type,
  'required': instance.required,
};

EntityType _$EntityTypeFromJson(Map<String, dynamic> json) => EntityType(
  id: (json['id'] as num?)?.toInt(),
  name: json['name'] as String,
  description: json['description'] as String? ?? "",
  attributes: (json['attributes'] as List<dynamic>)
      .map((e) => EntityAttribute.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$EntityTypeToJson(EntityType instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'attributes': instance.attributes,
    };

RelationshipType _$RelationshipTypeFromJson(Map<String, dynamic> json) =>
    RelationshipType(
      id: (json['id'] as num?)?.toInt(),
      name: json['name'] as String,
      description: json['description'] as String? ?? "",
      source_entity_type: json['source_entity_type'] as String? ?? "",
      target_entity_type: json['target_entity_type'] as String? ?? "",
      attributes: (json['attributes'] as List<dynamic>)
          .map((e) => RelationshipAttribute.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$RelationshipTypeToJson(RelationshipType instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'source_entity_type': instance.source_entity_type,
      'target_entity_type': instance.target_entity_type,
      'attributes': instance.attributes,
    };

Ontology _$OntologyFromJson(Map<String, dynamic> json) => Ontology(
  id: (json['id'] as num?)?.toInt(),
  uuid: json['uuid'] as String?,
  created: json['created'] == null
      ? null
      : DateTime.parse(json['created'] as String),
  modified: json['modified'] == null
      ? null
      : DateTime.parse(json['modified'] as String),
  name: json['name'] as String,
  title: json['title'] as String,
  project_id: (json['project_id'] as num?)?.toInt(),
  description: json['description'] as String? ?? "",
  entity_types: (json['entity_types'] as List<dynamic>?)
      ?.map((e) => EntityType.fromJson(e as Map<String, dynamic>))
      .toList(),
  relationship_types: (json['relationship_types'] as List<dynamic>?)
      ?.map((e) => RelationshipType.fromJson(e as Map<String, dynamic>))
      .toList(),
);

Map<String, dynamic> _$OntologyToJson(Ontology instance) => <String, dynamic>{
  'id': instance.id,
  'uuid': instance.uuid,
  'created': instance.created?.toIso8601String(),
  'modified': instance.modified?.toIso8601String(),
  'name': instance.name,
  'title': instance.title,
  'project_id': instance.project_id,
  'description': instance.description,
  'entity_types': instance.entity_types,
  'relationship_types': instance.relationship_types,
};
