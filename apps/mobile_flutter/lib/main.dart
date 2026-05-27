import 'package:flutter/material.dart';

import 'api.dart';
import 'screens/ask_screen.dart';
import 'screens/compute_screen.dart';
import 'screens/jobs_screen.dart';

void main() {
  runApp(const CivicGridMobileApp());
}

class CivicGridMobileApp extends StatefulWidget {
  const CivicGridMobileApp({super.key});

  @override
  State<CivicGridMobileApp> createState() => _CivicGridMobileAppState();
}

class _CivicGridMobileAppState extends State<CivicGridMobileApp> {
  int _index = 0;
  final _baseController = TextEditingController(text: 'http://10.0.2.2:8000');

  @override
  Widget build(BuildContext context) {
    final api = CivicApi(baseUrl: _baseController.text.trim());

    final pages = [
      AskScreen(api: api),
      JobsScreen(api: api),
      const ComputeScreen(),
    ];

    return MaterialApp(
      title: 'CivicGrid Mobile',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0F6D50)),
        useMaterial3: true,
      ),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('CivicGrid NYC Mobile'),
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(72),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: TextField(
                controller: _baseController,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'API Base URL',
                ),
                onSubmitted: (_) => setState(() {}),
              ),
            ),
          ),
        ),
        body: pages[_index],
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (value) => setState(() => _index = value),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.search), label: 'Ask'),
            NavigationDestination(icon: Icon(Icons.analytics), label: 'Jobs'),
            NavigationDestination(icon: Icon(Icons.memory), label: 'Compute'),
          ],
        ),
      ),
    );
  }
}
