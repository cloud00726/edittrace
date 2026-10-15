"""Regressions for checkout byte stability and the Unix installer permission step."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import bootstrap
from native_artifact import find_native_executable

ROOT = Path(__file__).resolve().parents[1]


class CISupportTests(unittest.TestCase):
    def test_artifact_resolution_handles_both_names_independently_of_host(self):
        artifacts = ROOT / 'artifacts'
        artifacts.mkdir(exist_ok=True)
        for name in ['edittrace', 'edittrace.exe']:
            root = Path(tempfile.mkdtemp(prefix='artifact-name-', dir=artifacts))
            folder = root / '_build/native/debug/build/cmd/edittrace'
            folder.mkdir(parents=True)
            expected = folder / name
            expected.write_bytes(b'fixture')
            self.assertEqual(find_native_executable(root), expected)

    def test_artifact_resolution_rejects_missing_and_ambiguous_outputs(self):
        artifacts = ROOT / 'artifacts'
        artifacts.mkdir(exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix='artifact-invalid-', dir=artifacts))
        with self.assertRaisesRegex(RuntimeError, 'found 0'):
            find_native_executable(root)
        folder = root / '_build/native/debug/build/cmd/edittrace'
        folder.mkdir(parents=True)
        for name in ['edittrace', 'edittrace.exe']:
            (folder / name).write_bytes(b'fixture')
        with self.assertRaisesRegex(RuntimeError, 'found 2'):
            find_native_executable(root)

    def test_autocrlf_checkout_preserves_oracle_digest(self):
        artifacts = ROOT / 'artifacts'
        artifacts.mkdir(exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix='checkout-regression-', dir=artifacts))
        (work / 'tests/oracle').mkdir(parents=True)
        shutil.copyfile(ROOT / '.gitattributes', work / '.gitattributes')
        corpus = work / 'tests/oracle/corpus.jsonl'
        shutil.copyfile(ROOT / 'tests/oracle/corpus.jsonl', corpus)

        def git(*args):
            subprocess.run(['git', '-C', str(work), *args], check=True, capture_output=True)

        git('init')
        git('config', 'core.autocrlf', 'true')
        git('add', '.')
        corpus.unlink()
        git('checkout-index', '--all', '--force')
        expected = json.loads((ROOT / 'tests/oracle/manifest.json').read_text())['corpus_sha256']
        self.assertEqual(hashlib.sha256(corpus.read_bytes()).hexdigest(), expected)
        self.assertNotIn(b'\r\n', corpus.read_bytes())

    def test_unix_permission_policy_includes_internal_tcc(self):
        # A fake filesystem makes the policy test portable; actual Linux execution
        # remains covered by the Ubuntu CI job, not claimed by this unit test.
        class File:
            def __init__(self, regular=True):
                self.regular, self.mode = regular, None
            def is_file(self):
                return self.regular
            def stat(self):
                return type('Mode', (), {'st_mode': 0o644})()
            def chmod(self, mode):
                self.mode = mode

        moon, moonc, directory, tcc = File(), File(), File(False), File()

        class Bin:
            def iterdir(self):
                return [moon, moonc, directory]

        class Target:
            def __truediv__(self, name):
                return Bin() if name == 'bin' else tcc

        bootstrap.make_executable(Target())
        self.assertEqual([moon.mode, moonc.mode, tcc.mode], [0o755] * 3)
        self.assertIsNone(directory.mode)


if __name__ == '__main__':
    unittest.main()
