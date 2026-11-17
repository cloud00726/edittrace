"""Exercise provider evidence through a supplied native CLI."""

import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile


def edit_observation():
    return {
        'schema_version': 3, 'kind': 'provider_observation', 'name': 'two-files',
        'expected': [{'path': 'a', 'uri': 'file:///a', 'text': 'A'},
                     {'path': 'b', 'uri': 'file:///b', 'text': 'b'}],
        'observed': [{'path': 'a', 'uri': 'file:///a', 'text': 'A'},
                     {'path': 'b', 'uri': 'file:///b', 'text': 'b'}],
        'verification': {'kind': 'edit_plan', 'plan': {
            'schema_version': 1, 'kind': 'edit_plan', 'position_encoding': 'utf-16', 'source': {},
            'documents': [{'uri': 'file:///a', 'version': 1, 'text': 'a'},
                          {'uri': 'file:///b', 'version': 1, 'text': 'b'}],
            'workspace_edit': {'documentChanges': [{
                'textDocument': {'uri': 'file:///a', 'version': 1},
                'edits': [{'range': {'start': {'line': 0, 'character': 0},
                                     'end': {'line': 0, 'character': 1}}, 'newText': 'A'}],
            }]},
            'actual': [{'uri': 'file:///a', 'text': 'A'}],
        }},
    }


def cases():
    good = edit_observation()
    unexplained = copy.deepcopy(good)
    unexplained['observed'][1]['text'] = unexplained['expected'][1]['text'] = 'B'
    missing = copy.deepcopy(good)
    missing['observed'].pop()
    swapped = copy.deepcopy(good)
    swapped['observed'][0]['uri'], swapped['observed'][1]['uri'] = (
        swapped['observed'][1]['uri'], swapped['observed'][0]['uri'])
    regression = copy.deepcopy(good)
    regression['expected'][0]['text'] = 'different'
    legacy = copy.deepcopy(good)
    legacy['schema_version'] = 2
    for item in legacy['expected']:
        del item['uri']
    sync = {
        'schema_version': 3, 'kind': 'provider_observation', 'name': 'sync',
        'expected': good['expected'],
        'observed': good['observed'],
        'verification': {'kind': 'trace', 'records': [
            {'kind': 'meta', 'schema_version': 1, 'position_encoding': 'utf-16',
             'capture_mode': 'fragment', 'provenance': 'synthetic', 'producer': 'provider-tests'},
            {'kind': 'message', 'seq': 1, 'direction': 'client_to_server', 'message': {
                'jsonrpc': '2.0', 'method': 'textDocument/didOpen',
                'params': {'textDocument': {'uri': 'file:///a', 'languageId': 'text', 'version': 1, 'text': 'a'}},
            }},
            {'kind': 'message', 'seq': 2, 'direction': 'client_to_server', 'message': {
                'jsonrpc': '2.0', 'method': 'textDocument/didOpen',
                'params': {'textDocument': {'uri': 'file:///b', 'languageId': 'text', 'version': 1, 'text': 'b'}},
            }},
            {'kind': 'message', 'seq': 3, 'direction': 'client_to_server', 'message': {
                'jsonrpc': '2.0', 'method': 'textDocument/didChange',
                'params': {'textDocument': {'uri': 'file:///a', 'version': 2}, 'contentChanges': [{'text': 'A'}]},
            }},
            {'kind': 'checkpoint', 'seq': 4, 'uri': 'file:///a', 'version': 2, 'text': 'A',
             'source': 'vscode.TextDocument.getText.afterCommand'},
            {'kind': 'checkpoint', 'seq': 5, 'uri': 'file:///b', 'version': 1, 'text': 'b',
             'source': 'vscode.TextDocument.getText.afterCommand'},
        ]},
    }
    missing_checkpoint = copy.deepcopy(sync)
    missing_checkpoint['verification']['records'].pop()
    duplicate_checkpoint = copy.deepcopy(sync)
    duplicate_checkpoint['verification']['records'][-1].update(uri='file:///a', text='A', version=2)
    stale_checkpoint = copy.deepcopy(sync)
    stale_checkpoint['verification']['records'][-2]['version'] = 1
    sync_regression = copy.deepcopy(sync)
    sync_regression['expected'][0]['text'] = 'different'
    return [
        ('unexplained-edit', unexplained, 0, 2), ('missing-observation', missing, 1, 2),
        ('valid-edit', good, 0, 0), ('swapped-binding', swapped, 1, 2),
        ('reviewed-mismatch', regression, 1, 1), ('legacy-observation', legacy, 0, 2),
        ('valid-sync', sync, 0, 0), ('sync-behavior-mismatch', sync_regression, 1, 1),
        ('missing-checkpoint', missing_checkpoint, 2, 2),
        ('duplicate-checkpoint', duplicate_checkpoint, 2, 2),
        ('stale-checkpoint', stale_checkpoint, 2, 2),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('core', type=Path)
    parser.add_argument('--baseline-051', action='store_true')
    args = parser.parse_args()
    core = args.core.resolve()
    version = subprocess.check_output([core, '--version'], text=True, timeout=15).strip()
    if args.baseline_051 and version != '0.5.1':
        raise SystemExit('Baseline reproduction requires EditTrace 0.5.1')
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)/'observation.json'
        for name, value, old_code, new_code in cases():
            if args.baseline_051:
                if name not in ('unexplained-edit', 'missing-observation'):
                    continue
                value['schema_version'] = 2
                for item in value['expected']:
                    del item['uri']
            path.write_text(json.dumps(value), encoding='utf-8')
            result = subprocess.run([core, 'check-provider', path, '--format', 'json'],
                                    capture_output=True, timeout=15)
            report = json.loads(result.stdout)
            expected = old_code if args.baseline_051 else new_code
            if (result.returncode != expected or report['exit_code'] != expected
                    or report['analysis_complete'] is not (expected != 2)):
                raise AssertionError((name, result.returncode, report))
            print(json.dumps({'core': version, 'case': name, 'exit_code': result.returncode,
                              'failures': report['failures']}))


if __name__ == '__main__':
    main()
