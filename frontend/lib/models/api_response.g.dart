// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

APIResponse<T> _$APIResponseFromJson<T>(
  Map<String, dynamic> json,
  T Function(Object? json) fromJsonT,
) => APIResponse<T>(
  status: json['status'] as String,
  detail: json['detail'] as String?,
  record: _$nullableGenericFromJson(json['record'], fromJsonT),
  records: (json['records'] as List<dynamic>?)?.map(fromJsonT).toList(),
  meta: json['meta'] as Map<String, dynamic>?,
);

Map<String, dynamic> _$APIResponseToJson<T>(
  APIResponse<T> instance,
  Object? Function(T value) toJsonT,
) => <String, dynamic>{
  'status': instance.status,
  'detail': instance.detail,
  'record': _$nullableGenericToJson(instance.record, toJsonT),
  'records': instance.records?.map(toJsonT).toList(),
  'meta': instance.meta,
};

T? _$nullableGenericFromJson<T>(
  Object? input,
  T Function(Object? json) fromJson,
) => input == null ? null : fromJson(input);

Object? _$nullableGenericToJson<T>(
  T? input,
  Object? Function(T value) toJson,
) => input == null ? null : toJson(input);
