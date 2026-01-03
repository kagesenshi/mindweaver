import '../models/form_schema.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/api_providers.dart';

class FormService {
  final Ref _ref;

  FormService(this._ref);

  Future<FormSchema> getCreateForm(String entityPath) async {
    final client = _ref.read(apiClientProvider);
    final response = await client.get<FormSchema>(
      '$entityPath/+create-form',
      (json) => FormSchema.fromJson(json as Map<String, dynamic>),
    );
    if (response.record == null) {
      throw Exception('Form schema not found');
    }
    return response.record!;
  }

  Future<FormSchema> getEditForm(String entityPath) async {
    final client = _ref.read(apiClientProvider);
    final response = await client.get<FormSchema>(
      '$entityPath/+edit-form',
      (json) => FormSchema.fromJson(json as Map<String, dynamic>),
    );
    if (response.record == null) {
      throw Exception('Form schema not found');
    }
    return response.record!;
  }
}

final formServiceProvider = Provider<FormService>((ref) {
  return FormService(ref);
});
