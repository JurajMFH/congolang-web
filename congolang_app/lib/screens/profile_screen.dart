import 'package:flutter/material.dart';
import 'package:percent_indicator/percent_indicator.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mon Profil')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const CircleAvatar(
              radius: 60,
              backgroundColor: Color(0xFFFFD700),
              child: Icon(Icons.person, size: 80, color: Colors.black),
            ),
            const SizedBox(height: 16),
            const Text(
              'Juraj_DataExpert',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const Text('Expert Linguist (Brazzaville)', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 32),
            _statRow('Points XP', '4,520', Icons.bolt, Colors.orange),
            const SizedBox(height: 16),
            _trustScoreWidget(0.96),
            const SizedBox(height: 32),
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Badges', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _badgeIcon(Icons.verified, 'Verify_Gold', Colors.amber),
                _badgeIcon(Icons.history_edu, 'Historian', Colors.green),
                _badgeIcon(Icons.map, 'Explorer', Colors.blue),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _statRow(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(15),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(icon, color: color),
              const SizedBox(width: 12),
              Text(label, style: const TextStyle(fontSize: 18)),
            ],
          ),
          Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.orange)),
        ],
      ),
    );
  }

  Widget _trustScoreWidget(double score) {
    return CircularPercentIndicator(
      radius: 80.0,
      lineWidth: 10.0,
      percent: score,
      center: Text(
        "${(score * 100).toInt()}%",
        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
      ),
      footer: const Padding(
        padding: EdgeInsets.only(top: 12.0),
        child: Text("Trust Score", style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      ),
      circularStrokeCap: CircularStrokeCap.round,
      progressColor: const Color(0xFF009543),
      backgroundColor: Colors.white12,
    );
  }

  Widget _badgeIcon(IconData icon, String label, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: color.withOpacity(0.2),
          ),
          child: Icon(icon, color: color, size: 30),
        ),
        const SizedBox(height: 8),
        Text(label, style: const TextStyle(fontSize: 12)),
      ],
    );
  }
}
