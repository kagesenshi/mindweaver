// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'form_schema.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FormSchema _$FormSchemaFromJson(Map<String, dynamic> json) => FormSchema(
  jsonschema: json['jsonschema'] as Map<String, dynamic>,
  widgets: (json['widgets'] as Map<String, dynamic>).map(
    (k, e) => MapEntry(k, WidgetMetadata.fromJson(e as Map<String, dynamic>)),
  ),
  immutable_fields: (json['immutable_fields'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
  internal_fields: (json['internal_fields'] as List<dynamic>)
      .map((e) => e as String)
      .toList(),
);

Map<String, dynamic> _$FormSchemaToJson(FormSchema instance) =>
    <String, dynamic>{
      'jsonschema': instance.jsonschema,
      'widgets': instance.widgets,
      'immutable_fields': instance.immutable_fields,
      'internal_fields': instance.internal_fields,
    };

WidgetMetadata _$WidgetMetadataFromJson(Map<String, dynamic> json) =>
    WidgetMetadata(
      type: json['type'] as String,
      label: json['label'] as String?,
      endpoint: json['endpoint'] as String?,
      field: json['field'] as String?,
      multiselect: json['multiselect'] as bool?,
      min: (json['min'] as num?)?.toDouble(),
      max: (json['max'] as num?)?.toDouble(),
      defaultValue: json['defaultValue'],
      options: (json['options'] as List<dynamic>?)
          ?.map((e) => SelectOption.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$WidgetMetadataToJson(WidgetMetadata instance) =>
    <String, dynamic>{
      'type': instance.type,
      'label': instance.label,
      'endpoint': instance.endpoint,
      'field': instance.field,
      'multiselect': instance.multiselect,
      'min': instance.min,
      'max': instance.max,
      'defaultValue': instance.defaultValue,
      'options': instance.options,
    };

SelectOption _$SelectOptionFromJson(Map<String, dynamic> json) => SelectOption(
  value: json['value'] as String,
  label: json['label'] as String,
);

Map<String, dynamic> _$SelectOptionToJson(SelectOption instance) =>
    <String, dynamic>{'value': instance.value, 'label': instance.label};
