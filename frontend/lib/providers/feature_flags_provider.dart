import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../config/settings.dart';
import '../models/feature_flags.dart';

final featureFlagsProvider = FutureProvider<FeatureFlags>((ref) async {
  final response = await http.get(
    Uri.parse('${Settings.apiBaseUrl}/feature-flags'),
  );

  if (response.statusCode == 200) {
    return FeatureFlags.fromJson(jsonDecode(response.body));
  } else {
    throw Exception('Failed to load feature flags');
  }
});
