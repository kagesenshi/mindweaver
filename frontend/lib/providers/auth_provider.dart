import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

final authProvider = StateNotifierProvider<AuthNotifier, AsyncValue<User?>>((
  ref,
) {
  return AuthNotifier(ref);
});

class AuthNotifier extends StateNotifier<AsyncValue<User?>> {
  final Ref ref;
  static const _tokenKey = 'auth_token';

  AuthNotifier(this.ref) : super(const AsyncValue.loading()) {
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(_tokenKey);

      if (token == null) {
        state = const AsyncValue.data(null);
        return;
      }

      // Verify token/get user info
      // We assume ApiClient picks up the token if we set it, or we set it globally
      // But here we might not have initialized ApiClient with token yet if it's singleton
      // Let's assume we can pass header manually validation

      final client = http.Client();
      // Assuming localhost:8000 for now, should be from config
      final baseUrl = 'http://localhost:8000/api/v1';

      final response = await client.get(
        Uri.parse('$baseUrl/auth/me'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final userData = json.decode(response.body);
        final user = User.fromJson(userData);
        state = AsyncValue.data(user);
      } else {
        // Token invalid
        await logout();
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<String> getLoginUrl(String redirectUrl) async {
    // Construct backend login URL
    // http://localhost:8000/api/v1/auth/login?redirect_url=...
    const baseUrl = 'http://localhost:8000/api/v1';
    return '$baseUrl/auth/login?redirect_url=${Uri.encodeComponent(redirectUrl)}';
  }

  Future<void> handleCallback(String code, String redirectUrl) async {
    state = const AsyncValue.loading();
    try {
      final client = http.Client();
      const baseUrl = 'http://localhost:8000/api/v1';

      // Backend expects query params

      final uri = Uri.parse(
        '$baseUrl/auth/callback',
      ).replace(queryParameters: {'code': code, 'redirect_url': redirectUrl});

      final resp = await client.post(uri);

      if (resp.statusCode == 200) {
        final data = json.decode(resp.body);
        final token = data['access_token'];

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_tokenKey, token);

        // Refresh user info
        await _checkAuth();
      } else {
        throw Exception('Login failed: ${resp.body}');
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    state = const AsyncValue.data(null);
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }
}
