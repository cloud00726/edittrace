"""Build synthetic VSIXs for behavioral and incomplete-execution checks."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build(output, moonfmt=None):
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    versions = ['1.0.0', '1.1.0', '1.1.1', '1.2.0', '1.3.0', '1.4.0']
    if moonfmt:
        versions.append('2.0.0')
    for version in versions:
        real_formatter = version == '2.0.0'
        manifest = {
            'name': 'versioned-provider', 'publisher': 'edittrace-fixture',
            'displayName': 'EditTrace synthetic provider', 'version': version,
            'engines': {'vscode': '^1.100.0'}, 'main': './fixture.js',
            'activationEvents': ['onLanguage:edittrace-fixture'],
            'contributes': {
                'languages': [{'id': 'edittrace-fixture', 'extensions': ['.etrf']}],
            },
        }
        if real_formatter:
            manifest.update({
                'displayName': 'EditTrace Moonfmt verification adapter',
                'main': './moonfmt.js',
                'activationEvents': ['onLanguage:edittrace-moonfmt'],
                'contributes': {'languages': [{'id': 'edittrace-moonfmt', 'extensions': ['.mbt']}]},
                'edittraceMoonfmtSha256': hashlib.sha256(moonfmt.read_bytes()).hexdigest(),
            })
        asset = output/f'versioned-provider-{version}.vsix'
        with zipfile.ZipFile(asset, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('extension/package.json', json.dumps(manifest))
            entry = 'moonfmt.js' if real_formatter else 'fixture.js'
            archive.write(Path(__file__).with_name(entry), 'extension/'+entry)
            archive.writestr('extension.vsixmanifest', f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="versioned-provider" Version="{version}" Publisher="edittrace-fixture"/>
    <DisplayName>EditTrace synthetic provider</DisplayName>
    <Description>Synthetic regression fixture</Description>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets><Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/></Assets>
</PackageManifest>""")
            archive.writestr('[Content_Types].xml', """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="js" ContentType="application/javascript"/>
  <Default Extension="vsixmanifest" ContentType="text/xml"/>
</Types>""")
        files[asset.name] = hashlib.sha256(asset.read_bytes()).hexdigest()
    (output/'SHA256.json').write_text(json.dumps(files, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--moonfmt', type=Path, help='Also package an adapter for this exact MoonBit formatter')
    args = parser.parse_args()
    build(args.output, args.moonfmt)
