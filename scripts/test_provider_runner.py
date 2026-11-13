"""Exercise the boundary where a malformed scenario or stale host result could pass CI."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from run_provider_regression import ExecutionIncomplete, ROOT, launch, launcher_hint, read_host_report, read_suite


class ProviderRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.input = self.directory/'suite.json'
        self.suite = json.loads((ROOT/'examples/provider-consumer/suite.json').read_text(encoding='utf-8'))

    def test_fixture_paths_must_work_on_both_platforms(self):
        for paths in [('dir', 'DIR/a'), ('A/x', 'a/y'), ('NUL', 'b'), ('../a', 'b')]:
            with self.subTest(paths=paths):
                suite = copy.deepcopy(self.suite)
                for item, path in zip(suite['scenarios'][0]['files'], paths):
                    item['path'] = path
                suite['scenarios'][0]['operation']['path'] = paths[0]
                self.input.write_text(json.dumps(suite), encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_suite(self.input)

    def test_valid_suite_and_invalid_operation_fields(self):
        self.input.write_text(json.dumps(self.suite), encoding='utf-8')
        self.assertEqual(read_suite(self.input)[0], self.suite)
        self.suite['scenarios'][0]['operation']['characters'] = 12
        self.input.write_text(json.dumps(self.suite), encoding='utf-8')
        with self.assertRaises(ValueError):
            read_suite(self.input)

    def test_host_success_requires_matching_complete_evidence(self):
        request = {'request_id': 'current', 'host': '1.144.0', 'candidate': {'id': 'test.sample'},
                   'scenario': self.suite['scenarios'][0]}
        report = {'report_protocol': 2, 'request_id': 'current', 'host': request['host'],
                  'candidate': request['candidate'], 'name': request['scenario']['name'],
                  'exit_code': 0, 'analysis_complete': True, 'failures': [], 'stage': 'complete', 'rules': []}
        self.input.write_text(json.dumps(report), encoding='utf-8')
        self.assertEqual(read_host_report(self.input, request), report)
        for changed in [{'request_id': 'stale'}, {'candidate': {}}, {'host': '1.143.1'},
                        {'name': 'other'}, {'analysis_complete': False}, {'exit_code': False},
                        {'stage': 'provider_request'}, {'rules': ['/private/file']}]:
            with self.subTest(changed=changed):
                self.input.write_text(json.dumps(report | changed), encoding='utf-8')
                with self.assertRaises(ExecutionIncomplete):
                    read_host_report(self.input, request)

    def test_launcher_timeout_is_classified(self):
        with self.assertRaises(ExecutionIncomplete) as error:
            launch([sys.executable, '-c', 'import time; time.sleep(30)'], None,
                   self.directory/'host.log', 0.2, 'host_launch')
        self.assertEqual(error.exception.diagnostic, {'stage': 'host_launch', 'reason': 'process_timeout'})

    def test_launcher_only_exposes_known_hint(self):
        self.input.write_bytes(b'private source\nNo usable sandbox!')
        self.assertEqual(launcher_hint(self.input), 'electron_sandbox')
        self.input.write_bytes(b'private source')
        self.assertEqual(launcher_hint(self.input), 'unclassified')

    def test_excessive_launcher_output_is_blocked_and_truncated(self):
        with self.assertRaises(ExecutionIncomplete) as error:
            launch([sys.executable, '-c', "print('x' * (2 * 1024 * 1024))"], None,
                   self.directory/'host.log', 5, 'host_launch')
        self.assertEqual(error.exception.diagnostic['reason'], 'launcher_log_limit')
        self.assertEqual((self.directory/'host.log').stat().st_size, 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
