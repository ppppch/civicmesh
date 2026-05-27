import 'package:flutter/material.dart';

class ComputeScreen extends StatelessWidget {
  const ComputeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Civic Compute',
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700)),
          SizedBox(height: 8),
          Text(
            'Mobile compute mode will run local embedding and verification workloads. '
            'This Flutter shell is wired to job APIs first; next phase adds local model runtime.',
          ),
        ],
      ),
    );
  }
}
