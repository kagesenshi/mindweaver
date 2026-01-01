import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/settings.dart';
import '../models/api_response.dart';

class APIClient {
  final String baseUrl;
  final int timeout;
  final Map<String, String> _headers = {'Content-Type': 'application/json'};

  APIClient({String? baseUrl, int? timeout})
    : baseUrl = baseUrl ?? Settings.apiBaseUrl,
      timeout = timeout ?? Settings.apiTimeout;

  void setToken(String? token) {
    if (token != null) {
      _headers['Authorization'] = 'Bearer $token';
    } else {
      _headers.remove('Authorization');
    }
  }

  void setHeader(String key, String value) {
    _headers[key] = value;
  }

  void removeHeader(String key) {
    _headers.remove(key);
  }

  Future<List<T>> listAll<T>(
    String endpoint,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl$endpoint'),
          headers: {..._headers, ...?headers},
        )
        .timeout(Duration(milliseconds: timeout));

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to load records: ${response.statusCode} ${response.body}',
      );
    }

    final data = jsonDecode(response.body);
    final List<dynamic> records = data['records'] ?? [];
    return records.map((e) => fromJsonT(e)).toList();
  }

  Future<APIResponse<T>> get<T>(
    String endpoint,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl$endpoint'),
          headers: {..._headers, ...?headers},
        )
        .timeout(Duration(milliseconds: timeout));

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to get record: ${response.statusCode} ${response.body}',
      );
    }

    return APIResponse<T>.fromJson(jsonDecode(response.body), fromJsonT);
  }

  Future<APIResponse<T>> post<T>(
    String endpoint,
    dynamic data,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl$endpoint'),
          headers: {..._headers, ...?headers},
          body: jsonEncode(data),
        )
        .timeout(Duration(milliseconds: timeout));

    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception(
        'Failed to create record: ${response.statusCode} ${response.body}',
      );
    }

    return APIResponse<T>.fromJson(jsonDecode(response.body), fromJsonT);
  }

  Future<APIResponse<T>> put<T>(
    String endpoint,
    dynamic data,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    final response = await http
        .put(
          Uri.parse('$baseUrl$endpoint'),
          headers: {..._headers, ...?headers},
          body: jsonEncode(data),
        )
        .timeout(Duration(milliseconds: timeout));

    if (response.statusCode != 200) {
      throw Exception(
        'Failed to update record: ${response.statusCode} ${response.body}',
      );
    }

    return APIResponse<T>.fromJson(jsonDecode(response.body), fromJsonT);
  }

  Future<bool> delete(String endpoint, {Map<String, String>? headers}) async {
    final response = await http
        .delete(
          Uri.parse('$baseUrl$endpoint'),
          headers: {..._headers, ...?headers},
        )
        .timeout(Duration(milliseconds: timeout));

    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception(
        'Failed to delete record: ${response.statusCode} ${response.body}',
      );
    }

    final data = jsonDecode(response.body);
    if (data['status'] != 'success') {
      throw Exception(
        'Failed to delete record: ${data['detail'] ?? 'Unknown error'}',
      );
    }
    return true;
  }
}
