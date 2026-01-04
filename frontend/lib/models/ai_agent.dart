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
  final List<int> knowledge_db_ids;

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

  AIAgent copyWith({
    int? id,
    String? uuid,
    DateTime? created,
    DateTime? modified,
    String? name,
    String? title,
    int? project_id,
    String? model,
    double? temperature,
    String? system_prompt,
    String? status,
    List<int>? knowledge_db_ids,
  }) {
    return AIAgent(
      id: id ?? this.id,
      uuid: uuid ?? this.uuid,
      created: created ?? this.created,
      modified: modified ?? this.modified,
      name: name ?? this.name,
      title: title ?? this.title,
      project_id: project_id ?? this.project_id,
      model: model ?? this.model,
      temperature: temperature ?? this.temperature,
      system_prompt: system_prompt ?? this.system_prompt,
      status: status ?? this.status,
      knowledge_db_ids: knowledge_db_ids ?? this.knowledge_db_ids,
    );
  }

  factory AIAgent.fromJson(Map<String, dynamic> json) =>
      _$AIAgentFromJson(json);
  Map<String, dynamic> toJson() => _$AIAgentToJson(this);
}
