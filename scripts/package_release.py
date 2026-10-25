"""Build local native ZIP and platform VSIX, without publishing or invoking remote services."""
import argparse, hashlib, json, os, platform, re, subprocess, zipfile
from pathlib import Path
from native_artifact import find_native_executable
ROOT=Path(__file__).resolve().parents[1]

def package(destination):
    destination=Path(destination).resolve()
    destination.mkdir(parents=True,exist_ok=False)
    exe=find_native_executable(ROOT)
    version=subprocess.run([str(exe),'--version'],check=True,capture_output=True).stdout.decode('ascii').strip()
    declared=re.search(r'^version\s*=\s*"([^"]+)"', (ROOT/'moon.mod').read_text(encoding='utf-8'),re.M).group(1)
    if version!=declared:raise RuntimeError('Binary and module versions differ; rebuild before packaging')
    arch={'AMD64':'x64','x86_64':'x64','aarch64':'arm64','ARM64':'arm64'}.get(platform.machine())
    system={'Windows':'win32','Linux':'linux','Darwin':'darwin'}.get(platform.system())
    if not arch or not system: raise RuntimeError('Unsupported package platform')
    target=f'{system}-{arch}'
    extension=ROOT/'extensions/vscode'
    home=Path(os.environ.get('MOON_HOME',ROOT/'.tooling/moon'))
    licenses={'MoonBit-core-LICENSE':home/'lib/core/LICENSE','moonbitlang-async-LICENSE':ROOT/'.mooncakes/moonbitlang/async/LICENSE'}
    if (home/'lib/core/NOTICE').is_file():licenses['MoonBit-core-NOTICE']=home/'lib/core/NOTICE'
    if not all(p.is_file() for p in licenses.values()): raise RuntimeError('Build first; dependency licenses must be available')
    manifest=json.loads((extension/'package.json').read_text(encoding='utf-8'))
    if manifest['version']!=version:raise RuntimeError('Extension and core release versions differ')
    files=[ROOT/'moon.mod']
    for directory in ['core','adapters','io','cmd','extensions/vscode']:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix in ['.mbt','.mbti','.pkg','.js','.json'])
    digests={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
    provenance={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'input_sha256':digests}
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
        z.write(exe,'extension/bin/'+('edittrace.exe' if system=='win32' else 'edittrace'))
    archive=destination/f'edittrace-core-{version}-{target}.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('BUILD_INFO.json',json.dumps(provenance,indent=2)+'\n')
        z.write(exe,'edittrace.exe' if system=='win32' else 'edittrace')
        for name in ['LICENSE','THIRD_PARTY_NOTICES.md','docs/QUICKSTART.md','docs/CLI.md','docs/REGRESSIONS.md']: z.write(ROOT/name,Path(name).name)
        for name,file in licenses.items():z.write(file,'licenses/'+name)
        for file in (ROOT/'examples/real-world').glob('*'):
            if file.is_file():z.write(file,'examples/'+file.name)
    evidence={'platform':target,'core_version':version,'extension_version':manifest['version'],'published':False,'source':provenance,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [archive,vsix]}}
    (destination/'SHA256.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    return evidence

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(ROOT/'output/release'));args=parser.parse_args()
    print(json.dumps(package(args.out)))
