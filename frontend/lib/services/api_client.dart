import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/settings.dart';
import '../models/api_response.dart';

class APIClient {
  final String baseUrl;
  final int timeout;
  final Map<String, String> _headers = {'Content-Type': 'application/json'};

  final Future<String?> Function()? getToken;

  APIClient({String? baseUrl, int? timeout, this.getToken})
    : baseUrl = baseUrl ?? Settings.apiBaseUrl,
      timeout = timeout ?? Settings.apiTimeout;

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
    final headersMap = {..._headers, ...?headers};
    if (getToken != null) {
      final token = await getToken!();
      if (token != null) headersMap['Authorization'] = 'Bearer $token';
    }

    final response = await http
        .get(Uri.parse('$baseUrl$endpoint'), headers: headersMap)
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
    final headersMap = {..._headers, ...?headers};
    if (getToken != null) {
      final token = await getToken!();
      if (token != null) headersMap['Authorization'] = 'Bearer $token';
    }

    final response = await http
        .get(Uri.parse('$baseUrl$endpoint'), headers: headersMap)
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
    final headersMap = {..._headers, ...?headers};
    if (getToken != null) {
      final token = await getToken!();
      if (token != null) headersMap['Authorization'] = 'Bearer $token';
    }

    final response = await http
        .post(
          Uri.parse('$baseUrl$endpoint'),
          headers: headersMap,
          body: jsonEncode(data),
        )
        .timeout(Duration(milliseconds: timeout));

    return APIResponse<T>.fromJson(jsonDecode(response.body), fromJsonT);
  }

  Future<Map<String, dynamic>> postRaw(
    String endpoint,
    dynamic data, {
    Map<String, String>? headers,
  }) async {
    final headersMap = {..._headers, ...?headers};
    if (getToken != null) {
      final token = await getToken!();
      if (token != null) headersMap['Authorization'] = 'Bearer $token';
    }

    final response = await http
        .post(
          Uri.parse('$baseUrl$endpoint'),
          headers: headersMap,
          body: jsonEncode(data),
        )
        .timeout(Duration(milliseconds: timeout));

    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception(
        'Request failed: ${response.statusCode} ${response.body}',
      );
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<APIResponse<T>> put<T>(
    String endpoint,
    dynamic data,
    T Function(Object? json) fromJsonT, {
    Map<String, String>? headers,
  }) async {
    final headersMap = {..._headers, ...?headers};
    if (getToken != null) {
      final token = await getToken!();
      if (token != null) headersMap['Authorization'] = 'Bearer $token';
    }

    final response = await http
        .put(
          Uri.parse('$baseUrl$endpoint'),
          headers: headersMap,
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
    final headersMap = {..._headers, ...?headers};
    if (getToken != null) {
      final token = await getToken!();
      if (token != null) headersMap['Authorization'] = 'Bearer $token';
    }

    final response = await http
        .delete(Uri.parse('$baseUrl$endpoint'), headers: headersMap)
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
