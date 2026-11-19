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


def scope_cases():
    sync = next(value for name, value, *_ in cases() if name == 'valid-sync')

    def with_events(events):
        value = copy.deepcopy(sync)
        records = value['verification']['records']
        records[-2:-2] = events
        for seq, record in enumerate(records[1:], 1):
            record['seq'] = seq
        return value

    def message(method, document, **params):
        return {'kind': 'message', 'direction': 'client_to_server', 'message': {
            'jsonrpc': '2.0', 'method': 'textDocument/' + method,
            'params': {'textDocument': document, **params},
        }}

    def open_doc(uri):
        return message('didOpen', {'uri': uri, 'version': 1, 'languageId': 'text', 'text': 'old'})

    def change(uri, version, text):
        return message('didChange', {'uri': uri, 'version': version}, contentChanges=[{'text': text}])

    other = 'file:///outside.mbt'
    memory = 'untitled:Untitled-1'
    wrong_direction = change(other, 2, 'new')
    wrong_direction['direction'] = 'server_to_client'
    malformed = change(other, 2, 'new')
    del malformed['message']['params']['contentChanges']
    missing = with_events([open_doc(other), change(other, 2, 'new')])
    missing['observed'].pop()
    frozen = with_events([change('file:///b', 2, 'edited'), change('file:///b', 3, 'b')])
    frozen['verification']['records'][-1]['version'] = 3
    return [
        ('outside-file', with_events([open_doc(other), change(other, 2, 'new')]), 0, 1),
        ('outside-untitled', with_events([open_doc(memory), change(memory, 2, 'new')]), 0, 1),
        ('background-open', with_events([open_doc(other)]), 0, 0),
        ('outside-undo', with_events([open_doc(other), change(other, 2, 'new'), change(other, 3, 'old')]), 0, 1),
        ('frozen-undo', frozen, 0, 1),
        ('outside-missing-open', with_events([change(other, 2, 'new')]), 2, 2),
        ('outside-wrong-direction', with_events([open_doc(other), wrong_direction]), 1, 2),
        ('outside-malformed', with_events([open_doc(other), malformed]), 2, 2),
        ('outside-and-missing-observation', missing, 2, 2),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('core', type=Path)
    baseline = parser.add_mutually_exclusive_group()
    baseline.add_argument('--baseline-051', action='store_true')
    baseline.add_argument('--baseline-052', action='store_true')
    args = parser.parse_args()
    core = args.core.resolve()
    version = subprocess.check_output([core, '--version'], text=True, timeout=15).strip()
    if args.baseline_051 and version != '0.5.1':
        raise SystemExit('Baseline reproduction requires EditTrace 0.5.1')
    if args.baseline_052 and version != '0.5.2':
        raise SystemExit('Scope reproduction requires EditTrace 0.5.2')
    scenarios = scope_cases() if args.baseline_052 else cases() if args.baseline_051 else cases() + scope_cases()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)/'observation.json'
        for name, value, old_code, new_code in scenarios:
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
            expected = old_code if args.baseline_051 or args.baseline_052 else new_code
            if (result.returncode != expected or report['exit_code'] != expected
                    or report['analysis_complete'] is not (expected != 2)):
                raise AssertionError((name, result.returncode, report))
            reasons = {'outside-file': 'sync edit outside declared files',
                       'outside-untitled': 'sync edit outside declared files',
                       'outside-undo': 'sync edit outside declared files',
                       'frozen-undo': 'sync edit to a file expected to stay unchanged'}
            if expected == 1 and name in reasons and not any(
                    failure['reason'] == reasons[name] for failure in report['failures']):
                raise AssertionError((name, report))
            print(json.dumps({'core': version, 'case': name, 'exit_code': result.returncode,
                              'failures': report['failures']}))


if __name__ == '__main__':
    main()
