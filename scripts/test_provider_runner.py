"""Exercise the boundary where a malformed scenario or stale host result could pass CI."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

from run_provider_regression import (ExecutionIncomplete, ROOT, await_host_result, launch,
                                     launcher_hint, read_host_report, read_suite)


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
                   'invocation': 'host_observation',
                   'scenario': self.suite['scenarios'][0]}
        report = {'report_protocol': 3, 'request_id': 'current', 'host': request['host'],
                  'candidate': request['candidate'], 'name': request['scenario']['name'],
                  'invocation': request['invocation'],
                  'exit_code': 0, 'analysis_complete': True, 'failures': [], 'stage': 'complete', 'rules': []}
        self.input.write_text(json.dumps(report), encoding='utf-8')
        self.assertEqual(read_host_report(self.input, request), report)
        for changed in [{'request_id': 'stale'}, {'candidate': {}}, {'host': '1.143.1'},
                        {'name': 'other'}, {'analysis_complete': False}, {'exit_code': False},
                        {'stage': 'provider_request'}, {'rules': ['/private/file']},
                        {'invocation': 'candidate_api_v1'}]:
            with self.subTest(changed=changed):
                self.input.write_text(json.dumps(report | changed), encoding='utf-8')
                with self.assertRaises(ExecutionIncomplete):
                    read_host_report(self.input, request)

    def test_launcher_timeout_is_classified(self):
        with self.assertRaises(ExecutionIncomplete) as error:
            launch([sys.executable, '-c', 'import time; time.sleep(30)'], None,
                   self.directory/'host.log', 0.2, 'host_launch')
        self.assertEqual(error.exception.diagnostic, {'stage': 'host_launch', 'reason': 'process_timeout'})

    def test_scope_regression_keeps_first_event(self):
        scenario = self.suite['scenarios'][2]
        request = {'request_id': 'current', 'host': '1.144.0', 'candidate': {'id': 'test.sample'},
                   'invocation': 'host_observation', 'scenario': scenario}
        failure = {'reason': 'sync edit outside declared files', 'seq': 8}
        report = {**request, 'report_protocol': 3, 'name': scenario['name'], 'exit_code': 1,
                  'analysis_complete': True, 'stage': 'complete', 'rules': [], 'failures': [failure]}
        del report['scenario']
        self.input.write_text(json.dumps(report), encoding='utf-8')
        self.assertEqual(read_host_report(self.input, request), report)
        failure['seq'] = True
        self.input.write_text(json.dumps(report), encoding='utf-8')
        with self.assertRaises(ExecutionIncomplete):
            read_host_report(self.input, request)

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

    def test_host_without_report_is_classified_by_ready_marker(self):
        ready, result, log = (self.directory/f for f in ('ready', 'result', 'host.log'))
        log.write_text('private text', encoding='utf-8')
        for marker, reason in [(None, 'host_not_ready'), ('current', 'missing_host_report'),
                               ('stale', 'invalid_ready_marker')]:
            with self.subTest(marker=marker):
                if marker is not None:
                    ready.write_text(marker, encoding='ascii')
                with self.assertRaises(ExecutionIncomplete) as error:
                    await_host_result(0, time.monotonic(), ready, result, 'current', log)
                self.assertEqual(error.exception.diagnostic['reason'], reason)
        ready.write_text('current', encoding='ascii')
        with self.assertRaises(ExecutionIncomplete) as error:
            await_host_result(None, time.monotonic(), ready, result, 'current', log)
        self.assertEqual(error.exception.diagnostic['stage'], 'host_result')
        self.assertEqual(error.exception.diagnostic['reason'], 'process_timeout')

    def test_successful_launcher_exit_can_precede_host_report(self):
        ready, result, log = (self.directory/f for f in ('ready', 'result', 'host.log'))

        def report_later(status, deadline):
            def publish():
                ready.write_text('current', encoding='ascii')
                result.write_text('{}', encoding='ascii')

            timer = threading.Timer(0.08, publish)
            timer.start()
            try:
                await_host_result(status, deadline, ready, result, 'current', log)
            finally:
                timer.join()

        status, _ = launch([sys.executable, '-c', 'pass'], None, log, 4, 'host_launch',
                           after_exit=report_later)
        self.assertEqual(status, 0)


if __name__ == '__main__':
    unittest.main()
