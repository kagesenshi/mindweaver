// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'feature_flags.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

FeatureFlags _$FeatureFlagsFromJson(Map<String, dynamic> json) => FeatureFlags(
  experimentalDataSource: json['experimental_data_source'] as bool? ?? false,
  experimentalKnowledgeDb: json['experimental_knowledge_db'] as bool? ?? false,
  experimentalLakehouseStorage:
      json['experimental_lakehouse_storage'] as bool? ?? false,
  experimentalIngestion: json['experimental_ingestion'] as bool? ?? false,
);

Map<String, dynamic> _$FeatureFlagsToJson(FeatureFlags instance) =>
    <String, dynamic>{
      'experimental_data_source': instance.experimentalDataSource,
      'experimental_knowledge_db': instance.experimentalKnowledgeDb,
      'experimental_lakehouse_storage': instance.experimentalLakehouseStorage,
      'experimental_ingestion': instance.experimentalIngestion,
    };
