import 'package:flutter/material.dart';

import '../api.dart';

class JobsScreen extends StatefulWidget {
  const JobsScreen({super.key, required this.api});

  final CivicApi api;

  @override
  State<JobsScreen> createState() => _JobsScreenState();
}

class _JobsScreenState extends State<JobsScreen> {
  bool _loading = false;
  String _status = 'Load MVP jobs or generate 10,000 jobs';
  List<Map<String, dynamic>> _mvpJobs = const [];
  List<Map<String, dynamic>> _generatedJobs = const [];

  Future<void> _loadMvpJobs() async {
    setState(() {
      _loading = true;
      _status = 'Loading MVP jobs...';
    });
    try {
      final jobs = await widget.api.listMvpJobs();
      setState(() {
        _mvpJobs = jobs;
        _status = 'Loaded ${jobs.length} MVP jobs';
      });
    } catch (e) {
      setState(() {
        _status = 'Load failed: $e';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Future<void> _generate10k() async {
    setState(() {
      _loading = true;
      _status = 'Generating 10,000 jobs...';
    });
    try {
      final summary = await widget.api.buildGeneratedJobs(target: 10000);
      setState(() {
        _status =
            'Generated ${summary['generated_count']} jobs from ${summary['dataset_pool_size']} datasets';
      });
      await _loadGenerated();
    } catch (e) {
      setState(() {
        _status = 'Generation failed: $e';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Future<void> _loadGenerated() async {
    setState(() {
      _loading = true;
      _status = 'Loading generated jobs...';
    });
    try {
      final payload = await widget.api.listGeneratedJobs(offset: 0, limit: 25);
      final items = (payload['items'] as List<dynamic>)
          .map((e) => e as Map<String, dynamic>)
          .toList();
      setState(() {
        _generatedJobs = items;
        _status =
            'Showing ${items.length} of ${payload['total']} generated jobs';
      });
    } catch (e) {
      setState(() {
        _status = 'Generated list failed: $e';
      });
    } finally {
      setState(() {
        _loading = false;
      });
    }
  }

  Future<void> _runJob(String jobId) async {
    setState(() {
      _loading = true;
      _status = 'Running $jobId...';
    });
    try {
      final result = await widget.api.runJob(jobId);
      final rowCount = (result['rows'] as List<dynamic>).length;
      setState(() {
        _status = 'Job $jobId returned $rowCount result rows';
      });
    } catch (e) {
      setState(() {
        _status = 'Run failed: $e';
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
          Text('Jobs', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            children: [
              ElevatedButton(
                onPressed: _loading ? null : _loadMvpJobs,
                child: const Text('Load MVP Jobs'),
              ),
              ElevatedButton(
                onPressed: _loading ? null : _generate10k,
                child: const Text('Generate 10,000'),
              ),
              ElevatedButton(
                onPressed: _loading ? null : _loadGenerated,
                child: const Text('List Generated'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(_status),
          const SizedBox(height: 12),
          Expanded(
            child: ListView(
              children: [
                const Text('MVP Jobs',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                ..._mvpJobs.map(
                  (j) => Card(
                    child: ListTile(
                      title: Text(j['title']?.toString() ?? ''),
                      subtitle: Text(j['objective']?.toString() ?? ''),
                      trailing: IconButton(
                        icon: const Icon(Icons.play_arrow),
                        onPressed: _loading
                            ? null
                            : () => _runJob(j['job_id']?.toString() ?? ''),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'Generated Jobs (sample)',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                ..._generatedJobs.map(
                  (j) => Card(
                    child: ListTile(
                      title: Text(j['title']?.toString() ?? ''),
                      subtitle: Text(j['job_id']?.toString() ?? ''),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
