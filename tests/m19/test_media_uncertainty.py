#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run the pinned component's media-binding regressions in the M19 gate."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]


class MediaBindingTests(unittest.TestCase):
    def test_component_driver_and_filesystem_policy(self):
        tests = ROOT / 'components/fdkernel/pc88va/tests'
        for name in ('test_m19_media_uncertainty.py', 'test_m14_media_lifetime.py'):
            with self.subTest(script=name):
                subprocess.run([sys.executable, '-B', str(tests / name)],
                               cwd=ROOT, check=True)


if __name__ == '__main__':
    unittest.main()
