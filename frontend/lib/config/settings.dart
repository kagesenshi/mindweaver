class Settings {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const int apiTimeout = 30000; // 30 seconds
}
