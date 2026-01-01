import 'package:mindweaver_flutter/models/api_response.dart';
import 'package:mindweaver_flutter/services/api_client.dart';

class MockApiClient implements APIClient {
  String? lastMethod;
  String? lastEndpoint;
  dynamic lastBody;
  dynamic mockResponse;
  bool shouldThrowError = false;

  @override
  String get baseUrl => 'http://mock-api';

  @override
  int get timeout => 1000;

  @override
  void setHeader(String key, String value) {}

  @override
  void removeHeader(String key) {}

  @override
  void setToken(String? token) {}

  void setMockResponse(dynamic response) {
    mockResponse = response;
    shouldThrowError = false;
  }

  void setError() {
    shouldThrowError = true;
  }

  @override
  Future<List<T>> listAll<T>(
    String endpoint,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    lastMethod = 'GET_LIST';
    lastEndpoint = endpoint;
    lastBody = null;

    if (shouldThrowError) {
      throw Exception('Mock Error');
    }

    if (mockResponse != null) {
      if (mockResponse is List) {
        return (mockResponse as List).map((e) => fromJsonT(e)).toList();
      }
    }
    return [];
  }

  @override
  Future<APIResponse<T>> get<T>(
    String endpoint,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    lastMethod = 'GET';
    lastEndpoint = endpoint;
    lastBody = null;

    if (shouldThrowError) {
      throw Exception('Mock Error');
    }

    return APIResponse<T>(status: "success", record: fromJsonT(mockResponse));
  }

  @override
  Future<APIResponse<T>> post<T>(
    String endpoint,
    dynamic data,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    lastMethod = 'POST';
    lastEndpoint = endpoint;
    lastBody = data;

    if (shouldThrowError) {
      throw Exception('Mock Error');
    }

    // For test connection which returns Map<String, dynamic> directly (wrapped in record)
    if (endpoint.endsWith('/test_connection')) {
      // Ideally the notifier expects the record to be the response map
      // The real client returns APIResponse<T>, so we should return that.
      // The notifier calls .record! on it.
      return APIResponse<T>(
        status: "success",
        record: fromJsonT(mockResponse ?? {'status': 'success'}),
      );
    }

    return APIResponse<T>(
      status: "success",
      record: fromJsonT(mockResponse ?? data),
    );
  }

  @override
  Future<APIResponse<T>> put<T>(
    String endpoint,
    dynamic data,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    lastMethod = 'PUT';
    lastEndpoint = endpoint;
    lastBody = data;

    if (shouldThrowError) {
      throw Exception('Mock Error');
    }

    return APIResponse<T>(
      status: "success",
      record: fromJsonT(mockResponse ?? data),
    );
  }

  @override
  Future<bool> delete(String endpoint, {Map<String, String>? headers}) async {
    lastMethod = 'DELETE';
    lastEndpoint = endpoint;
    lastBody = null;

    if (shouldThrowError) {
      throw Exception('Mock Error');
    }

    return true;
  }
}
