import 'package:json_annotation/json_annotation.dart';

part 'api_response.g.dart';

@JsonSerializable(genericArgumentFactories: true)
class APIResponse<T> {
  final String status;
  final String? detail;
  final T? record;
  final List<T>? records;
  final Map<String, dynamic>? meta;

  APIResponse({
    required this.status,
    this.detail,
    this.record,
    this.records,
    this.meta,
  });

  factory APIResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object? json) fromJsonT,
  ) => _$APIResponseFromJson(json, fromJsonT);

  Map<String, dynamic> toJson(Object? Function(T value) toJsonT) =>
      _$APIResponseToJson(this, toJsonT);
}
