import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/record.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';

  Future<WordRecord?> getRandomRecord(String lang) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/records/random?language_code=$lang'));
      if (response.statusCode == 200) {
        return WordRecord.fromJson(jsonDecode(response.body));
      }
    } catch (e) {
      print('API Error: $e');
    }
    return null;
  }

  Future<bool> registerVote(int userId, int recordId, String action) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/vote?user_id=$userId&record_id=$recordId&action=$action'),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Vote Error: $e');
    }
    return false;
  }
}
