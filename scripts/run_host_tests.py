"""Run the installed real VS Code Extension Host in an isolated workspace/profile."""
import argparse, json, os, shutil, subprocess, time, tempfile
from pathlib import Path
from native_artifact import find_native_executable

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--code', default=shutil.which('code'))
    parser.add_argument('--extension-path', default=str(ROOT/'extensions/vscode'))
    args = parser.parse_args()
    if not args.code:
        raise SystemExit('VS Code is unavailable; host integration NOT verified')
    base = ROOT / 'artifacts' / 'vscode-host'
    base.mkdir(parents=True, exist_ok=True)
    work = base / 'workspace'
    work.mkdir(exist_ok=True)
    (work / 'tsconfig.json').write_text('{"compilerOptions":{"module":"commonjs","target":"es2020"},"include":["*.ts"]}', encoding='utf-8')
    (work/'captured-regression.case.json').unlink(missing_ok=True)
    profile = Path(tempfile.mkdtemp(prefix='vscode-test-profile-', dir=ROOT/'.tooling'))
    (profile / 'User').mkdir(parents=True, exist_ok=True)
    (profile / 'User/settings.json').write_text(json.dumps({'telemetry.telemetryLevel':'off','update.mode':'none','workbench.enableExperiments':False,'json.schemaDownload.enable':False,'security.workspace.trust.enabled':False,'extensions.autoCheckUpdates':False,'extensions.autoUpdate':False,'git.enabled':False,'files.hotExit':'off','window.restoreWindows':'none'}), encoding='utf-8')
    result = base / 'result.json'
    result.unlink(missing_ok=True)
    env = os.environ.copy()
    env['EDITTRACE_HOST_OUTPUT'] = str(result)
    bundled=Path(args.extension_path)/'bin'/('edittrace.exe' if os.name=='nt' else 'edittrace')
    env['EDITTRACE_EXE'] = str(bundled if bundled.is_file() else find_native_executable(ROOT))
    command = [args.code, '--user-data-dir', str(profile), '--extensions-dir', str(base/'extensions'), '--extensionDevelopmentPath='+str(Path(args.extension_path).resolve()), '--extensionTestsPath='+str(ROOT/'extensions/vscode/test/host'), '--disable-workspace-trust', '--skip-welcome', '--skip-release-notes', '--disable-updates', str(work)]
    # Use Code.exe directly on Windows, not a command string through cmd.exe.
    if os.name == 'nt' and Path(args.code).suffix == '.cmd':
        installation = Path(args.code).parent.parent
        candidates = list(installation.glob('*/resources/app/out/cli.js'))
        if len(candidates) != 1: raise SystemExit('Cannot uniquely locate VS Code CLI')
        command = [str(installation/'Code.exe'), str(candidates[0]), *command[1:], '--wait']
        env['ELECTRON_RUN_AS_NODE'] = '1'
    startup = None
    if os.name == 'nt':
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    proc = subprocess.run(command, env=env, capture_output=True, timeout=180, startupinfo=startup)
    (base/'host.log').write_bytes(proc.stdout + proc.stderr)
    deadline = time.monotonic() + 120
    report = {}
    while time.monotonic() < deadline:
        try: report = json.loads(result.read_text(encoding='utf-8'))
        except (OSError, ValueError): pass
        if 'checks' in report: break
        time.sleep(0.2)
    if 'checks' not in report: raise SystemExit(f'Host produced no completed result (launcher exit {proc.returncode}); inspect artifacts/vscode-host/host.log')
    probe=report.get('samples',{}).get('moonbit',{})
    summary={'exit':proc.returncode, 'host':report.get('host'), 'extension_mode':report.get('extension_mode'), 'checks':report.get('checks'), 'error':report.get('error'),'moonbit_provider_probe':{k:v for k,v in probe.items() if k!='plan'}}
    (ROOT/'docs/host-validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    if proc.returncode or report.get('error'): raise SystemExit(1)

if __name__ == '__main__': main()
