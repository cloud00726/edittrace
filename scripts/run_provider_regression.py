"""Install a trusted candidate in a fresh VS Code profile and run reviewed scenarios."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import signal
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 256 * 1024
MAX_SUITE = 2 * 1024 * 1024
MAX_LOG = 1024 * 1024
REPORT_PROTOCOL = 2


def fields(value, required):
    if not isinstance(value, dict) or value.keys() != set(required.split()):
        raise ValueError('Invalid object fields')


def matches(value, pattern):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('Duplicate JSON key')
        obj[key] = value
    return obj


def read_bounded(path, limit):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Input exceeds size limit')
    return raw


def read_suite(path):
    raw = read_bounded(path, MAX_SUITE)
    suite = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    fields(suite, 'schema_version kind provider review scenarios')
    if type(suite['schema_version']) is not int or suite['schema_version'] != 1 or suite['kind'] != 'provider_suite':
        raise ValueError('Unsupported provider suite')
    if not matches(suite['provider'], r'[a-zA-Z0-9_-]{1,64}\.[a-zA-Z0-9_-]{1,64}'):
        raise ValueError('Invalid provider ID')
    fields(suite['review'], 'source')
    if not isinstance(suite['review']['source'], str) or not suite['review']['source'].strip():
        raise ValueError('Provide reviewed expectation provenance')
    scenarios = suite['scenarios']
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 32:
        raise ValueError('Expected 1–32 scenarios')
    names = set()
    for scenario in scenarios:
        fields(scenario, 'name language operation files')
        name = scenario['name']
        if not matches(scenario['language'], r'[a-zA-Z0-9_.-]{1,64}'):
            raise ValueError('Invalid scenario language')
        if (not matches(name, r'[a-zA-Z0-9_-]{1,64}') or name.lower() in names
                or PureWindowsPath(name).is_reserved()):
            raise ValueError('Invalid or duplicate scenario name')
        names.add(name.lower())
        files = scenario['files']
        if not isinstance(files, list) or not 1 <= len(files) <= 64:
            raise ValueError('Expected 1–64 files per scenario')
        paths = set()
        directories = {}
        for file in files:
            fields(file, 'path before after')
            path = file['path']
            if not isinstance(path, str) or len(path) > 200 or not all(re.fullmatch(r'[a-zA-Z0-9_-][a-zA-Z0-9_.-]{0,63}', part)
                       and not part.endswith('.') and not PureWindowsPath(part).is_reserved()
                       for part in path.split('/')):
                raise ValueError('Invalid fixture path')
            folded = path.lower()
            if any(p == folded or p.startswith(folded + '/') or folded.startswith(p + '/') for p in paths):
                raise ValueError('Conflicting fixture path')
            paths.add(folded)
            for parent in PurePosixPath(path).parents:
                spelling = parent.as_posix()
                if directories.setdefault(spelling.lower(), spelling) != spelling:
                    raise ValueError('Inconsistent directory casing')
            if any(not isinstance(file[key], str) or len(file[key].encode('utf-8')) > MAX_FILE for key in ('before', 'after')):
                raise ValueError('Fixture text exceeds 256 KiB')
        op = scenario['operation']
        if not isinstance(op, dict):
            raise ValueError('Invalid operation object')
        if op['path'] not in [file['path'] for file in files]:
            raise ValueError('Operation target must be declared')
        if op['kind'] == 'rename':
            fields(op, 'kind path line character new_name')
            if any(type(op[key]) is not int or not 0 <= op[key] <= 1000000
                   for key in ('line', 'character')) or not isinstance(op['new_name'], str) or not op['new_name']:
                raise ValueError('Invalid rename parameters')
        elif op['kind'] == 'sync':
            fields(op, 'kind path command')
            if not matches(op['command'], r'[a-zA-Z0-9_.-]{1,100}'):
                raise ValueError('Invalid sync command')
        elif op['kind'] == 'format':
            fields(op, 'kind path')
        else:
            raise ValueError('Unsupported operation')
    return suite, hashlib.sha256(raw).hexdigest()


def artifact_identity(path, expected_hash):
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('Candidate archive exceeds 128 MiB')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_hash:
        raise ValueError('Candidate SHA-256 mismatch')
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo('extension/package.json')
        if info.file_size > MAX_FILE:
            raise ValueError('Candidate manifest too large')
        manifest = json.loads(archive.read(info))
    if manifest.get('extensionDependencies') or manifest.get('extensionPack'):
        raise ValueError('Provider dependencies are not supported by this runner')
    for key in ('publisher', 'name'):
        if not matches(manifest.get(key), r'[a-zA-Z0-9_-]{1,64}'):
            raise ValueError('Invalid VSIX identity')
    if not matches(manifest.get('version'), r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][a-zA-Z0-9.-]{1,64})?') or len(manifest['version']) > 96:
        raise ValueError('Invalid VSIX version')
    return {
        'id': manifest['publisher'] + '.' + manifest['name'],
        'version': manifest['version'],
        'sha256': digest,
    }


def code_launcher(code):
    env = os.environ.copy()
    if os.name == 'nt' and Path(code).suffix.lower() == '.cmd':
        installation = Path(code).parent.parent
        cli = list(installation.glob('*/resources/app/out/cli.js'))
        legacy = installation / 'resources/app/out/cli.js'
        if legacy.is_file():
            cli.append(legacy)
        if len(cli) != 1:
            raise ValueError('Cannot uniquely locate VS Code CLI')
        env['ELECTRON_RUN_AS_NODE'] = '1'
        return [str(installation/'Code.exe'), str(cli[0])], env
    return [code], env


class ExecutionIncomplete(RuntimeError):
    def __init__(self, stage, reason, **details):
        self.diagnostic = {'stage': stage, 'reason': reason, **details}


def stop_process_tree(process):
    if os.name == 'nt':
        try:
            subprocess.run(['taskkill.exe', '/pid', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=5, check=False)
        finally:
            if process.poll() is None:
                process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def launch(command, env, log, timeout, stage):
    started = time.monotonic()
    try:
        with log.open('xb') as stream:
            with subprocess.Popen(command, env=env, stdout=stream,
                                  stderr=subprocess.STDOUT, start_new_session=os.name != 'nt') as process:
                while True:
                    status = process.poll()
                    if log.stat().st_size > MAX_LOG:
                        stop_process_tree(process)
                        stream.truncate(MAX_LOG)
                        raise ExecutionIncomplete(stage, 'launcher_log_limit')
                    if status is not None:
                        break
                    if time.monotonic() - started >= timeout:
                        stop_process_tree(process)
                        raise ExecutionIncomplete(stage, 'process_timeout')
                    time.sleep(0.05)
    except OSError:
        raise ExecutionIncomplete(stage, 'process_launch_failed') from None
    return status, round(time.monotonic() - started, 3)


def launcher_hint(log):
    raw = read_bounded(log, MAX_LOG).lower()
    if any(token in raw for token in (b'no usable sandbox', b'suid sandbox', b'failed to move to new namespace', b'running as root without --no-sandbox')):
        return 'electron_sandbox'
    if any(token in raw for token in (b'missing x server', b'missing display', b'cannot open display')):
        return 'display_unavailable'
    if b'error while loading shared libraries' in raw:
        return 'missing_shared_library'
    return 'unclassified'


def read_host_report(path, request):
    try:
        report = json.loads(read_bounded(path, MAX_FILE), object_pairs_hook=unique_object)
        fields(report, 'report_protocol request_id name host candidate exit_code analysis_complete failures stage rules')
        if (type(report['report_protocol']) is not int or report['report_protocol'] != REPORT_PROTOCOL
                or report['request_id'] != request['request_id']
                or report['name'] != request['scenario']['name']
                or report['candidate'] != request['candidate']
                or type(report['exit_code']) is not int or report['exit_code'] not in (0, 1, 2)
                or report['analysis_complete'] is not (report['exit_code'] != 2)
                or (report['stage'] == 'complete') != (report['exit_code'] != 2)
                or (report['host'] != request['host'] and
                    (report['exit_code'], report['stage']) != (2, 'host_version'))
                or not matches(report['host'], r'[0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}')
                or report['stage'] not in ('host_version', 'candidate_activation', 'provider_request', 'core_verification', 'complete')
                or not isinstance(report['failures'], list) or len(report['failures']) > 130
                or bool(report['failures']) != (report['exit_code'] != 0)
                or not isinstance(report['rules'], list) or len(report['rules']) > 1024
                or any(not matches(rule, r'[A-Z][A-Z0-9_]{0,95}') for rule in report['rules'])):
            raise ValueError('Invalid host report values')
        allowed_reasons = {
            'fresh edit verification failed', 'missing observation', 'unexpected observation',
            'reviewed text mismatch', 'provider edit outside declared files',
            'provider changed files on disk', 'host or provider execution incomplete',
            'provider response unavailable', 'provider request timed out',
        }
        declared = {f['path'] for f in request['scenario']['files']}
        for failure in report['failures']:
            if (not isinstance(failure, dict)
                    or not set(failure).issubset({'reason', 'path', 'first_difference_utf16'})
                    or failure.get('reason') not in allowed_reasons
                    or ('path' in failure and failure['path'] not in declared)
                    or ('first_difference_utf16' in failure and
                        (type(failure['first_difference_utf16']) is not int or failure['first_difference_utf16'] < 0))):
                raise ValueError('Invalid failure evidence')
    except (OSError, ValueError, KeyError, TypeError):
        raise ExecutionIncomplete('report', 'invalid_host_report') from None
    return report


def run_scenario(scenario, args, candidate, directory):
    workspace = directory / 'workspace'
    workspace.mkdir(parents=True)
    for file in scenario['files']:
        target = workspace / file['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file['before'].encode('utf-8'))
    profile = directory / 'profile'
    settings = profile / 'User/settings.json'
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({
        'telemetry.telemetryLevel': 'off', 'update.mode': 'none',
        'extensions.autoUpdate': False, 'extensions.autoCheckUpdates': False,
        'security.workspace.trust.enabled': False, 'git.enabled': False,
        'files.autoSave': 'off', 'files.hotExit': 'off', 'window.restoreWindows': 'none',
        'workbench.startupEditor': 'none',
    }), encoding='utf-8')
    installed = directory / 'extensions'
    launcher, env = code_launcher(args.code)
    isolation = ['--user-data-dir', str(profile), '--extensions-dir', str(installed)]
    install_log = directory/'install.log'
    status, install_seconds = launch([*launcher, *isolation, '--install-extension', str(args.candidate)],
                                     env, install_log, 60, 'install')
    if status:
        raise ExecutionIncomplete('install', 'launcher_exit', process_exit=status, hint=launcher_hint(install_log))
    manifests = list(installed.glob('*/package.json'))
    if len(manifests) != 1:
        raise RuntimeError('Expected a single isolated candidate installation')
    manifest = json.loads(read_bounded(manifests[0], MAX_FILE))
    languages = manifest.get('contributes', {}).get('languages', [])
    if scenario['language'] not in {language['id'] for language in languages}:
        raise ExecutionIncomplete('install', 'scenario_language_not_declared')
    result = directory/'result.json'
    request_path = directory/'request.json'
    request = {
        'report_protocol': REPORT_PROTOCOL, 'request_id': uuid.uuid4().hex,
        'scenario': scenario, 'candidate': candidate, 'installed': str(manifests[0].parent),
        'host': args.host, 'core': str(args.core), 'result': str(result),
        'log': str(directory/'provider.log'),
    }
    request_path.write_text(json.dumps(request), encoding='utf-8')
    env['EDITTRACE_PROVIDER_REQUEST'] = str(request_path)
    host_log = directory/'host.log'
    status, host_seconds = launch([
        *launcher, *isolation, '--extensionDevelopmentPath=' + str(ROOT/'extensions/vscode'),
        '--extensionTestsPath=' + str(ROOT/'extensions/vscode/provider-host.js'),
        '--disable-workspace-trust', '--skip-welcome', '--skip-release-notes', '--disable-updates',
        '--wait', str(workspace),
    ], env, host_log, 90, 'host_launch')
    if status or not result.is_file():
        raise ExecutionIncomplete('host_launch', 'launcher_exit' if status else 'missing_host_report',
                                  process_exit=status, hint=launcher_hint(host_log))
    report = read_host_report(result, request)
    report['timings_seconds'] = {'install': install_seconds, 'host': host_seconds}
    del report['request_id']
    return report


def write_reports(output, report):
    (output/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    cases = report['scenarios']
    xml = ET.Element('testsuite', name='EditTrace provider regressions', tests=str(len(cases)),
                     failures=str(sum(c['exit_code'] == 1 for c in cases)),
                     errors=str(sum(c['exit_code'] == 2 for c in cases)))
    for case in cases:
        node = ET.SubElement(xml, 'testcase', name=case['name'])
        if case['exit_code']:
            ET.SubElement(node, 'failure' if case['exit_code'] == 1 else 'error',
                          message='Provider regression' if case['exit_code'] == 1 else 'Execution incomplete').text = json.dumps(case['failures'])
    ET.ElementTree(xml).write(output/'junit.xml', encoding='utf-8', xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', type=Path)
    parser.add_argument('--check-input', action='store_true',
                        help='Verify the suite, candidate digest and declared host version without installing')
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--code', default=shutil.which('code'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.candidate = args.candidate.resolve()
    args.core = args.core.resolve()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    report = {'schema_version': 1, 'host': args.host, 'scenarios': []}
    try:
        if not matches(args.host, r'[0-9]{1,5}\.[0-9]{1,5}\.[0-9]{1,5}'):
            raise ValueError('Invalid expected VS Code version')
        suite, suite_hash = read_suite(args.suite)
        report['suite_sha256'] = suite_hash
        report['core_sha256'] = hashlib.sha256(args.core.read_bytes()).hexdigest()
        if args.candidate.stat().st_size > 128 * 1024 * 1024:
            raise ValueError('Candidate archive exceeds 128 MiB')
        candidate_copy = args.out/'candidate.vsix'
        shutil.copyfile(args.candidate, candidate_copy)
        candidate = artifact_identity(candidate_copy, args.sha256)
        args.candidate = candidate_copy
        if candidate['id'] != suite['provider']:
            raise ValueError('Candidate extension ID differs from reviewed suite')
        report['candidate'] = candidate
        if not args.code:
            raise ValueError('VS Code executable unavailable')
        if args.check_input:
            launcher, env = code_launcher(args.code)
            probe_log = args.out/'host-version.log'
            status, seconds = launch([*launcher, '--version'], env, probe_log, 15, 'host_version')
            lines = read_bounded(probe_log, MAX_LOG).decode('utf-8', errors='replace').splitlines()
            if status or args.host not in lines:
                raise ExecutionIncomplete('host_version', 'host_version_unverified', process_exit=status,
                                          hint=launcher_hint(probe_log))
            report['scenarios'].append({'name': 'check-input', 'exit_code': 0, 'analysis_complete': True,
                                        'failures': [], 'timings_seconds': {'host_version': seconds}})
        for scenario in ([] if args.check_input else suite['scenarios']):
            try:
                case = run_scenario(scenario, args, candidate, args.out/scenario['name'])
            except ExecutionIncomplete as error:
                case = {'name': scenario['name'], 'exit_code': 2, 'analysis_complete': False,
                        'failures': [error.diagnostic]}
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                case = {'name': scenario['name'], 'exit_code': 2, 'analysis_complete': False,
                        'failures': [{'stage': 'prepare', 'reason': type(error).__name__}]}
            report['scenarios'].append(case)
        if hashlib.sha256(read_bounded(args.suite, MAX_SUITE)).hexdigest() != suite_hash:
            raise ValueError('Reviewed suite changed during execution')
    except ExecutionIncomplete as error:
        report['scenarios'].append({'name': 'setup', 'exit_code': 2, 'analysis_complete': False,
                                    'failures': [error.diagnostic]})
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile, RecursionError) as error:
        reason = str(error) if type(error) is ValueError else type(error).__name__
        if isinstance(error, json.JSONDecodeError):
            reason = 'Invalid JSON'
        report['scenarios'].append({'name': 'setup', 'exit_code': 2, 'analysis_complete': False,
                                    'failures': [{'stage': 'setup', 'reason': reason}]})
    report['exit_code'] = max(case['exit_code'] for case in report['scenarios'])
    write_reports(args.out, report)
    print(json.dumps(report))
    return report['exit_code']


if __name__ == '__main__':
    sys.exit(main())
