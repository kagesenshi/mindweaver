import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mindweaver_flutter/providers/auth_provider.dart';
import 'package:mindweaver_flutter/providers/api_providers.dart';
import '../test/mocks/api_client_mock.dart';

void main() {
  late MockApiClient mockApiClient;

  setUp(() {
    mockApiClient = MockApiClient();
    SharedPreferences.setMockInitialValues({});
  });

  ProviderContainer createContainer() {
    return ProviderContainer(
      overrides: [apiClientProvider.overrideWithValue(mockApiClient)],
    );
  }

  Future<void> waitForInit(ProviderContainer container) async {
    while (container.read(authProvider).status == AuthStatus.loading) {
      await Future.delayed(Duration.zero);
    }
  }

  test('AuthProvider initial state is loading then unauthenticated', () async {
    final container = createContainer();
    expect(container.read(authProvider).status, AuthStatus.loading);

    await waitForInit(container);

    expect(container.read(authProvider).status, AuthStatus.unauthenticated);
  });

  test('AuthProvider login updates state and persists token', () async {
    final container = createContainer();
    await Future.microtask(() {});

    await container.read(authProvider.notifier).login('test-token');

    expect(container.read(authProvider).status, AuthStatus.authenticated);
    expect(container.read(authProvider).token, 'test-token');

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('auth_token'), 'test-token');
  });

  test('AuthProvider logout updates state and removes token', () async {
    SharedPreferences.setMockInitialValues({'auth_token': 'prev-token'});
    final container = createContainer();

    await waitForInit(container);

    expect(container.read(authProvider).status, AuthStatus.authenticated);

    await container.read(authProvider.notifier).logout();

    expect(container.read(authProvider).status, AuthStatus.unauthenticated);
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('auth_token'), null);
  });
}
