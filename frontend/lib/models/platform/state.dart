import 'package:json_annotation/json_annotation.dart';

part 'state.g.dart';

@JsonSerializable()
class PlatformState {
  final int platform_id;
  final String status; // online, offline, pending, error
  final bool active;
  final String? message;
  final DateTime? last_heartbeat;
  final Map<String, dynamic>? extra_data;

  PlatformState({
    required this.platform_id,
    required this.status,
    required this.active,
    this.message,
    this.last_heartbeat,
    this.extra_data,
  });

  factory PlatformState.fromJson(Map<String, dynamic> json) =>
      _$PlatformStateFromJson(json);
  Map<String, dynamic> toJson() => _$PlatformStateToJson(this);
}
