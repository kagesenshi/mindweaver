// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'state.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

PlatformState _$PlatformStateFromJson(Map<String, dynamic> json) =>
    PlatformState(
      platform_id: (json['platform_id'] as num).toInt(),
      status: json['status'] as String,
      active: json['active'] as bool,
      message: json['message'] as String?,
      last_heartbeat: json['last_heartbeat'] == null
          ? null
          : DateTime.parse(json['last_heartbeat'] as String),
      extra_data: json['extra_data'] as Map<String, dynamic>?,
    );

Map<String, dynamic> _$PlatformStateToJson(PlatformState instance) =>
    <String, dynamic>{
      'platform_id': instance.platform_id,
      'status': instance.status,
      'active': instance.active,
      'message': instance.message,
      'last_heartbeat': instance.last_heartbeat?.toIso8601String(),
      'extra_data': instance.extra_data,
    };
