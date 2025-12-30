import 'package:json_annotation/json_annotation.dart';

part 'ai_agent.g.dart';

@JsonSerializable()
class AIAgent {
  final int? id;
  final String? uuid;
  final DateTime? created;
  final DateTime? modified;
  final String name;
  final String title;
  final int? project_id;
  final String model;
  final double temperature;
  final String system_prompt;
  final String status;
  final List<String> knowledge_db_ids;

  AIAgent({
    this.id,
    this.uuid,
    this.created,
    this.modified,
    required this.name,
    required this.title,
    this.project_id,
    this.model = "gpt-4-turbo",
    this.temperature = 0.7,
    this.system_prompt = "",
    this.status = "Inactive",
    required this.knowledge_db_ids,
  });

  factory AIAgent.fromJson(Map<String, dynamic> json) =>
      _$AIAgentFromJson(json);
  Map<String, dynamic> toJson() => _$AIAgentToJson(this);
}
