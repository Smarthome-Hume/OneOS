#!/usr/bin/env python3
"""Regressions for Fold8 Pixel boot resources and wallpaper preservation."""
import base64
import gzip
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'switcher/assets/guest_prepare.sh').read_text()
RRO = SOURCE.split('# BEGIN GENERATED PIXEL FOLD8 CONFIG\n', 1)[1].split('# END GENERATED PIXEL FOLD8 CONFIG', 1)[0]
WALLPAPER = SOURCE.split("# Pixel 17's WallpaperDataParser", 1)[1]
WALLPAPER = "# Pixel 17's WallpaperDataParser" + WALLPAPER.split('if [ -n "$OEM_FILES" ]; then', 1)[0]
SYMLINK = 'no_symlink() {' + SOURCE.split('no_symlink() {', 1)[1].split('\n}\n', 1)[0] + '\n}\n'


class PixelFold8(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.p = Path(self.temp.name)
        self.stage = self.p / 'stage'
        self.stage.mkdir()
        self.ext = self.p / 'system_ext'
        marker = self.ext / 'priv-app/SystemUIGoogle/SystemUIGoogle.apk'
        marker.parent.mkdir(parents=True)
        marker.touch()
        self.bb = self.p / 'bb'
        self.bb.write_text('#!/bin/sh\nexec "$@"\n')
        self.bb.chmod(0o755)
        self.env = dict(os.environ, STAGE=str(self.stage), GUEST_SYSTEM_EXT=str(self.ext),
                        ROOTFS=str(self.p / 'rootfs'), BB=str(self.bb), ONEOS_PROFILE='f8', OEM_FILES='')

    def shell(self, script, ok=True):
        sha = 'sha256sum() { shasum -a 256 "$@"; }\n'
        result = subprocess.run(['/bin/sh', '-e'], input=sha + SYMLINK + script,
                                text=True, env=self.env, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def wallpaper(self, text=None):
        w = self.stage / 'data/system/users/0/wallpaper_info.xml'
        w.parent.mkdir(parents=True, exist_ok=True)
        w.write_text(text or '<?xml version="1.0"?>\n<wp component="chosen/.Wallpaper" cropLeft="7" cropRight="400">\n  <description component="chosen/.Wallpaper">\n    <content><string>keep\nthis</string></content>\n  </description>\n</wp>\n')
        return w

    def test_overlay_scope_and_integrity(self):
        self.shell(RRO)
        files = list((self.stage / 'oem/overlay').glob('*.apk'))
        self.assertEqual(len(files), 2)
        for p in files:
            with zipfile.ZipFile(p) as z:
                self.assertIn('AndroidManifest.xml', z.namelist())
                self.assertIn('resources.arsc', z.namelist())
                self.assertFalse(any(n.endswith('.dex') for n in z.namelist()))
            self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(), RRO)
        for marker, data in re.findall(r"<<'(ONEOS_PIXEL_FOLD8_[A-Z]+)'[^\n]*\n(.*?)\n\1", RRO, re.S):
            self.assertTrue(gzip.decompress(base64.b64decode(data)).startswith(b'PK'))

    def test_other_profiles_unchanged(self):
        self.env['ONEOS_PROFILE'] = 'f8u'
        w = self.wallpaper()
        before = w.read_bytes()
        self.shell(RRO + WALLPAPER)
        self.assertFalse((self.stage / 'oem').exists())
        self.assertEqual(w.read_bytes(), before)

    def test_coloros_unchanged(self):
        (self.ext / 'priv-app/SystemUIGoogle/SystemUIGoogle.apk').unlink()
        w = self.wallpaper()
        before = w.read_bytes()
        self.shell(RRO + WALLPAPER)
        self.assertFalse((self.stage / 'oem').exists())
        self.assertEqual(w.read_bytes(), before)

    def test_native_sizes_and_user_aod_setting_preserved(self):
        values = {}
        for kind in ('framework', 'systemui'):
            for item in ET.parse(ROOT / f'switcher/overlays/pixel_fold8_{kind}/res/values/config.xml').getroot():
                values[item.attrib['name']] = item.text
        self.assertEqual(values['config_dozeAlwaysOnDisplayAvailable'], 'true')
        self.assertEqual(values['config_dozeComponent'], 'com.android.systemui/com.android.systemui.doze.DozeService')
        for name in ('default', 'portrait', 'landscape'):
            self.assertEqual(values['status_bar_height_' + name], '48dp')
        self.assertEqual(values['status_bar_padding_top'], '0dp')
        self.assertNotIn('status_bar_icon_size', values)
        self.assertNotIn('status_bar_clock_size', values)
        self.assertNotIn('config_dozeAlwaysOnEnabled', values)
        self.assertNotIn('settings put', RRO)

    def test_wallpaper_attributes_content_and_backup_preserved(self):
        w = self.wallpaper()
        before = w.read_text()
        self.shell(WALLPAPER)
        root = ET.fromstring(w.read_text())
        self.assertEqual(root.attrib, ET.fromstring(before).attrib)
        self.assertEqual(root.find('description').attrib['component'], 'chosen/.Wallpaper')
        self.assertEqual(root.find('.//string').text, 'keep\nthis')
        self.assertIn('><description', w.read_text())
        self.assertEqual(Path(str(w) + '.oneos-spacing-backup').read_text(), before)
        compact = w.read_bytes()
        self.shell(WALLPAPER)
        self.assertEqual(w.read_bytes(), compact)
        self.assertEqual(Path(str(w) + '.oneos-spacing-backup').read_text(), before)

    def test_failed_normalization_retains_original(self):
        w = self.wallpaper()
        before = w.read_bytes()
        self.bb.write_text('#!/bin/sh\n[ "$1" != sed ] || exit 1\nexec "$@"\n')
        self.shell(WALLPAPER)
        self.assertEqual(w.read_bytes(), before)
        self.assertFalse(Path(str(w) + '.oneos-normalized').exists())

    def test_symlinked_temporary_file_refused(self):
        w = self.wallpaper()
        before = w.read_bytes()
        target = self.p / 'outside'
        target.write_text('untouched')
        Path(str(w) + '.oneos-normalized').symlink_to(target)
        self.shell(WALLPAPER, ok=False)
        self.assertEqual(target.read_text(), 'untouched')
        self.assertEqual(w.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
