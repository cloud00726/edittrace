"""Build three synthetic VSIXs representing correct, faulty and fixed releases."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for version in ['1.0.0', '1.1.0', '1.1.1']:
        manifest = {
            'name': 'versioned-provider', 'publisher': 'edittrace-fixture',
            'displayName': 'EditTrace synthetic provider', 'version': version,
            'engines': {'vscode': '^1.100.0'}, 'main': './fixture.js',
            'activationEvents': ['onLanguage:edittrace-fixture'],
            'contributes': {
                'languages': [{'id': 'edittrace-fixture', 'extensions': ['.etrf']}],
            },
        }
        asset = output/f'versioned-provider-{version}.vsix'
        with zipfile.ZipFile(asset, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('extension/package.json', json.dumps(manifest))
            archive.write(Path(__file__).with_name('fixture.js'), 'extension/fixture.js')
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
    build(parser.parse_args().output)
