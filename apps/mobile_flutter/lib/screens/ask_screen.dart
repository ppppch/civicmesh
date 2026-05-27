import 'package:flutter/material.dart';

import '../api.dart';

class AskScreen extends StatefulWidget {
  const AskScreen({super.key, required this.api});

  final CivicApi api;

  @override
  State<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends State<AskScreen> {
  final TextEditingController _controller = TextEditingController(
    text:
        'Which neighborhoods have rising 311 heat complaints but low tree coverage?',
  );

  bool _loading = false;
  String _status = 'Ready';
  List<Map<String, dynamic>> _results = const [];

  Future<void> _ingest() async {
    setState(() {
      _loading = true;
      _status = 'Ingesting NYC catalog...';
    });
    try {
      final summary = await widget.api.ingestCatalog();
      setState(() {
        _status =
            'Ingested ${summary['datasets_selected']} selected out of ${summary['datasets_scanned']} scanned';
      });
    } catch (e) {
      setState(() {
        _status = 'Ingest failed: $e';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Future<void> _search() async {
    setState(() {
      _loading = true;
      _status = 'Searching datasets...';
    });
    try {
      final results = await widget.api.searchDatasets(_controller.text.trim());
      setState(() {
        _results = results;
        _status = 'Found ${results.length} datasets';
      });
    } catch (e) {
      setState(() {
        _status = 'Search failed: $e';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Ask NYC',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _controller,
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              labelText: 'Question',
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            children: [
              ElevatedButton(
                onPressed: _loading ? null : _ingest,
                child: const Text('Ingest Catalog'),
              ),
              ElevatedButton(
                onPressed: _loading ? null : _search,
                child: const Text('Find Datasets'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(_status),
          const SizedBox(height: 12),
          Expanded(
            child: ListView.builder(
              itemCount: _results.length,
              itemBuilder: (context, index) {
                final item = _results[index];
                return Card(
                  child: ListTile(
                    title: Text(item['title']?.toString() ?? 'Untitled'),
                    subtitle: Text(item['description']?.toString() ?? ''),
                    trailing: Text(item['category']?.toString() ?? ''),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
