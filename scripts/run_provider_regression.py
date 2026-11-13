"""Install a trusted candidate in a fresh VS Code profile and run reviewed scenarios."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 256 * 1024


def read_suite(path):
    with path.open('rb') as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('Suite exceeds 2 MiB')
    suite = json.loads(raw)
    if suite['schema_version'] != 1 or suite['kind'] != 'provider_suite':
        raise ValueError('Unsupported provider suite')
    if not isinstance(suite['review']['source'], str) or not suite['review']['source'].strip():
        raise ValueError('Provide reviewed expectation provenance')
    scenarios = suite['scenarios']
    if not 1 <= len(scenarios) <= 32:
        raise ValueError('Expected 1–32 scenarios')
    names = set()
    for scenario in scenarios:
        name = scenario['name']
        if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,64}', scenario['language']):
            raise ValueError('Invalid scenario language')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', name) or name in names:
            raise ValueError('Invalid or duplicate scenario name')
        names.add(name)
        files = scenario['files']
        if not 1 <= len(files) <= 64:
            raise ValueError('Expected 1–64 files per scenario')
        paths = set()
        for file in files:
            path = file['path']
            if not all(re.fullmatch(r'[a-zA-Z0-9_-][a-zA-Z0-9_.-]{0,63}', part)
                       and not part.endswith('.') and not PurePosixPath(part).is_reserved()
                       for part in path.split('/')):
                raise ValueError('Invalid fixture path')
            if path.lower() in paths:
                raise ValueError('Duplicate fixture path')
            paths.add(path.lower())
            if any(len(file[key].encode('utf-8')) > MAX_FILE for key in ('before', 'after')):
                raise ValueError('Fixture text exceeds 256 KiB')
        op = scenario['operation']
        if op['path'] not in [file['path'] for file in files]:
            raise ValueError('Operation target must be declared')
        if op['kind'] == 'rename':
            if any(type(op[key]) is not int or not 0 <= op[key] <= 1000000
                   for key in ('line', 'character')) or not isinstance(op['new_name'], str) or not op['new_name']:
                raise ValueError('Invalid rename parameters')
        elif op['kind'] == 'sync':
            if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,100}', op['command']):
                raise ValueError('Invalid sync command')
        elif op['kind'] != 'format':
            raise ValueError('Unsupported operation')
        if 'allow_empty' in op:
            raise ValueError('Empty provider responses are not supported in v1')
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


def launch(command, env, log, timeout):
    with log.open('xb') as stream:
        return subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT,
                              timeout=timeout, check=False).returncode


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
    status = launch([*launcher, *isolation, '--install-extension', str(args.candidate)],
                    env, directory/'install.log', 60)
    if status:
        raise RuntimeError('VSIX installation failed')
    manifests = list(installed.glob('*/package.json'))
    if len(manifests) != 1:
        raise RuntimeError('Expected a single isolated candidate installation')
    manifest = json.loads(manifests[0].read_text(encoding='utf-8'))
    if manifest.get('extensionDependencies') or manifest.get('extensionPack'):
        raise RuntimeError('Provider dependencies are not supported by this runner')
    languages = manifest.get('contributes', {}).get('languages', [])
    if scenario['language'] not in {language['id'] for language in languages}:
        raise RuntimeError('Candidate does not declare the scenario language')
    result = directory/'result.json'
    request = directory/'request.json'
    request.write_text(json.dumps({
        'scenario': scenario, 'candidate': candidate, 'installed': str(manifests[0].parent),
        'host': args.host, 'core': str(args.core), 'result': str(result),
        'log': str(directory/'provider.log'),
    }), encoding='utf-8')
    env['EDITTRACE_PROVIDER_REQUEST'] = str(request)
    status = launch([
        *launcher, *isolation, '--extensionDevelopmentPath=' + str(ROOT/'extensions/vscode'),
        '--extensionTestsPath=' + str(ROOT/'extensions/vscode/provider-host.js'),
        '--disable-workspace-trust', '--skip-welcome', '--skip-release-notes', '--disable-updates',
        '--wait', str(workspace),
    ], env, directory/'host.log', 90)
    if status or not result.is_file() or result.stat().st_size > MAX_FILE:
        raise RuntimeError('VS Code host did not complete')
    report = json.loads(result.read_text(encoding='utf-8'))
    if report.get('exit_code') not in (0, 1, 2):
        raise RuntimeError('Invalid host result')
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
        for scenario in suite['scenarios']:
            try:
                case = run_scenario(scenario, args, candidate, args.out/scenario['name'])
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                case = {'name': scenario['name'], 'exit_code': 2, 'failures': [{'reason': str(error)}]}
            report['scenarios'].append(case)
        if hashlib.sha256(args.suite.read_bytes()).hexdigest() != suite_hash:
            raise ValueError('Reviewed suite changed during execution')
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile) as error:
        report['scenarios'].append({'name': 'setup', 'exit_code': 2, 'failures': [{'reason': str(error)}]})
    report['exit_code'] = max(case['exit_code'] for case in report['scenarios'])
    write_reports(args.out, report)
    print(json.dumps(report))
    return report['exit_code']


if __name__ == '__main__':
    sys.exit(main())
