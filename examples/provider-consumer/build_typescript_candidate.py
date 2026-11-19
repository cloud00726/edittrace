"""Build a test adapter for an exact official TypeScript npm archive."""

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile

from build_candidates import write_candidate

LOCK = json.loads(Path(__file__).with_name('typescript-lock.json').read_text(encoding='utf-8'))


def build(version, archive, output, omit_reference=False):
    locked = LOCK[version]
    with archive.open('rb') as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    integrity = 'sha512-' + base64.b64encode(hashlib.sha512(raw).digest()).decode('ascii')
    if integrity != locked['integrity']:
        raise ValueError('TypeScript registry archive integrity mismatch')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as package:
        with package.extractfile('package/lib/typescript.js') as stream:
            runtime = stream.read()
    if hashlib.sha256(runtime).hexdigest() != locked['runtime_sha256']:
        raise ValueError('TypeScript runtime SHA-256 mismatch')

    output.mkdir(parents=True, exist_ok=False)
    (output/'typescript.js').write_bytes(runtime)
    asset = output/'typescript-rename.vsix'
    manifest = {
        'name': 'typescript-rename', 'publisher': 'edittrace-fixture',
        'version': version, 'displayName': 'EditTrace TypeScript verification adapter',
        'engines': {'vscode': '^1.100.0'}, 'main': './typescript-rename.js',
        'contributes': {'languages': [{'id': 'typescript', 'extensions': ['.ts']}]},
        'edittraceTypeScript': {'version': version, 'sha256': locked['runtime_sha256'],
                               'synthetic_omit_reference': omit_reference},
    }
    write_candidate(asset, manifest, Path(__file__).with_name('typescript-rename.js'))
    receipt = {**locked, 'version': version, 'synthetic_omit_reference': omit_reference,
               'candidate': asset.name, 'candidate_sha256': hashlib.sha256(asset.read_bytes()).hexdigest()}
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version', choices=LOCK)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--synthetic-omit-reference', action='store_true')
    args = parser.parse_args()
    build(args.version, args.archive, args.output, args.synthetic_omit_reference)
