import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';
import 'project_provider.dart';
import 'auth_provider.dart';

final apiClientProvider = Provider((ref) {
  final client = APIClient(getToken: ref.read(authProvider.notifier).getToken);
  final project = ref.watch(currentProjectProvider);
  if (project != null) {
    client.setHeader('X-Project-Id', project.id.toString());
  } else {
    client.removeHeader('X-Project-Id');
  }
  return client;
});
