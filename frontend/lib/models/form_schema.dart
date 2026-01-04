import 'package:json_annotation/json_annotation.dart';

part 'form_schema.g.dart';

@JsonSerializable()
class FormSchema {
  final Map<String, dynamic> jsonschema;
  final Map<String, WidgetMetadata> widgets;
  final List<String> immutable_fields;
  final List<String> internal_fields;

  FormSchema({
    required this.jsonschema,
    required this.widgets,
    required this.immutable_fields,
    required this.internal_fields,
  });

  factory FormSchema.fromJson(Map<String, dynamic> json) =>
      _$FormSchemaFromJson(json);
  Map<String, dynamic> toJson() => _$FormSchemaToJson(this);
}

@JsonSerializable()
class WidgetMetadata {
  final String? type;
  final String? label;
  final String? endpoint;
  final String? field;
  final bool? multiselect;
  final double? min;
  final double? max;
  final dynamic defaultValue;
  final List<SelectOption>? options;
  final int? order;
  @JsonKey(name: 'column_span')
  final int? columnSpan;

  WidgetMetadata({
    required this.type,
    this.label,
    this.endpoint,
    this.field,
    this.multiselect,
    this.min,
    this.max,
    this.defaultValue,
    this.options,
    this.order,
    this.columnSpan,
  });

  factory WidgetMetadata.fromJson(Map<String, dynamic> json) =>
      _$WidgetMetadataFromJson(json);
  Map<String, dynamic> toJson() => _$WidgetMetadataToJson(this);
}

@JsonSerializable()
class SelectOption {
  final String value;
  final String label;

  SelectOption({required this.value, required this.label});

  factory SelectOption.fromJson(Map<String, dynamic> json) =>
      _$SelectOptionFromJson(json);
  Map<String, dynamic> toJson() => _$SelectOptionToJson(this);
}
