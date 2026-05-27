import 'dart:convert';

import 'package:http/http.dart' as http;

class CivicApi {
  CivicApi({required this.baseUrl});

  final String baseUrl;

  Future<Map<String, dynamic>> ingestCatalog(
      {int limit = 200, int topK = 100}) async {
    final uri = Uri.parse('$baseUrl/ingest/catalog?limit=$limit&top_k=$topK');
    final response = await http.post(uri);
    _ensureOk(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> searchDatasets(String query) async {
    final uri = Uri.parse(
        '$baseUrl/datasets/search?query=${Uri.encodeQueryComponent(query)}&limit=10');
    final response = await http.get(uri);
    _ensureOk(response);
    final payload = jsonDecode(response.body) as Map<String, dynamic>;
    return (payload['results'] as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<List<Map<String, dynamic>>> listMvpJobs() async {
    final uri = Uri.parse('$baseUrl/jobs');
    final response = await http.get(uri);
    _ensureOk(response);
    final payload = jsonDecode(response.body) as Map<String, dynamic>;
    return (payload['jobs'] as List<dynamic>)
        .map((e) => e as Map<String, dynamic>)
        .toList();
  }

  Future<Map<String, dynamic>> runJob(String jobId) async {
    final uri = Uri.parse('$baseUrl/jobs/$jobId/run?limit=10');
    final response = await http.post(uri);
    _ensureOk(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> buildGeneratedJobs({int target = 10000}) async {
    final uri = Uri.parse('$baseUrl/jobs/generated/build?target_count=$target');
    final response = await http.post(uri);
    _ensureOk(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> listGeneratedJobs(
      {int offset = 0, int limit = 20}) async {
    final uri =
        Uri.parse('$baseUrl/jobs/generated?offset=$offset&limit=$limit');
    final response = await http.get(uri);
    _ensureOk(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  void _ensureOk(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception('API error ${response.statusCode}: ${response.body}');
    }
  }
}
