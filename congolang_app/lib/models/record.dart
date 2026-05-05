class WordRecord {
  final int id;
  final String languageCode;
  final String regionTarget;
  final String normalizedText;
  final String registerType;

  WordRecord({
    required this.id,
    required this.languageCode,
    required this.regionTarget,
    required this.normalizedText,
    required this.registerType,
  });

  factory WordRecord.fromJson(Map<String, dynamic> json) {
    return WordRecord(
      id: json['id'],
      languageCode: json['language_code'],
      regionTarget: json['region_target'],
      normalizedText: json['normalized_text'],
      registerType: json['register_type'],
    );
  }
}
