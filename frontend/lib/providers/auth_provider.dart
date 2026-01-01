import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_client.dart';
import 'api_providers.dart';

enum AuthStatus { authenticated, unauthenticated, loading }

class AuthState {
  final AuthStatus status;
  final String? token;
  final Map<String, dynamic>? user;

  AuthState({required this.status, this.token, this.user});

  factory AuthState.loading() => AuthState(status: AuthStatus.loading);
  factory AuthState.unauthenticated() =>
      AuthState(status: AuthStatus.unauthenticated);
  factory AuthState.authenticated(String token, Map<String, dynamic>? user) =>
      AuthState(status: AuthStatus.authenticated, token: token, user: user);
}

class AuthNotifier extends StateNotifier<AuthState> {
  final APIClient _apiClient;
  static const _tokenKey = 'auth_token';

  AuthNotifier(this._apiClient) : super(AuthState.loading()) {
    _init();
  }

  Future<void> _init() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_tokenKey);
    if (token != null) {
      _apiClient.setToken(token);
      // In a real app, we might want to verify the token or fetch user info here
      // For now, assume authenticated if token exists
      state = AuthState.authenticated(token, null);
    } else {
      state = AuthState.unauthenticated();
    }
  }

  Future<void> login(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    _apiClient.setToken(token);
    state = AuthState.authenticated(token, null);
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    _apiClient.setToken(null);
    state = AuthState.unauthenticated();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return AuthNotifier(apiClient);
});
