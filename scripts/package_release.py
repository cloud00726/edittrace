"""Build local native ZIP and platform VSIX, without publishing or invoking remote services."""
import argparse, hashlib, json, os, platform, stat, subprocess, zipfile
from pathlib import Path
from native_artifact import distribution_core_bytes, find_native_executable, module_version
ROOT=Path(__file__).resolve().parents[1]


def write_native(archive, path, payload):
    member = zipfile.ZipInfo(path)
    member.create_system = 3  # UNIX mode retained by the VSIX installer.
    member.external_attr = (stat.S_IFREG | 0o755) << 16
    archive.writestr(member, payload, compress_type=zipfile.ZIP_DEFLATED)


def package(destination, require_clean=False):
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    if require_clean and dirty: raise RuntimeError('Build the release candidate from a clean checkout')
    destination=Path(destination).resolve()
    exe=find_native_executable(ROOT)
    version=subprocess.run([str(exe),'--version'],check=True,capture_output=True).stdout.decode('ascii').strip()
    declared=module_version(ROOT)
    if version!=declared:raise RuntimeError('Binary and module versions differ; rebuild before packaging')
    arch={'AMD64':'x64','x86_64':'x64','aarch64':'arm64','ARM64':'arm64'}.get(platform.machine())
    system={'Windows':'win32','Linux':'linux','Darwin':'darwin'}.get(platform.system())
    if not arch or not system: raise RuntimeError('Unsupported package platform')
    target=f'{system}-{arch}'
    extension=ROOT/'extensions/vscode'
    home=Path(os.environ.get('MOON_HOME',ROOT/'.tooling/moon'))
    licenses={'MoonBit-core-LICENSE':home/'lib/core/LICENSE',
              'MoonBit-core-NOTICE':home/'lib/core/NOTICE',
              'moonbitlang-async-LICENSE':ROOT/'.mooncakes/moonbitlang/async/LICENSE'}
    if not all(p.is_file() for p in licenses.values()): raise RuntimeError('Build first; dependency licenses must be available')
    manifest=json.loads((extension/'package.json').read_text(encoding='utf-8'))
    if manifest['version']!=version:raise RuntimeError('Extension and core release versions differ')
    guides = ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'docs/QUICKSTART.md', 'docs/CLI.md', 'docs/REGRESSIONS.md',
              'docs/STAGE2_SPEC.md', 'docs/RELEASE_NOTES_0.4.0.md', 'docs/RELEASE_NOTES_0.5.3.md',
              'docs/PROVIDER_REGRESSIONS.md']
    runner = ['scripts/run_provider_regression.py', 'scripts/draft_provider_suite.py', 'extensions/vscode/provider-host.js',
              'extensions/vscode/package.json', 'extensions/vscode/extension.js',
              'extensions/vscode/bridge.js', 'extensions/vscode/diagnostics.js',
              'extensions/vscode/presentation.js', 'extensions/vscode/project.js']
    examples = ['suite.json', 'candidate-format-suite.json', 'build_candidates.py', 'fixture.js',
                'moonfmt.js', 'moonfmt-suite.json', 'sync-scope-suite.json', 'typescript-rename.js',
                'typescript-rename-suite.json', 'typescript-lock.json', 'build_typescript_candidate.py',
                'workflow.yml', 'README.md']
    sample_paths = ['examples/provider-consumer/' + filename for filename in examples]
    reviewed_examples = ['README.md', 'capture-evidence.json', 'format.case.json', 'format.plan.json',
                         'injected-lost-event.case.json', 'injected-stale.case.json', 'rename.case.json',
                         'rename.plan.json', 'same-position-events.case.json', 'same-position.plan.json',
                         'stage2-checkpoint.jsonl', 'suite.json', 'sync.case.json', 'sync.jsonl', 'vscode-jsonrpc.jsonl']
    example_files = [ROOT/'examples/real-world'/name for name in reviewed_examples]
    files=[ROOT/name for name in ['moon.mod', 'toolchain.json', 'extensions/vscode/README.md',
                                  *guides, *runner, *sample_paths]] + example_files
    for directory in ['core','adapters','io','cmd','extensions/vscode']:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix in ['.mbt','.mbti','.pkg','.js','.json'])
    digests={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
    provenance={'source_commit':source_commit,'working_tree_dirty':dirty,
                'toolchain':json.loads((ROOT/'toolchain.json').read_text(encoding='utf-8')),
                'input_sha256':digests}
    payload=distribution_core_bytes(exe)
    local_root=str(ROOT).lower().encode('utf-8')
    if local_root in payload.lower() or str(ROOT).lower().encode('utf-16le') in payload.lower():
        raise RuntimeError('Release binary contains the local build directory')
    provenance['binary_debug_info']='stripped' if system=='linux' else 'original platform build'
    destination.mkdir(parents=True,exist_ok=False)
    manifest_xml=f'''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
<Metadata><Identity Language="en-US" Id="edittrace" Version="{manifest['version']}" Publisher="cloud00726" TargetPlatform="{target}"/>
<DisplayName>EditTrace</DisplayName><Description xml:space="preserve">Local text edit validation with the MoonBit core</Description>
<Tags>debuggers</Tags><Categories>Other</Categories><GalleryFlags>Public</GalleryFlags><Properties>
<Property Id="Microsoft.VisualStudio.Code.Engine" Value="^1.100.0"/>
<Property Id="Microsoft.VisualStudio.Code.ExecutesCode" Value="true"/>
</Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation><Dependencies/>
<Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE" Addressable="true"/></Assets></PackageManifest>'''
    content_types='''<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/><Default Extension="md" ContentType="text/markdown"/><Default Extension="exe" ContentType="application/octet-stream"/><Default Extension="vsixmanifest" ContentType="text/xml"/><Default Extension="" ContentType="application/octet-stream"/></Types>'''
    vsix=destination/f'edittrace-{manifest["version"]}-{target}.vsix'
    with zipfile.ZipFile(vsix,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content_types);z.writestr('extension.vsixmanifest',manifest_xml)
        z.writestr('extension/BUILD_INFO.json',json.dumps(provenance,indent=2)+'\n')
        for name in ['package.json','extension.js','bridge.js','diagnostics.js','presentation.js','project.js','README.md']: z.write(extension/name,'extension/'+name)
        z.write(ROOT/'LICENSE','extension/LICENSE')
        z.write(ROOT/'THIRD_PARTY_NOTICES.md','extension/THIRD_PARTY_NOTICES.md')
        for name,file in licenses.items():z.write(file,'extension/licenses/'+name)
        write_native(z,'extension/bin/'+('edittrace.exe' if system=='win32' else 'edittrace'),payload)
    archive=destination/f'edittrace-core-{version}-{target}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('BUILD_INFO.json',json.dumps(provenance,indent=2)+'\n')
        write_native(z,'edittrace.exe' if system=='win32' else 'edittrace',payload)
        for name in guides: z.write(ROOT/name,Path(name).name)
        for name in runner:
            z.write(ROOT/name,'provider-runner/'+name)
        for name in sample_paths:
            z.write(ROOT/name,name)
        for name,file in licenses.items():z.write(file,'licenses/'+name)
        for file in example_files:
            z.write(file,'examples/'+file.name)
    evidence={'platform':target,'core_version':version,'extension_version':manifest['version'],'published':False,'source':provenance,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [archive,vsix]}}
    evidence['archive_members']={}
    for asset in (archive, vsix):
        with zipfile.ZipFile(asset) as z:
            evidence['archive_members'][asset.name]=sorted(z.namelist())
    (destination/'SHA256.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    return evidence

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(ROOT/'output/release'))
    parser.add_argument('--require-clean',action='store_true');args=parser.parse_args()
    print(json.dumps(package(args.out, args.require_clean)))
