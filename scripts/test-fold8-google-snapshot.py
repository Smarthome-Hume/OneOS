#!/usr/bin/env python3
"""Run the shipped APK extraction and manifest checks against real ZIP fixtures."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / 'switcher/assets/fold8_coloros.sh').read_text()
EXTRACT = SOURCE[SOURCE.index('        for apk in "$new"/*.apk; do'):SOURCE.index('        chown -R')]
VERIFY = SOURCE[SOURCE.index('        (cd "$dir" && sha256sum'):SOURCE.index('    done\n}', SOURCE.index('verify_google()'))]

class Snapshot(unittest.TestCase):
    def run_fixture(self, libraries):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / 'lib/arm64').mkdir(parents=True)
            with zipfile.ZipFile(root / 'base.apk', 'w') as z:
                z.writestr('classes.dex', b'fixture')
                z.writestr('lib/armeabi-v7a/libwrong.so', b'wrong ABI')
            with zipfile.ZipFile(root / 'split_config.arm64_v8a.apk', 'w') as z:
                z.writestr('resources.arsc', b'fixture')
                for name, data in libraries.items(): z.writestr(name, data)
            bb = root / 'bb'
            bb.write_text('#!/bin/sh\nexec "$@"\n'); bb.chmod(0o755)
            env = dict(os.environ, new=t, dir=t, BB=str(bb))
            result = subprocess.run(['/bin/sh', '-ec', 'fail() { echo "$*" >&2; exit 3; };\n' + EXTRACT + VERIFY], env=env, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((root / 'lib/libwrong.so').exists())
            return {p.relative_to(root).as_posix(): p.read_bytes() for p in (root / 'lib').rglob('*.so')}, (root / 'native.sha256').read_text()

    def test_libraries_in_split_apk_are_extracted_and_verified(self):
        files, manifest = self.run_fixture({'lib/arm64-v8a/libexample.so': b'arm64 fixture'})
        self.assertEqual({'lib/libexample.so': b'arm64 fixture', 'lib/arm64/libexample.so': b'arm64 fixture'}, files)
        self.assertEqual(2, len(manifest.splitlines()))

    def test_apks_without_native_libraries_have_valid_empty_manifest(self):
        self.assertEqual(({}, ''), self.run_fixture({}))

    def test_modified_native_library_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / 'base.apk').write_bytes(b'fixture')
            (root / 'native.so').write_bytes(b'original')
            subprocess.run(['/bin/sh', '-ec', 'sha256sum base.apk > apk.sha256; sha256sum native.so > native.sha256'], cwd=t, check=True)
            (root / 'native.so').write_bytes(b'changed')
            r = subprocess.run(['/bin/sh', '-ec', 'fail() { echo "$*" >&2; exit 3; };\n' + VERIFY], env=dict(os.environ, dir=t), capture_output=True)
            self.assertEqual(3, r.returncode)
            self.assertIn(b'invalid', r.stderr)

    def test_archive_listing_failure_is_fatal(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t); (root / 'broken.apk').write_bytes(b'not a zip')
            bb = root / 'bb'; bb.write_text('#!/bin/sh\nexec "$@"\n'); bb.chmod(0o755)
            r = subprocess.run(['/bin/sh', '-ec', 'fail() { echo "$*" >&2; exit 3; };\n' + EXTRACT], env=dict(os.environ, new=t, BB=str(bb)), capture_output=True)
            self.assertEqual(3, r.returncode)
            self.assertIn(b'cannot list APK', r.stderr)

if __name__ == '__main__': unittest.main()
