import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/record.dart';

final swipeProvider = StateNotifierProvider<SwipeNotifier, List<WordRecord>>((ref) {
  return SwipeNotifier();
});

class SwipeNotifier extends StateNotifier<List<WordRecord>> {
  SwipeNotifier() : super([]);

  void addRecord(WordRecord record) {
    state = [...state, record];
  }

  void removeRecord(int id) {
    state = state.where((r) => r.id != id).toList();
  }
}

final userTrustScoreProvider = StateProvider<double>((ref) => 0.96);
final userXPProvider = StateProvider<int>((ref) => 4520);
