# SPDX-License-Identifier: GPL-2.0-or-later
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m18'))
from finish_image import extract_jwasm_license


class CompilerRuntimeSourceTests(unittest.TestCase):
    OFFICIAL_SHA256 = '6d303327988ee2dda60cfabebf3f45a9758aee4da117d41cf3153fccb7e5e4bf'
    LICENSE_SHA256 = '4173a410eac727611c8cc156c6ecc5c12be621bf05d84514245e4c950b8cb042'

    def test_pinned_upstream_source_and_license_notice_are_consistent(self):
        package = json.loads((ROOT / 'config/m18/packages.json').read_text())
        source = package['compiler_runtime_source']
        self.assertEqual(source['archive_sha256'], self.OFFICIAL_SHA256)
        self.assertRegex(source['archive_url'],
                         r'^https://github\.com/open-watcom/open-watcom-1\.9/releases/download/ow1\.9/open_watcom_1\.9\.0-src\.tar\.bz2$')
        self.assertEqual(source['license'], 'Sybase Open Watcom Public License 1.0')
        for path in ('config/m18/payload/README.TXT',
                     'tools/m18/DISTRIBUTION-README.md',
                     'tools/m18/build_image.py'):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertIn(self.OFFICIAL_SHA256, text)
                self.assertIn('open_watcom_1.9.0-src.tar.bz2', text)
        # The separately downloaded official OW 1.9 source's license.txt has
        # this same normalized content; no network or cached archive is needed
        # by the public builder or synthetic host checks.
        self.assertEqual(hashlib.sha256(extract_jwasm_license()).hexdigest(), self.LICENSE_SHA256)


if __name__ == '__main__':
    unittest.main()
