import 'package:json_annotation/json_annotation.dart';

part 'feature_flags.g.dart';

@JsonSerializable()
class FeatureFlags {
  @JsonKey(name: 'experimental_data_source')
  final bool experimentalDataSource;
  @JsonKey(name: 'experimental_knowledge_db')
  final bool experimentalKnowledgeDb;
  @JsonKey(name: 'experimental_lakehouse_storage')
  final bool experimentalLakehouseStorage;
  @JsonKey(name: 'experimental_ingestion')
  final bool experimentalIngestion;

  FeatureFlags({
    this.experimentalDataSource = false,
    this.experimentalKnowledgeDb = false,
    this.experimentalLakehouseStorage = false,
    this.experimentalIngestion = false,
  });

  factory FeatureFlags.fromJson(Map<String, dynamic> json) =>
      _$FeatureFlagsFromJson(json);

  Map<String, dynamic> toJson() => _$FeatureFlagsToJson(this);
}
