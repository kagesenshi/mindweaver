import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/form_schema.dart';
import '../services/form_service.dart';

final createFormSchemaProvider = FutureProvider.family<FormSchema, String>((
  ref,
  entityPath,
) async {
  final formService = ref.read(formServiceProvider);
  return formService.getCreateForm(entityPath);
});

final editFormSchemaProvider = FutureProvider.family<FormSchema, String>((
  ref,
  entityPath,
) async {
  final formService = ref.read(formServiceProvider);
  return formService.getEditForm(entityPath);
});
